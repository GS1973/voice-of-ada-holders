// Build and sign an answer transaction against a mock CIP-30 wallet with real
// ed25519 keys, and write it out for an independent check (tools/sign_check.py,
// cardano-cli). Run:   DATA=path/to/data.json node tools/sign.test.js OUT.hex
// Cases: plain-ada inputs only; tokens needed for the fee; a wallet that adds
// a witness of its own (the fee margin must cover it); a wallet that signs
// without the stake key, and a basket with an action the tally no longer has
// (both refused before anything is submitted).
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

global.window = {};
global.location = { search: '' };
global.localStorage = { getItem: () => null, setItem() {}, removeItem() {} };
require(path.join(__dirname, '..', 'vendor', 'blake2b.js'));
const src = fs.readFileSync(path.join(__dirname, '..', 'sign.js'), 'utf8');
const S = new Function(src + '; return { signAnswers, cborEncode, cborDecode, hexToBytes, bytesToHex, blake, SignError };')();

const data = JSON.parse(fs.readFileSync(process.env.DATA, 'utf8'));
// The rules of the epoch come from the tally; a test without them could not disagree.
if (!data.params) throw new Error('data has no params: use a tally from the generator');
const open = data.actions.filter(a => a.answerable ?? a.status === 'open');
if (!open.length) throw new Error('no open action in data');
const answers = open.map((a, i) => [a.id, ['yes', 'no', 'none'][i % 3]]);

function key() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
  const pub = Buffer.from(publicKey.export({ format: 'jwk' }).x, 'base64url');
  return { pub: new Uint8Array(pub), priv: privateKey, hash: S.blake(new Uint8Array(pub), 28) };
}

function mockWallet({ withTokensOnly, signStake = true, extraWitness = false }) {
  const pay = key(), stake = key();
  const addr = Uint8Array.from([0x01, ...pay.hash, ...stake.hash]);      // base address, mainnet
  const reward = Uint8Array.from([0xe1, ...stake.hash]);
  const txh = n => new Uint8Array(32).fill(n);
  const policy = new Uint8Array(28).fill(7);
  const tokens = coin => [BigInt(coin), new Map([[policy, new Map([[new TextEncoder().encode('TOKEN'), 42n]])]])];
  const utxos = withTokensOnly
    ? [S.cborEncode([[txh(1), 0], [addr, tokens(1500000)]]),               // legacy array output
       S.cborEncode([[txh(2), 3], new Map([[0, addr], [1, tokens(2000000)]])])]
    : [S.cborEncode([[txh(3), 1], new Map([[0, addr], [1, 5000000n]])]),
       S.cborEncode([[txh(4), 0], [addr, tokens(1200000)]])];
  let submitted = null;
  const api = {
    getNetworkId: async () => 1,
    getRewardAddresses: async () => [S.bytesToHex(reward)],
    getChangeAddress: async () => S.bytesToHex(addr),
    getUtxos: async () => utxos.map(S.bytesToHex),
    signTx: async (hex) => {
      const tx = S.hexToBytes(hex);
      const bodyEnd = S.cborDecode(tx, 1).end;
      const h = S.blake(tx.slice(1, bodyEnd), 32);
      const wit = k => [k.pub, new Uint8Array(crypto.sign(null, h, k.priv))];
      const wits = signStake ? [wit(pay), wit(stake)] : [wit(pay)];
      if (extraWitness) wits.push(wit(key()));
      return S.bytesToHex(S.cborEncode(new Map([[0, wits]])));
    },
    submitTx: async (hex) => { submitted = hex; return 'ok'; },
  };
  window.cardano = { mock: { name: 'Mock', enable: async () => api } };
  return { get submitted() { return submitted; }, stakeHash: S.bytesToHex(stake.hash) };
}

(async () => {
  const out = process.argv[2];
  const results = [];
  for (const [name, opts] of [['ada', {}], ['tokens', { withTokensOnly: true }], ['extra-witness', { extraWitness: true }]]) {
    const w = mockWallet(opts);
    const steps = [];
    const r = await S.signAnswers('mock', answers, data, s => steps.push(s));
    if (!w.submitted) throw new Error(name + ': nothing submitted');
    if (steps.join() !== 'connect,build,sign,submit') throw new Error(name + ': steps ' + steps);
    results.push({ case: name, tx: w.submitted, txId: r.txId, fee: String(r.fee), stake: w.stakeHash, answers });
    console.log(`${name}: tx ${r.txId.slice(0, 16)}…, fee ${r.fee}, ${w.submitted.length / 2} bytes`);
  }
  const bad = mockWallet({ signStake: false });
  try {
    await S.signAnswers('mock', answers, data, () => {});
    throw new Error('signed without stake key, yet not refused');
  } catch (e) {
    if (e.key !== 'noStakeSig' || bad.submitted) throw e;
    console.log('no stake signature: refused, nothing submitted');
  }
  const gone = mockWallet({});
  try {
    await S.signAnswers('mock', [...answers, ['ab'.repeat(32) + '-0', 'yes']], data, () => {});
    throw new Error('answer to an action not in the tally, yet not refused');
  } catch (e) {
    if (e.key !== 'closing' || gone.submitted) throw e;
    console.log('action not in the tally: refused, nothing submitted');
  }
  fs.writeFileSync(out, JSON.stringify(results, null, 1));
})().catch(e => { console.error(e); process.exit(1); });
