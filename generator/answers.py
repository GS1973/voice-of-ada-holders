"""The Voice of ADA Holders — counting the answers under metadata label 1695.

Applies the rules of the CIP draft (cip/README.md) to what db-sync holds:

  record   the value under label 1695 is a map with 0 = 1 (version), 1 = [0,
           stake key hash], 2 = a non-empty list of [[tx hash, index], choice];
           unknown keys are ignored; anything else malformed voids the record
  proof    the stake key hash is in the transaction's required_signers, and
           the transaction passed phase-2 validation
  answer   counts if the action was submitted before it, the block lies before
           the action's closing time, and the credential was registered when
           the action was submitted and stayed registered without interruption
           until the closing time (for an action still open: until the tally)
  latest   per action and credential only the latest answer counts, in chain
           order: block, position in block, position in the list

Closing time is the start of the first epoch in which the ledger accepts no
more votes on the action. Measured on db-sync 24-09-2026: votes are cast in the
ratified_epoch (50 of 81 enacted actions have votes in it) and never in the
enacted_epoch; expired and dropped actions have no votes in their expired or
dropped epoch; and no vote is ever cast in epoch expiration, even when the
action was ratified into it and is enacted only an epoch later (31 of 81). So
the closing epoch is the least of expiration and the epoch the action leaves
the proposals: enacted_epoch, else ratified_epoch + 1, else expired_epoch, else
dropped_epoch (tally.py computes it).

The label was used by no transaction before 24-09-2026 (every label below
100000 counted on mainnet that day), so the scan starts at the first
transaction of epoch 657. Records are kept in a cache and only the chain after
it is read again, from 2160 blocks back so that a rollback is never missed.

FLOOR_TX and the cache hold db-sync's numbers for transactions, which a rebuild
of db-sync renumbers. So each carries the hash of its transaction: the floor
is refused if its number now names another transaction, and a cache whose
last number does is thrown away and read again from the floor.
"""
import json
import os
from datetime import datetime, timezone

import cbor2

LABEL = 1695
FLOOR_TX = 124109660             # first transaction of epoch 657
FLOOR_HASH = '33675eba5ffa3c4132174902ee71227932bd5726d6e015fc8c99d1dd5e729330'
ROLLBACK_BLOCKS = 2160           # the security parameter k
CHOICES = ('no', 'yes', 'none')  # 0, 1, 2 as the ledger's Vote
LOVELACE = 1_000_000
CACHE = os.path.expanduser(os.environ.get('TVOAH_ANSWER_CACHE', '~/.cache/tvoah/answer_records.json'))


def _q(cur, sql, args=None):
    cur.execute(sql, args)
    return cur.fetchall()


def tx_hash(cur, tx_id):
    r = _q(cur, "select encode(hash, 'hex') from tx where id = %(t)s", {'t': tx_id})
    return r[0][0] if r else None


def scan(cur, tip_block, tip_tx):
    """All label-1695 transactions up to the pinned tip, from cache plus a rescan."""
    if tx_hash(cur, FLOOR_TX) != FLOOR_HASH:
        raise SystemExit(f'FLOOR_TX {FLOOR_TX} no longer names the first transaction of epoch 657 '
                         f'(db-sync renumbered?); derive it again before counting')
    empty = {'scanned_to': FLOOR_TX - 1, 'records': []}
    try:
        with open(CACHE) as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = empty
    if cache is not empty and tx_hash(cur, cache['scanned_to']) != cache.get('scanned_hash'):
        print('answer cache: its last transaction number names another transaction; reading from the floor')
        cache = empty
    back = _q(cur, """
        select coalesce(min(t.id), %(tip)s + 1) from tx t
        where t.block_id >= (select id from block where block_no = %(b)s)""",
              {'b': max(tip_block - ROLLBACK_BLOCKS, 0), 'tip': tip_tx})[0][0]
    start = max(FLOOR_TX, min(cache['scanned_to'] + 1, back))
    kept = [r for r in cache['records'] if r['tx_id'] < start]
    rows = _q(cur, """
        select m.tx_id, encode(t.hash, 'hex'), b.block_no, t.block_index, b.time, t.valid_contract,
               encode(m.bytes, 'hex'),
               (select array_agg(encode(e.hash, 'hex')) from extra_key_witness e where e.tx_id = t.id)
        from tx_metadata m join tx t on t.id = m.tx_id join block b on b.id = t.block_id
        where m.key = %(l)s and m.tx_id between %(s)s and %(t)s
        order by m.tx_id""", {'l': LABEL, 's': start, 't': tip_tx})
    new = [{'tx_id': r[0], 'tx': r[1], 'block': r[2], 'index': r[3],
            'time': r[4].replace(tzinfo=timezone.utc).isoformat(), 'valid': r[5],
            'cbor': r[6], 'signers': r[7] or []} for r in rows]
    records = kept + new
    tmp = CACHE + '.tmp'
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(tmp, 'w') as f:
        json.dump({'scanned_to': tip_tx, 'scanned_hash': tx_hash(cur, tip_tx), 'records': records}, f)
    os.replace(tmp, CACHE)
    return records


