#!/usr/bin/env python3
"""Independent check of the transactions tools/sign.test.js built, with
pycardano (a separate implementation of the ledger's CBOR):

    python3 tools/sign_check.py OUT.json

Checks per transaction: it decodes as a Conway transaction; the fee covers the
minimum for its size; inputs balance the output plus fee, tokens included;
the change output holds its minimum ada; every signature verifies over the
body hash; the stake key is in required_signers and has signed; the metadata
under label 1695 is exactly the record of the CIP draft with the answers asked.
"""
import hashlib
import io
import json
import sys

import cbor2

from pycardano import Transaction, VerificationKeyWitness
from pycardano.hash import TransactionId

MIN_FEE_A, MIN_FEE_B, COINS_PER_UTXO_BYTE = 44, 155381, 4310
CHOICE = {'no': 0, 'yes': 1, 'none': 2}
TOKEN = (bytes([7] * 28), b'TOKEN', 42)
# The mock wallet's outputs, by the byte its transaction hash is filled with.
MOCK = {1: (1500000, True), 2: (2000000, True), 3: (5000000, False), 4: (1200000, True)}


def check(case):
    raw = bytes.fromhex(case['tx'])
    tx = Transaction.from_cbor(raw)
    body = tx.transaction_body
    fail = lambda m: sys.exit(f"{case['case']}: {m}")

    # The ledger hashes the body bytes as sent; pycardano would re-encode them.
    fp = io.BytesIO(raw)
    fp.seek(1)
    cbor2.CBORDecoder(fp).decode()
    body_hash = hashlib.blake2b(raw[1:fp.tell()], digest_size=32).digest()
    if body_hash.hex() != case['txId']:
        fail('transaction id differs')
    if body.to_cbor() != raw[1:fp.tell()]:
        print(f"{case['case']}: note: pycardano re-encodes the body differently (hash from the bytes as sent)")
    min_fee = MIN_FEE_A * len(raw) + MIN_FEE_B
    if body.fee < min_fee:
        fail(f'fee {body.fee} below minimum {min_fee}')

    coin_in, tokens_in = 0, 0
    for i in body.inputs:
        coin, tok = MOCK[i.transaction_id.payload[0]]
        coin_in += coin
        tokens_in += TOKEN[2] if tok else 0
    if len(body.outputs) != 1:
        fail('expected one change output')
    out = body.outputs[0]
    tokens_out = sum(q for p, assets in (out.amount.multi_asset or {}).items() for n, q in assets.items())
    if out.amount.coin + body.fee != coin_in or tokens_out != tokens_in:
        fail(f'does not balance: in {coin_in}/{tokens_in}, out {out.amount.coin}+{body.fee}/{tokens_out}')
    min_ada = COINS_PER_UTXO_BYTE * (160 + len(out.to_cbor()))
    if out.amount.coin < min_ada:
        fail(f'change {out.amount.coin} below minimum {min_ada}')

    stake = bytes.fromhex(case['stake'])
    if [bytes(h.payload) for h in body.required_signers or []] != [stake]:
        fail('required_signers is not exactly the stake key hash')
    signed = set()
    for w in tx.transaction_witness_set.vkey_witnesses:
        if not verify(w, body_hash):
            fail('a signature does not verify')
        signed.add(bytes(w.vkey.hash().payload))
    if stake not in signed:
        fail('stake key has not signed')

    aux = tx.auxiliary_data
    if body.auxiliary_data_hash is None or bytes(body.auxiliary_data_hash.payload) != bytes(aux.hash().payload):
        fail('auxiliary data hash differs')
    md = aux.data if hasattr(aux, 'data') else aux
    record = dict(md)[1695]
    want = {0: 1, 1: [0, stake], 2: [[[bytes.fromhex(i.split('-')[0]), int(i.split('-')[1])], CHOICE[c]]
                                     for i, c in case['answers']]}
    if normal(record) != normal(want):
        fail(f'record differs:\n {normal(record)}\n {normal(want)}')
    if body.ttl is None:
        fail('no time-to-live')
    print(f"{case['case']}: ok  fee {body.fee} (minimum {min_fee}), {len(raw)} bytes, "
          f"{len(body.inputs)} input(s), ttl {body.ttl}, {len(signed)} signatures")


def verify(w, h):
    from nacl.signing import VerifyKey
    try:
        VerifyKey(w.vkey.payload).verify(h, w.signature)
        return True
    except Exception:
        return False


def normal(x):
    if isinstance(x, dict):
        return {normal(k): normal(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [normal(v) for v in x]
    if isinstance(x, (bytes, bytearray)):
        return bytes(x).hex()
    return x


if __name__ == '__main__':
    for case in json.load(open(sys.argv[1])):
        check(case)
