// The Voice of ADA Holders: signing the answers in the basket.
//
// Builds one transaction carrying every answer under metadata label 1695, in
// the record format of the CIP draft (cip/README.md), asks the wallet to sign
// it over CIP-30, and hands it back to the wallet to submit. No library: the
// transaction is a handful of CBOR fields, written here so that anyone can read
// what is signed. blake2b comes from vendor/blake2b.js.
//
//   body     inputs from the wallet, one change output back to the wallet,
//            fee, time-to-live, auxiliary data hash, and the wallet's stake
//            key hash in required_signers
//   metadata { 1695: { 0: 1, 1: [0, stake key hash], 2: [[[tx, ix], choice], …] } }
//
// The time-to-live is never later than the closing time of any action in the
// basket, so the ledger itself refuses an answer that would arrive too late;
// nor later than the next epoch boundary, where every closing falls, so an
// answer lands in the epoch it was signed in (a dropped action closes at a
// boundary without notice).
// Before submitting, the wallet's signatures are checked: without the stake
// key's signature the ledger would refuse the transaction, and the wallet is
// told so instead.
//
// Signing uses the wallet connected in the top bar (app.js), and first checks
// that the wallet is still on that account. It is on for everyone while the
// tally says answers_open (data.json); when it does not, only in a browser
// switched on with ?sign=on (and off again with ?sign=off).

const SIGN_KEY = 'tvoah.sign';
const SENT_KEY = 'tvoah.sent';
const LABEL = 1695;
const CHOICE = { no: 0, yes: 1, none: 2 };            // as the ledger's Vote
const SHELLEY_UNIX_MINUS_SLOT = 1591566291;           // mainnet: slot = unix time - this
const SHELLEY_SLOT = 4492800, EPOCH_SLOTS = 432000;   // mainnet: epoch 208 began at slot 4492800
const TTL_SECONDS = 2 * 3600;
const MAX_INPUTS = 30;
const FEE_MARGIN_BYTES = 110;                         // about 0.005 ADA: one extra witness (101) fits

(function switchFromUrl() {
  const v = new URLSearchParams(location.search).get('sign');
  try {
    if (v === 'on') localStorage.setItem(SIGN_KEY, 'on');
    if (v === 'off') localStorage.removeItem(SIGN_KEY);
  } catch (e) { /* storage blocked: stays off */ }
})();
function signingOn() {
  if (typeof DATA !== 'undefined' && DATA && DATA.answers_open === true) return true;
  try { return localStorage.getItem(SIGN_KEY) === 'on'; } catch (e) { return false; }
}

// ---------- bytes ----------

const hexToBytes = h => Uint8Array.from(h.match(/../g) || [], b => parseInt(b, 16));
const bytesToHex = b => Array.from(b, x => x.toString(16).padStart(2, '0')).join('');
const concatBytes = parts => {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
};
const blake = (bytes, len) => window.blakejs.blake2b(bytes, null, len);
const sameBytes = (a, b) => a.length === b.length && a.every((x, i) => x === b[i]);

// ---------- CBOR (RFC 8949), the part a transaction needs ----------

class Tagged { constructor(tag, value) { this.tag = tag; this.value = value; } }

function cborHead(major, n) {
  n = BigInt(n);
  const m = major << 5;
  if (n < 24n) return Uint8Array.of(m | Number(n));
  if (n < 0x100n) return Uint8Array.of(m | 24, Number(n));
  if (n < 0x10000n) return Uint8Array.of(m | 25, Number(n >> 8n), Number(n & 0xffn));
  if (n < 0x100000000n) return Uint8Array.of(m | 26, ...[24n, 16n, 8n, 0n].map(s => Number((n >> s) & 0xffn)));
  return Uint8Array.of(m | 27, ...[56n, 48n, 40n, 32n, 24n, 16n, 8n, 0n].map(s => Number((n >> s) & 0xffn)));
}

