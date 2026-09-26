#!/usr/bin/env python3
"""The Voice of ADA Holders: tally generator.

Reads db-sync and writes the data.json the site renders. Everything it writes
can be recounted from the chain; the tally states the block it was taken at.

Two modes, because they differ a hundredfold in cost:

    tally.py OUT.json               light, every quarter hour: actions, their
                                    status and documents, wallets per action;
                                    ADA figures come from the latest snapshot
    tally.py --ada SNAPSHOT.json.gz heavy, once per epoch: ADA per wallet

TVOAH_DSN="host=... port=... dbname=cexplorer user=tvoah_ro" selects db-sync.

Definitions:
  wallet    a stake key registered continuously from before the governance
            action was submitted until it closes (for an open action: until
            now); one key, one voice. Script credentials cannot sign an
            answer and are not counted (cip/README.md)
  ADA       what a credential holds: unspent outputs on its addresses plus
            withdrawable rewards; shown as a check, never counted. Taken once
            per epoch; data.json says which epoch, per action
  closed    an action whose closing time has passed is counted once more
            when its closing block is 2160 blocks deep, and its figures are
            kept from then on (closed_actions.json): a closed action never
            changes again
  documents title and abstract are filled by anchors.py from the anchored
            document, only if it hashes to the value on chain
  answers   under metadata label 1695, counted by answers.py with the rules of
            the CIP draft (cip/README.md); per credential in answers.json

db-sync runs on a VM that also carries cardano-node. A query that takes the
memory takes the node down (23-09-2026: three OOM kills, each followed by a
full chain revalidation). Every session here is small on purpose: work_mem
64MB, no parallel workers (their hash tables live in /dev/shm), and a
statement timeout, so a query that grows is cancelled by the server itself.
"""
import gzip
import json
import os
import sys
import tempfile
from bisect import bisect_left
from datetime import timezone

import psycopg2

import answers

LOVELACE = 1_000_000

# Mainnet epochs are exactly five days; epoch 208 (the first Shelley epoch)
# began at 2020-07-29 21:44:51 UTC.
SHELLEY_START, SHELLEY_EPOCH, EPOCH_SECONDS = 1596059091, 208, 432000
SHELLEY_UNIX_MINUS_SLOT = 1591566291          # mainnet: slot = unix time - this
ROLLBACK_BLOCKS = 2160                        # the security parameter k


def epoch_start_iso(epoch):
    from datetime import datetime
    ts = SHELLEY_START + (epoch - SHELLEY_EPOCH) * EPOCH_SECONDS
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


SNAPSHOT = os.path.expanduser(os.environ.get('TVOAH_ADA_SNAPSHOT', '~/.cache/tvoah/ada_snapshot.json.gz'))
CLOSED = os.path.expanduser(os.environ.get('TVOAH_CLOSED', '~/.cache/tvoah/closed_actions.json'))


def q(cur, sql, args=None):
    cur.execute(sql, args)
    return cur.fetchall()


def connect(timeout_min):
    """One transaction for the whole run, REPEATABLE READ: every query sees
    the database as the first one did, whatever db-sync rolls back meanwhile.
    (25-09-2026: a fork of one block at the tip removed the pinned tip block
    during a run, and a later query found no row.) Nothing is committed: the
    run writes only temp tables, and the role has no write grants."""
    conn = psycopg2.connect(os.environ['TVOAH_DSN'])
    conn.set_session(isolation_level='REPEATABLE READ', readonly=False, autocommit=False)
    cur = conn.cursor()
    cur.execute("set work_mem = '64MB'")
    cur.execute("set max_parallel_workers_per_gather = 0")
    cur.execute(f"set statement_timeout = '{int(timeout_min)}min'")
    return cur


def pin_tip(cur):
    """Pin the tip first and read everything up to it; with the transaction
    of connect() the tables stay as they were at this first query."""
    return q(cur, """
        select b.block_no, b.epoch_no, b.time, (select max(id) from tx where block_id <= b.id), b.slot_no
        from block b where b.block_no is not null order by b.id desc limit 1""")[0]