def parse(rec):
    """(stake key hash hex, [(action id, choice, position)]) or (None, reason)."""
    if not rec['valid']:
        return None, 'phase-2 invalid'
    try:
        v = cbor2.loads(bytes.fromhex(rec['cbor']))
    except Exception:
        return None, 'not CBOR'
    # db-sync keeps the whole metadata entry, { 1695: record }.
    if isinstance(v, dict) and list(v) == [LABEL]:
        v = v[LABEL]
    isint = lambda x: type(x) is int
    if not isinstance(v, dict) or not all(k in v for k in (0, 1, 2)):
        return None, 'not a record'
    if not (isint(v[0]) and v[0] == 1):
        return None, 'unknown version'
    c = v[1]
    if not (isinstance(c, list) and len(c) == 2 and isint(c[0]) and c[0] == 0
            and isinstance(c[1], bytes) and len(c[1]) == 28):
        return None, 'bad credential'
    a = v[2]
    if not (isinstance(a, list) and a):
        return None, 'no answers'
    out = []
    for pos, x in enumerate(a):
        if not (isinstance(x, list) and len(x) == 2 and isinstance(x[0], list) and len(x[0]) == 2
                and isinstance(x[0][0], bytes) and len(x[0][0]) == 32
                and isint(x[0][1]) and 0 <= x[0][1] <= 65535 and isint(x[1]) and x[1] in (0, 1, 2)):
            return None, 'bad answer'
        out.append((f'{x[0][0].hex()}-{x[0][1]}', CHOICES[x[1]], pos))
    key = c[1].hex()
    if key not in rec['signers']:
        return None, 'not signed by the stake key'
    return key, out