// Values: number/BigInt, Uint8Array (bytes), string, Array, Map (keys in
// insertion order), Tagged, true/false.
function cborEncode(v) {
  if (typeof v === 'number' || typeof v === 'bigint') {
    const n = BigInt(v);
    return n >= 0n ? cborHead(0, n) : cborHead(1, -1n - n);
  }
  if (v instanceof Uint8Array) return concatBytes([cborHead(2, v.length), v]);
  if (typeof v === 'string') { const b = new TextEncoder().encode(v); return concatBytes([cborHead(3, b.length), b]); }
  if (Array.isArray(v)) return concatBytes([cborHead(4, v.length), ...v.map(cborEncode)]);
  if (v instanceof Map) {
    const parts = [cborHead(5, v.size)];
    for (const [k, x] of v) parts.push(cborEncode(k), cborEncode(x));
    return concatBytes(parts);
  }
  if (v instanceof Tagged) return concatBytes([cborHead(6, v.tag), cborEncode(v.value)]);
  if (v === true) return Uint8Array.of(0xf5);
  if (v === false) return Uint8Array.of(0xf4);
  throw new Error('cannot encode ' + typeof v);
}

// Integers decode to BigInt, maps to Map, tags to Tagged. Returns the value
// and the offset after it, so a caller can cut out the raw bytes of an item.
function cborDecode(b, i = 0) {
  const ib = b[i++], major = ib >> 5, info = ib & 31;
  const arg = () => {
    if (info < 24) return BigInt(info);
    const len = { 24: 1, 25: 2, 26: 4, 27: 8 }[info];
    if (!len) throw new Error('bad CBOR length');
    let n = 0n;
    for (let k = 0; k < len; k++) n = (n << 8n) | BigInt(b[i++]);
    return n;
  };
  const items = (fn) => {           // definite or indefinite count
    if (info === 31) { while (b[i] !== 0xff) fn(); i++; return; }
    const n = Number(arg());
    for (let k = 0; k < n; k++) fn();
  };
  const next = () => { const r = cborDecode(b, i); i = r.end; return r.value; };
  switch (major) {
    case 0: return { value: arg(), end: i };
    case 1: return { value: -1n - arg(), end: i };
    case 2: case 3: {
      let out;
      if (info === 31) {
        const parts = [];
        while (b[i] !== 0xff) { const r = cborDecode(b, i); parts.push(major === 2 ? r.value : new TextEncoder().encode(r.value)); i = r.end; }
        i++; out = concatBytes(parts);
      } else { const n = Number(arg()); out = b.slice(i, i + n); i += n; }
      return { value: major === 2 ? out : new TextDecoder().decode(out), end: i };
    }
    case 4: { const a = []; items(() => a.push(next())); return { value: a, end: i }; }
    case 5: { const m = new Map(); items(() => { const k = next(); m.set(typeof k === 'bigint' ? Number(k) : k, next()); }); return { value: m, end: i }; }
    case 6: { const tag = Number(arg()); return { value: new Tagged(tag, next()), end: i }; }
    case 7:
      if (info === 20) return { value: false, end: i };
      if (info === 21) return { value: true, end: i };
      if (info === 22 || info === 23) return { value: null, end: i };
      throw new Error('unsupported CBOR simple value');
  }
}
const untag = v => (v instanceof Tagged ? v.value : v);

// ---------- addresses ----------

// Payment key hash of a Shelley address whose payment part is a key; null for
// script addresses, Byron addresses and anything else this cannot sign for.
function paymentKeyHash(addr) {
  const type = addr[0] >> 4;
  return [0, 2, 4, 6].includes(type) && addr.length >= 29 ? addr.slice(1, 29) : null;
}

// ---------- values ----------

// { coin: BigInt, assets: Map('policyhex.namehex' -> BigInt) }
function outputValue(out) {
  const amount = out instanceof Map ? out.get(1) : out[1];
  const v = { coin: 0n, assets: new Map() };
  if (typeof amount === 'bigint') { v.coin = amount; return v; }
  v.coin = amount[0];
  for (const [policy, names] of untag(amount[1])) {
    for (const [name, q] of names) v.assets.set(bytesToHex(policy) + '.' + bytesToHex(name), q);
  }
  return v;
}
function addValue(a, b) {
  const assets = new Map(a.assets);
  for (const [k, q] of b.assets) assets.set(k, (assets.get(k) || 0n) + q);
  return { coin: a.coin + b.coin, assets };
}
// Canonical order (RFC 8949 §4.2.3): shorter keys first, then bytewise.
const canonical = (x, y) => x.length - y.length || (x < y ? -1 : x > y ? 1 : 0);
function encodeValue(v) {
  if (!v.assets.size) return v.coin;
  const policies = new Map();
  for (const k of [...v.assets.keys()].sort()) {
    const [p, n] = k.split('.');
    if (!policies.has(p)) policies.set(p, []);
    policies.get(p).push(n);
  }
  const ma = new Map();
  for (const p of [...policies.keys()].sort(canonical)) {
    const names = new Map();
    for (const n of policies.get(p).sort(canonical)) names.set(hexToBytes(n), v.assets.get(p + '.' + n));
    ma.set(hexToBytes(p), names);
  }
  return [v.coin, ma];
}