# Stake keys registered in the state before transaction t (tx_id < t), with
# the transaction of their registration then. Only keys (0xe1): a script
# credential cannot sign an answer. About 6 s on db-sync (25-09-2026).
REGISTERED_BEFORE = """
    select last.addr_id, last.tx_id as reg_tx from (
      select distinct on (addr_id) addr_id, tx_id, reg from (
        select addr_id, tx_id, cert_index, true as reg from stake_registration where tx_id < %(t)s
        union all
        select addr_id, tx_id, cert_index, false from stake_deregistration where tx_id < %(t)s) ev
      order by addr_id, tx_id desc, cert_index desc) last
    join stake_address sa on sa.id = last.addr_id
    where last.reg and get_byte(sa.hash_raw, 0) = 225"""


def live_credentials(cur, tip_tx):
    """Stake keys registered now, with the tx of their current registration."""
    cur.execute("create temp table live as " + REGISTERED_BEFORE, {'t': tip_tx + 1})
    cur.execute("create unique index on live(addr_id); analyze live")


def epoch_first_tx(cur, epoch):
    """db-sync's number of the first transaction of an epoch, and the number
    of its block. Found through the slot index: asked by epoch_no, the planner
    walks the primary key and takes minutes (measured 25-09-2026)."""
    slot = SHELLEY_START + (epoch - SHELLEY_EPOCH) * EPOCH_SECONDS - SHELLEY_UNIX_MINUS_SLOT
    block_id, block_no = q(cur, """
        select id, block_no from block where slot_no >= %(s)s order by slot_no limit 1""", {'s': slot})[0]
    tx_id = q(cur, "select id from tx where block_id >= %(b)s order by block_id, id limit 1", {'b': block_id})[0][0]
    return tx_id, block_no


def population_at(cur, close_tx, by_addr):
    """The stake keys registered when an action closed, as (reg_tx sorted,
    cumulative lovelace in the same order) for bisecting on an action's pos.
    A key that was registered before the action and still at its closing was
    registered throughout: a deregistration in between would have needed a
    new registration, later than the action. Lovelace per key from the ADA
    snapshot; a key not in it (deregistered since) holds 0 there."""
    rows = sorted(q(cur, REGISTERED_BEFORE, {'t': close_tx}), key=lambda r: r[1])
    cum, a = [], 0
    for addr_id, _ in rows:
        a += by_addr.get(addr_id, 0)
        cum.append(a)
    return [r[1] for r in rows], cum


ELIG_DIR = os.path.expanduser(os.environ.get('TVOAH_ELIG_DIR', '~/.cache/tvoah/elig'))
ELIG_PREFIX = 3


def eligibility_shards(cur):
    """Per registered stake key: db-sync's number for the transaction of its
    current registration, comparable with an action's 'pos' from the same
    run. (A chain position per key, block and index, costs a lookup in tx and
    block per key: over 10 minutes for 1.46 million, measured 24-09-2026.)
    Split by the first three hex digits of the key hash into 4096 files of
    about 25 kB, so that a connected wallet fetches only its own. A file is
    rewritten only when its content changed, so that publishing copies only
    those; a db-sync rebuild renumbers, and then every file changes once."""
    rows = q(cur, """
        select encode(sa.hash_raw, 'hex'), l.reg_tx
        from live l join stake_address sa on sa.id = l.addr_id""")   # live holds keys only (0xe1)
    shards = {}
    for raw, reg_tx in rows:
        h = raw[2:]
        shards.setdefault(h[:ELIG_PREFIX], {})[h[ELIG_PREFIX:]] = reg_tx
    os.makedirs(ELIG_DIR, exist_ok=True)
    changed = 0
    for n in range(16 ** ELIG_PREFIX):
        name = f'{n:0{ELIG_PREFIX}x}'
        body = (json.dumps(shards.get(name, {}), sort_keys=True, separators=(',', ':')) + '\n').encode()
        path = os.path.join(ELIG_DIR, name + '.json')
        try:
            with open(path, 'rb') as f:
                if f.read() == body:
                    continue
        except OSError:
            pass
        write_atomic(path, lambda f: f.write(body))
        changed += 1
    return len(rows), changed