def count(cur, records, actions, tip_time, tip_tx, snapshot_ada=None):
    """Fills heads, ada and groups on each action; returns the per-credential
    answers file and a summary. snapshot_ada (addr_id -> lovelace, from the ADA
    snapshot of the epoch) makes the ADA behind the answers come from the same
    epoch as the ADA of all wallets; without it, ADA is read at the tip."""
    by_id = {a['id']: a for a in actions}
    latest, invalid = {}, {}
    for rec in sorted(records, key=lambda r: (r['block'], r['index'])):
        key, parsed = parse(rec)
        if key is None:
            invalid[parsed] = invalid.get(parsed, 0) + 1
            continue
        for action_id, choice, pos in parsed:
            latest[(action_id, key)] = {'choice': choice, 'tx': rec['tx'], 'tx_id': rec['tx_id'],
                                        'time': rec['time'], 'block': rec['block'], 'pos': pos}

    creds = sorted({k for _, k in latest})
    info = credentials(cur, creds, tip_tx, snapshot_ada) if creds else {}

    tip_iso = tip_time.replace(tzinfo=timezone.utc).isoformat()
    per_cred, counted = {}, 0
    for (action_id, key), ans in latest.items():
        a = by_id.get(action_id)
        ci = info.get(key)
        if a is None:
            reason = 'no such action'
        elif ans['tx_id'] <= a['tx_id']:
            reason = 'before the action'
        elif utc(ans['time']) >= utc(a['closes_at_utc']):
            reason = 'after closing'
        elif ci is None or not registered_throughout(ci['events'], a['tx_id'], min(a['closes_at_utc'], tip_iso, key=utc)):
            reason = 'not registered since before the action'
        else:
            reason = None
        per_cred.setdefault(key, {})[action_id] = {'choice': ans['choice'], 'tx': ans['tx'],
                                                   'counted': reason is None, **({'reason': reason} if reason else {})}
        if reason is None:
            counted += 1
            lovelace = ci['lovelace']
            a['heads'][ans['choice']] += 1
            a['_ada'][ans['choice']] += lovelace
            g = group(ci['dreps'], a['tx_id'])
            gh = a['_groups'].setdefault(g, {'heads': {'yes': 0, 'no': 0, 'none': 0}, 'ada': {'yes': 0, 'no': 0, 'none': 0}})
            gh['heads'][ans['choice']] += 1
            gh['ada'][ans['choice']] += lovelace

    for a in actions:
        a['ada'] = {k: v // LOVELACE for k, v in a.pop('_ada').items()}
        groups = a.pop('_groups')
        a['groups'] = [{'name': n, 'heads': groups[n]['heads'],
                        'ada': {k: v // LOVELACE for k, v in groups[n]['ada'].items()}}
                       for n in GROUP_ORDER if n in groups]
        del a['tx_id'], a['closes_at_utc']
    summary = {'transactions': len(records), 'answers': len(latest), 'counted': counted,
               'ada_from': 'snapshot' if snapshot_ada is not None else 'tip',
               'credentials': len(creds), 'records_ignored': invalid}
    return per_cred, summary


GROUP_ORDER = ['Delegated to a DRep', 'Always abstain', 'Always no confidence', 'No DRep chosen']


def group(dreps, action_tx):
    """The DRep delegation in force when the action was submitted."""
    before = [d for d in dreps if d[0] < action_tx]
    if not before:
        return 'No DRep chosen'
    view = before[-1][1]
    return {'drep_always_abstain': 'Always abstain',
            'drep_always_no_confidence': 'Always no confidence'}.get(view, 'Delegated to a DRep')


def registered_throughout(events, action_tx, until_iso):
    """Registered in the state the action's transaction was applied to, and no
    deregistration from then until until_iso."""
    state = False
    for tx_id, _, reg, _ in events:
        if tx_id >= action_tx:
            break
        state = reg
    if not state:
        return False
    until = utc(until_iso)
    return not any(not reg and tx_id >= action_tx and utc(time) < until for tx_id, _, reg, time in events)


def utc(iso):
    """Times are compared as times, not as strings."""
    return datetime.fromisoformat(iso.replace('Z', '+00:00'))


def credentials(cur, keys, tip_tx, snapshot_ada=None):
    """Per stake key hash: registration events, DRep delegations, and the ADA it
    holds at the tip (unspent outputs plus withdrawable rewards)."""
    rows = _q(cur, """
        select id, encode(substring(hash_raw from 2), 'hex') from stake_address
        where hash_raw = any(%(h)s)""", {'h': [bytes.fromhex('e1' + k) for k in keys]})
    addr = {r[0]: r[1] for r in rows}
    info = {k: {'events': [], 'dreps': [], 'lovelace': 0} for k in addr.values()}
    if not addr:
        return info
    ids = list(addr)
    for addr_id, tx_id, cert_index, reg, time in _q(cur, """
        select r.addr_id, r.tx_id, r.cert_index, true, b.time from stake_registration r
          join tx on tx.id = r.tx_id join block b on b.id = tx.block_id
          where r.addr_id = any(%(a)s) and r.tx_id <= %(t)s
        union all
        select d.addr_id, d.tx_id, d.cert_index, false, b.time from stake_deregistration d
          join tx on tx.id = d.tx_id join block b on b.id = tx.block_id
          where d.addr_id = any(%(a)s) and d.tx_id <= %(t)s
        order by 2, 3""", {'a': ids, 't': tip_tx}):
        info[addr[addr_id]]['events'].append((tx_id, cert_index, reg, time.replace(tzinfo=timezone.utc).isoformat()))
    for addr_id, tx_id, view in _q(cur, """
        select dv.addr_id, dv.tx_id, dh.view from delegation_vote dv
          join drep_hash dh on dh.id = dv.drep_hash_id
          where dv.addr_id = any(%(a)s) and dv.tx_id <= %(t)s
        order by dv.tx_id""", {'a': ids, 't': tip_tx}):
        info[addr[addr_id]]['dreps'].append((tx_id, view))
    if snapshot_ada is not None:
        # a key registered after the snapshot holds nothing in it: 0
        for addr_id, key in addr.items():
            info[key]['lovelace'] = int(snapshot_ada.get(addr_id, 0))
        return info
    epoch = _q(cur, "select epoch_no from block b join tx on tx.block_id = b.id where tx.id = %(t)s", {'t': tip_tx})[0][0]
    for addr_id, lovelace in _q(cur, """
        select a.id, coalesce(u.v, 0) + coalesce(r.v, 0)
        from unnest(%(a)s::bigint[]) as a(id)
        left join (
          select o.stake_address_id id, sum(o.value) v from tx_out o
          where o.stake_address_id = any(%(a)s) and o.tx_id <= %(t)s
            and not exists (select 1 from tx_in i
                            where i.tx_out_id = o.tx_id and i.tx_out_index = o.index and i.tx_in_id <= %(t)s)
          group by 1) u using (id)
        left join (
          select addr_id id, sum(v) v from (
            select addr_id, amount v from reward where addr_id = any(%(a)s) and spendable_epoch <= %(e)s
            union all select addr_id, amount from reward_rest where addr_id = any(%(a)s) and spendable_epoch <= %(e)s
            union all select addr_id, -amount from withdrawal where addr_id = any(%(a)s) and tx_id <= %(t)s) x
          group by 1) r using (id)""", {'a': ids, 't': tip_tx, 'e': epoch}):
        info[addr[addr_id]]['lovelace'] = int(lovelace)
    return info