// ---------- the transaction ----------

function answerMetadata(stakeKeyHash, answers) {
  const list = answers.map(([id, choice]) => {
    const [tx, ix] = id.split('-');
    return [[hexToBytes(tx), Number(ix)], CHOICE[choice]];
  });
  const record = new Map([[0, 1], [1, [0, stakeKeyHash]], [2, list]]);
  return cborEncode(new Map([[LABEL, record]]));
}

function txBody({ inputs, changeAddr, change, fee, ttl, auxHash, stakeKeyHash }) {
  return cborEncode(new Map([
    [0, inputs.map(u => [u.txHash, u.index])],
    [1, [new Map([[0, changeAddr], [1, encodeValue(change)]])]],
    [2, fee],
    [3, ttl],
    [7, auxHash],
    [14, [stakeKeyHash]],
  ]));
}

// Chooses inputs and computes fee and change. Plain-ADA outputs are used first,
// so that tokens stay where they are unless the ADA alone does not suffice;
// any token in a chosen input goes back in the change output.
function buildTx({ utxos, changeAddr, stakeKeyHash, auxBytes, ttl, params }) {
  const auxHash = blake(auxBytes, 32);
  const usable = utxos.filter(u => u.keyHash)
    .sort((a, b) => (a.value.assets.size - b.value.assets.size) || (b.value.coin > a.value.coin ? 1 : -1));
  const chosen = [];
  let total = { coin: 0n, assets: new Map() };
  for (const u of usable.slice(0, MAX_INPUTS)) {
    chosen.push(u);
    total = addValue(total, u.value);
    const signers = new Set(chosen.map(c => bytesToHex(c.keyHash))).size + 1;
    // A vkey witness is [32-byte key, 64-byte signature]: 101 bytes in CBOR.
    // Wallets wrap them differently (a set tag adds 3 bytes; a wallet may add
    // a witness of its own, 101 more), so the estimate carries a margin of
    // FEE_MARGIN_BYTES; after signing the real size is checked against the
    // fee before anything is sent. The fee field is taken at its widest.
    const size = body => 1 + body.length + (8 + 101 * signers) + 1 + auxBytes.length + FEE_MARGIN_BYTES;
    let fee = 0n, change, body;
    for (let round = 0; round < 3; round++) {
      change = { coin: total.coin - fee, assets: total.assets };
      body = txBody({ inputs: chosen, changeAddr, change, fee: fee || 0xffffffffn, ttl, auxHash, stakeKeyHash });
      fee = BigInt(params.min_fee_a) * BigInt(size(body)) + BigInt(params.min_fee_b);
    }
    change = { coin: total.coin - fee, assets: total.assets };
    const outBytes = cborEncode(new Map([[0, changeAddr], [1, encodeValue(change)]]));
    const minAda = BigInt(params.coins_per_utxo_byte) * BigInt(160 + outBytes.length);
    if (change.coin < minAda) continue;
    body = txBody({ inputs: chosen, changeAddr, change, fee, ttl, auxHash, stakeKeyHash });
    if (size(body) > params.max_tx_size) break;
    return { body, fee, inputs: chosen };
  }
  return null;
}

// ---------- the wallet ----------

class SignError extends Error { constructor(key, detail) { super(key); this.key = key; this.detail = detail; } }

// NuFi is left out (decided 24-09-2026): tested, it gave no outputs through
// getUtxos() while reporting a balance, and warned it could not parse a valid
// Conway transaction. It did sign and send in the end, through the fallbacks.
const LEFT_OUT = /nufi/i;

function wallets() {
  const c = window.cardano || {};
  return Object.keys(c).filter(k => c[k] && typeof c[k].enable === 'function' && c[k].name)
    .filter(k => !LEFT_OUT.test(k) && !LEFT_OUT.test(String(c[k].name)))
    .map(k => ({ key: k, name: String(c[k].name), icon: String(c[k].icon || '') }));
}