def write_atomic(path, write):
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix='.tmp-')
    with os.fdopen(fd, 'wb') as f:
        write(f)
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def ada_snapshot(path):
    """Heavy: ADA per live credential, stored sorted by registration tx so the
    light run can sum any 'registered before' set with one bisect."""
    cur = connect(timeout_min=45)
    tip_block, tip_epoch, tip_time, tip_tx, _ = pin_tip(cur)
    live_credentials(cur, tip_tx)
    # Unspent = no tx_in spends it (tx_out.consumed_by_tx_id is not maintained in this db-sync).
    rows = q(cur, """
        select l.reg_tx, coalesce(u.v, 0) + coalesce(r.v, 0), l.addr_id
        from live l
        left join (
          select o.stake_address_id addr_id, sum(o.value) v
          from tx_out o join live l2 on l2.addr_id = o.stake_address_id
          where o.tx_id <= %(t)s
            and not exists (select 1 from tx_in i
                            where i.tx_out_id = o.tx_id and i.tx_out_index = o.index and i.tx_in_id <= %(t)s)
          group by 1) u using (addr_id)
        left join (
          select addr_id, sum(v) v from (
            select addr_id, amount v from reward where spendable_epoch <= %(e)s
            union all select addr_id, amount from reward_rest where spendable_epoch <= %(e)s
            union all select addr_id, -amount from withdrawal where tx_id <= %(t)s) x
          join live using (addr_id)
          group by 1) r using (addr_id)
        order by l.reg_tx""", {'t': tip_tx, 'e': tip_epoch})
    snap = {'epoch': tip_epoch, 'block': tip_block,
            'time': tip_time.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
            'reg_tx': [r[0] for r in rows], 'lovelace': [int(r[1]) for r in rows],
            # so that the ADA behind the answers comes from the same epoch as
            # the ADA of all wallets (answers.py)
            'addr_id': [r[2] for r in rows]}
    write_atomic(path, lambda f: f.write(gzip.compress(json.dumps(snap).encode())))
    print(f"ada snapshot at block {tip_block}, epoch {tip_epoch}: {len(rows)} wallets, "
          f"{sum(snap['lovelace']) // LOVELACE} ada")


def load_snapshot():
    """Cumulative ADA over credentials ordered by registration tx, or None."""
    if not os.path.exists(SNAPSHOT):
        return None
    with open(SNAPSHOT, 'rb') as f:
        s = json.loads(gzip.decompress(f.read()))
    cum, a = [], 0
    for lov in s['lovelace']:
        a += lov
        cum.append(a)
    by_addr = dict(zip(s['addr_id'], s['lovelace'])) if 'addr_id' in s else None
    return {'epoch': s['epoch'], 'block': s['block'], 'reg_tx': s['reg_tx'], 'cum': cum, 'by_addr': by_addr}