// Enables the wallet and reads its stake key hash: what connecting does, and
// the first step of signing.
async function enableWallet(walletKey) {
  let api;
  try { api = await window.cardano[walletKey].enable(); } catch (e) { throw new SignError('declined', e); }
  if (Number(await api.getNetworkId()) !== 1) throw new SignError('wrongNet');
  const rewards = (await api.getRewardAddresses()) || [];
  if (!rewards.length) throw new SignError('noStake');
  const reward = hexToBytes(rewards[0]);
  if (reward[0] >> 4 === 15) throw new SignError('script');
  if (reward[0] >> 4 !== 14 || reward.length !== 29) throw new SignError('noStake');
  return { api, stakeKeyHash: reward.slice(1) };
}
async function stakeKeyOf(walletKey) { return bytesToHex((await enableWallet(walletKey)).stakeKeyHash); }

async function signAnswers(walletKey, answers, data, step, expectStake) {
  step('connect');
  const { api, stakeKeyHash } = await enableWallet(walletKey);
  if (expectStake && bytesToHex(stakeKeyHash) !== expectStake) throw new SignError('walletChanged');

  step('build');
  const changeAddr = hexToBytes(await api.getChangeAddress());
  // Some wallets answer getUtxos() without arguments with nothing at all.
  // Then ask again: page by page (CIP-30 paginate), for an amount, and last
  // the collateral, which wallets leave out of getUtxos (a wallet holding one
  // output that it keeps as collateral otherwise offers nothing).
  const tries = [
    ['plain', () => api.getUtxos()],
    ['paged', async () => {
      let all = [];
      for (let page = 0; page < 20; page++) {
        const part = (await api.getUtxos(undefined, { page, limit: 50 })) || [];
        all = all.concat(part);
        if (part.length < 50) break;
      }
      return all;
    }],
    ['amount', () => api.getUtxos(bytesToHex(cborEncode(3000000n)))],
    ['collateral', () => (api.getCollateral ? api.getCollateral({ amount: bytesToHex(cborEncode(3000000n)) })
      : api.experimental && api.experimental.getCollateral ? api.experimental.getCollateral() : null)],
  ];
  let raw = [], source = 'none';
  for (const [name, get] of tries) {
    try { raw = (await get()) || []; } catch (e) { raw = []; }
    if (raw.length) { source = name; break; }
  }
  if (source !== 'plain') console.info('outputs from the wallet via:', source, raw.length);
  const utxos = raw.map(h => {
    const [input, output] = cborDecode(hexToBytes(h)).value;
    const addr = output instanceof Map ? output.get(0) : output[0];
    return { txHash: input[0], index: Number(input[1]), keyHash: paymentKeyHash(addr), value: outputValue(output), addrType: addr[0] >> 4 };
  });

  // Now, in slots: this computer's clock, but never before the tally the page
  // loaded plus the time since (a clock hours behind would give a
  // time-to-live the ledger has already passed).
  const clientSlot = Math.floor(Date.now() / 1000) - SHELLEY_UNIX_MINUS_SLOT;
  const tallySlot = data.tally && data.tally.slot
    ? data.tally.slot + Math.floor((performance.now() - (data._loadedAt ?? performance.now())) / 1000) : 0;
  const nowSlot = Math.max(clientSlot, tallySlot);
  const actions = answers.map(([id]) => data.actions.find(a => a.id === id));
  if (actions.some(a => !a)) throw new SignError('closing');           // no longer in the tally
  const closeSlots = actions.map(a => Math.floor(Date.parse(a.closes_at) / 1000) - SHELLEY_UNIX_MINUS_SLOT);
  if (!closeSlots.every(Number.isFinite)) throw new SignError('failed');
  const nextEpochSlot = SHELLEY_SLOT + (Math.floor((nowSlot - SHELLEY_SLOT) / EPOCH_SLOTS) + 1) * EPOCH_SLOTS;
  const ttl = Math.min(nowSlot + TTL_SECONDS, nextEpochSlot, ...closeSlots);
  if (ttl < nowSlot + 300) throw new SignError(Math.min(...closeSlots) < nowSlot + 300 ? 'closing' : 'epochEdge');

  const auxBytes = answerMetadata(stakeKeyHash, answers);
  const built = buildTx({ utxos, changeAddr, stakeKeyHash, auxBytes, ttl, params: data.params });
  if (!built) {
    // What the wallet offered, for finding out why nothing fit.
    let balance = null;
    try { const v = cborDecode(hexToBytes(await api.getBalance())).value; balance = String(Array.isArray(v) ? v[0] : v); } catch (e) { balance = 'unreadable'; }
    console.error('no inputs fit the fee:', JSON.stringify({
      walletBalance: balance, source,
      utxos: utxos.length,
      keyLocked: utxos.filter(u => u.keyHash).length,
      adaOnly: utxos.filter(u => u.keyHash && !u.value.assets.size).length,
      lovelace: utxos.reduce((n, u) => n + u.value.coin, 0n).toString(),
      addressTypes: [...new Set(utxos.map(u => u.addrType))],
    }));
    throw new SignError('noFunds');
  }
  const { body } = built;
  const unsigned = concatBytes([Uint8Array.of(0x84), body, Uint8Array.of(0xa0, 0xf5), auxBytes]);

  step('sign');
  let witHex;
  try { witHex = await api.signTx(bytesToHex(unsigned), true); } catch (e) { throw new SignError('declined', e); }
  const witBytes = hexToBytes(witHex);
  const wit = cborDecode(witBytes).value;
  const signed = new Set(((wit instanceof Map && untag(wit.get(0))) || []).map(w => bytesToHex(blake(w[0], 28))));
  if (!signed.has(bytesToHex(stakeKeyHash))) throw new SignError('noStakeSig');
  if (built.inputs.some(u => !signed.has(bytesToHex(u.keyHash)))) throw new SignError('missingSig');

  const tx = concatBytes([Uint8Array.of(0x84), body, witBytes, Uint8Array.of(0xf5), auxBytes]);
  const minFee = BigInt(data.params.min_fee_a) * BigInt(tx.length) + BigInt(data.params.min_fee_b);
  if (built.fee < minFee) {
    console.error('signed transaction, not sent (fee', String(built.fee), 'below', String(minFee), '):', bytesToHex(tx));
    throw new SignError('feeShort');
  }

  step('submit');
  try { await api.submitTx(bytesToHex(tx)); } catch (e) {
    console.error('signed transaction the wallet could not send:', bytesToHex(tx));
    throw new SignError('submitFailed', e);
  }
  return { txId: bytesToHex(blake(body, 32)), fee: built.fee, ttl };
}