def light(out_path):
    cur = connect(timeout_min=10)
    tip_block, tip_epoch, tip_time, tip_tx, tip_slot = pin_tip(cur)
    live_credentials(cur, tip_tx)
    reg_txs = [r[0] for r in q(cur, "select reg_tx from live order by reg_tx")]
    snap = load_snapshot()
    if snap and snap['by_addr'] is None:
        print("ADA snapshot has no addr_id (made by an older release); the ada run makes a new one")

    def eligible_before(tx_id):
        heads = bisect_left(reg_txs, tx_id)           # wallets registered before tx_id, still registered
        ada = None
        if snap:
            i = bisect_left(snap['reg_tx'], tx_id)
            ada = snap['cum'][i - 1] // LOVELACE if i else 0
        return heads, ada

    actions = []
    for (gid, tx_hash, idx, gtype, expiration, ratified, enacted, dropped, expired,
         submitted, submitted_time, tx_id, anchor_url, anchor_hash) in q(cur, """
        select g.id, encode(tx.hash, 'hex'), g.index, g.type::text, g.expiration,
               g.ratified_epoch, g.enacted_epoch, g.dropped_epoch, g.expired_epoch,
               b.epoch_no, b.time, g.tx_id, va.url, encode(va.data_hash, 'hex')
        from gov_action_proposal g
        join tx on tx.id = g.tx_id
        join block b on b.id = tx.block_id
        left join voting_anchor va on va.id = g.voting_anchor_id
        where g.tx_id <= %(t)s
        order by g.tx_id desc, g.index desc""", {'t': tip_tx}):
        if enacted is not None:
            status, status_epoch = 'enacted', enacted
        elif ratified is not None:
            status, status_epoch = 'ratified', ratified
        elif expired is not None:
            status, status_epoch = 'expired', expired
        elif dropped is not None:
            status, status_epoch = 'dropped', dropped
        else:
            status, status_epoch = 'open', expiration
        heads, ada = eligible_before(tx_id)
        zero = {'yes': 0, 'no': 0, 'none': 0}
        # The first epoch in which the ledger accepts no more votes on the
        # action: the one in which it leaves the proposals, or expiration,
        # whichever comes first (see answers.py for how this was measured).
        removed = (enacted if enacted is not None else ratified + 1 if ratified is not None
                   else expired if expired is not None else dropped)
        closing = min(expiration, removed) if removed is not None else expiration
        actions.append({
            # Answers are taken until the closing time, whatever the outcome
            # label says: a ratified action is still open in its ratified epoch.
            'answerable': closing > tip_epoch,
            'id': f'{tx_hash}-{idx}',
            'gov_action_id': f'{tx_hash}#{idx}',
            'type': gtype,
            # Title and abstract come from the anchored document, fetched and
            # hash-checked by anchors.py; db-sync is on-chain only.
            'anchor_url': anchor_url,
            'anchor_hash': anchor_hash,
            'title': '',
            'abstract': '',
            'submitted_epoch': submitted,
            'submitted_at': submitted_time.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
            # db-sync's number for the proposal's transaction; a wallet may
            # answer if its registration has a lower one (elig/ files).
            'pos': tx_id,
            # db-sync's expiration is the first epoch in which the action is no
            # longer open (submitted + govActionLifetime + 1; expired_epoch equals
            # it, and no vote was ever cast in it). Open through closing - 1,
            # closing at the start of epoch closing: expiration at the latest.
            'expires_epoch': expiration,
            'last_open_epoch': closing - 1,
            'closes_at': epoch_start_iso(closing),
            'status': status,
            'status_epoch': status_epoch,
            'eligible': {'heads': heads, 'ada': ada},
            'heads': dict(zero),
            'ada': dict(zero),
            'groups': [],
            # for answers.count, removed there
            'tx_id': tx_id,
            'closing_epoch': closing,
            'closes_at_utc': epoch_start_iso(closing).replace('Z', '+00:00'),
            '_ada': dict(zero),
            '_groups': {},
        })

    elig_count, elig_changed = eligibility_shards(cur)

    records = answers.scan(cur, tip_block, tip_tx)
    closing_of = {a['id']: a.pop('closing_epoch') for a in actions}
    per_credential, answer_summary = answers.count(cur, records, actions, tip_time, tip_tx,
                                                   snap['by_addr'] if snap else None)
    ada_epoch = snap['epoch'] if snap else None
    for a in actions:
        a['ada_epoch'] = ada_epoch if answer_summary['ada_from'] == 'snapshot' else None
    frozen = freeze_closed(cur, actions, closing_of, tip_block, tip_epoch, snap)

    # What the site needs to build an answer transaction: the fee and
    # minimum-output rules of the current epoch (the latest row, should the
    # run fall on the epoch boundary before db-sync has written the new one).
    min_fee_a, min_fee_b, max_tx_size, coins_per_utxo_byte = q(cur, """
        select min_fee_a, min_fee_b, max_tx_size, coins_per_utxo_size
        from epoch_param where epoch_no <= %(e)s order by epoch_no desc limit 1""", {'e': tip_epoch})[0]

    data = {
        'example': False,
        # Signing on the site is open to everyone (live since 25-09-2026);
        # False turns it off without a new site release.
        'answers_open': True,
        'params': {'min_fee_a': int(min_fee_a), 'min_fee_b': int(min_fee_b),
                   'max_tx_size': int(max_tx_size), 'coins_per_utxo_byte': int(coins_per_utxo_byte)},
        'tally': {'block': tip_block, 'epoch': tip_epoch, 'slot': tip_slot,
                  'time': tip_time.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
                  'ada_epoch': snap['epoch'] if snap else None},
        'eligible': {'credentials': len(reg_txs),
                     'ada': (snap['cum'][-1] // LOVELACE) if snap and snap['cum'] else None},
        'answers': answer_summary,
        'news': news(actions, records, tip_time, tip_epoch),
        'eligibility': {'dir': 'elig', 'prefix': ELIG_PREFIX, 'keys': elig_count},
        'actions': actions,
    }
    # Every counted and uncounted answer per stake key hash, for a wallet to
    # find its own, and for anyone to audit the tally.
    answers_path = os.path.join(os.path.dirname(os.path.abspath(out_path)), 'answers.json')
    write_atomic(answers_path, lambda f: f.write((json.dumps(
        {'tally': data['tally'], 'label': answers.LABEL, 'credentials': per_credential},
        ensure_ascii=False, sort_keys=True) + '\n').encode()))
    write_atomic(out_path, lambda f: f.write((json.dumps(data, ensure_ascii=False, indent=1) + '\n').encode()))
    print(f"tally at block {tip_block}, epoch {tip_epoch}: {len(actions)} actions, "
          f"{len(reg_txs)} wallets, ada from epoch {snap['epoch'] if snap else 'none'}; "
          f"answers: {answer_summary}; eligibility: {elig_count} keys, {elig_changed} files changed; "
          f"closed actions: {frozen}")


NEWS_DAYS = 14          # how far back the ticker looks
NEWS_CLOSING_DAYS = 3   # an open action closing within this many days is news
NEWS_MAX = 12


def news(actions, records, tip_time, tip_epoch):
    """What happened on chain lately, newest first, for the ticker on the site:
    actions submitted, ratified, enacted, expired or dropped; open actions
    closing soon; answers under label 1695 in the last day; when the current
    epoch ends, and that it began during its first day. Only events, never a
    choice of what matters: the chain sets the agenda here too. The site
    writes the sentences, in both languages."""
    from datetime import datetime, timedelta
    tip = tip_time.replace(tzinfo=timezone.utc)
    since = tip - timedelta(days=NEWS_DAYS)
    iso = lambda t: t.isoformat().replace('+00:00', 'Z')
    at = lambda s_: datetime.fromisoformat(s_.replace('Z', '+00:00'))
    events = []
    for a in actions:
        if at(a['submitted_at']) >= since:
            events.append({'time': a['submitted_at'], 'kind': 'submitted', 'action': a['id']})
        if a['status'] != 'open':
            t = at(epoch_start_iso(a['status_epoch']))
            if since <= t <= tip:
                events.append({'time': iso(t), 'kind': a['status'], 'action': a['id']})
        if a['answerable'] and at(a['closes_at']) - tip <= timedelta(days=NEWS_CLOSING_DAYS):
            events.append({'time': iso(tip), 'kind': 'closing', 'action': a['id'], 'closes_at': a['closes_at']})
    recent = [r for r in records if r['valid'] and at(r['time']) >= tip - timedelta(days=1)]
    if recent:
        events.append({'time': iso(tip), 'kind': 'answers_day', 'count': len(recent)})
    began = epoch_start_iso(tip_epoch)
    if tip - at(began) <= timedelta(days=1):
        events.append({'time': began, 'kind': 'epoch_began', 'epoch': tip_epoch})
    events.append({'time': iso(tip), 'kind': 'epoch_ends', 'epoch': tip_epoch,
                   'ends_at': epoch_start_iso(tip_epoch + 1)})
    events.sort(key=lambda e: e['time'], reverse=True)
    return events[:NEWS_MAX]


RESULT_KEYS = ('eligible', 'heads', 'ada', 'groups', 'ada_epoch')
# The rules a kept closed action was counted by. Raise it with any change to
# how a closed action's figures are made: kept figures of another version are
# thrown away and the actions frozen again (one query per closing epoch).
CLOSED_RULES = 1


def freeze_closed(cur, actions, closing_of, tip_block, tip_epoch, snap):
    """A closed action's figures are those of its closing time. The wallets
    are the keys registered from before its submission until its closing; the
    live set above only has those still registered now, and would lose every
    key that deregisters later. So the set is read as it stood at the closing
    (one query per closing epoch), and once the closing block is deeper than
    a rollback reaches, everything the action shows is kept in CLOSED and
    never computed again, ADA included, with the epoch of the snapshot it came
    from. Until then it is computed each run. Resumable: kept per action as
    soon as it is final. Without an ADA snapshot per key (addr_id) nothing is
    kept, and the figures stay those of the live set."""
    try:
        with open(CLOSED) as f:
            stored = json.load(f)
    except (OSError, ValueError):
        stored = {}
    if 'actions' not in stored:          # written before the version was kept (25-09-2026): rules 1
        stored = {'rules': 1, 'actions': stored}
    kept = stored['actions'] if stored['rules'] == CLOSED_RULES else {}
    if stored['rules'] != CLOSED_RULES and stored['actions']:
        print(f"closed actions: kept figures are of rules {stored['rules']}, now {CLOSED_RULES}; freezing again")
    usable = snap is not None and snap['by_addr'] is not None
    by_epoch = {}
    for a in actions:
        if a['id'] in kept:
            a.update(kept[a['id']])
        elif closing_of[a['id']] <= tip_epoch and usable:
            by_epoch.setdefault(closing_of[a['id']], []).append(a)
    counts = {'kept': len([a for a in actions if a['id'] in kept]), 'new': 0, 'unsettled': 0}
    for epoch in sorted(by_epoch):
        close_tx, close_block = epoch_first_tx(cur, epoch)
        reg, cum = population_at(cur, close_tx, snap['by_addr'])
        settled = tip_block - close_block >= ROLLBACK_BLOCKS
        for a in by_epoch[epoch]:
            i = bisect_left(reg, a['pos'])
            a['eligible'] = {'heads': i, 'ada': cum[i - 1] // LOVELACE if i else 0}
            # the answers' ADA came from the same snapshot only if count() used it
            if settled and a['ada_epoch'] == snap['epoch']:
                kept[a['id']] = {k: a[k] for k in RESULT_KEYS}
                counts['new'] += 1
            else:
                counts['unsettled'] += 1
        if settled:
            write_atomic(CLOSED, lambda f: f.write((json.dumps({'rules': CLOSED_RULES, 'actions': kept},
                                                              sort_keys=True) + '\n').encode()))
    return counts


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--ada':
        ada_snapshot(sys.argv[2])
    elif len(sys.argv) == 2:
        light(sys.argv[1])
    else:
        sys.exit('usage: tally.py OUT.json | tally.py --ada SNAPSHOT.json.gz')