// ---------- the dialog ----------

function openSigner() {
  const w = wallet(), b = basket(), answers = Object.entries(b);
  if (!w || !answers.length || !DATA) return;
  const box = document.createElement('div');
  box.className = 'modal-overlay';
  box.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-label="${T.chooseWallet}">
      <div class="modal-head"><h2>${T.chooseWallet}</h2><button class="btn ghost" data-close>${T.close}</button></div>
      <div class="modal-body"></div></div>`;
  let busy = true;
  const close = () => { if (busy) return; box.remove(); document.removeEventListener('keydown', onKey); document.body.style.overflow = ''; location.reload(); };
  const onKey = e => { if (e.key === 'Escape') close(); };
  box.addEventListener('click', e => { if (e.target === box || e.target.hasAttribute('data-close')) close(); });
  document.addEventListener('keydown', onKey);
  document.body.style.overflow = 'hidden';
  document.body.appendChild(box);
  const body = box.querySelector('.modal-body');
  const say = html => { body.innerHTML = html; };
  (async () => {
    try {
      const r = await signAnswers(w.key, answers, DATA, s => say(`<p>${T.signStep[s]}</p>`), w.stake);
      let sent = [];
      try { sent = JSON.parse(localStorage.getItem(SENT_KEY)) || []; } catch (e) { /* none */ }
      sent.push({ tx: r.txId, at: new Date().toISOString(), ttl: r.ttl, stake: w.stake, answers: b });
      try { localStorage.setItem(SENT_KEY, JSON.stringify(sent)); } catch (e) { /* storage blocked */ }
      say(`<p>${T.signDone(answers.length, `<a href="https://cardanoscan.io/transaction/${r.txId}" target="_blank" rel="noopener noreferrer">${r.txId.slice(0, 16)}…</a>`)}</p>`);
      clearAnswers();
    } catch (e) {
      console.error(e, e.detail);
      const detail = e.detail && (e.detail.info || e.detail.message) ? ` (${esc(String(e.detail.info || e.detail.message))})` : '';
      const msg = T.signErr[e.key] ? T.signErr[e.key](esc(w.name)) : T.signErr.failed(esc(w.name));
      say(`<p>${msg}${detail}</p><p class="fine">${T.nothingSent}</p>`);
    }
    busy = false;
  })();
}
