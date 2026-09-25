# The Voice of ADA Holders

The site at https://voiceofadaholders.com and the program that counts its answers.

ADA holders answer yes, no or no opinion on every Cardano governance action, each with a
transaction from their own wallet that carries the answer under metadata label `1695`. The
record format and the counting rules are a CIP draft, [`cip/README.md`](cip/README.md)
(submitted as cardano-foundation/CIPs#1277). Everything the site shows can be recounted from
the chain with the generator in this repository.

## The site

Static: plain HTML, one stylesheet (`styles.css`), one script for the pages (`app.js`) and one
for signing (`sign.js`, with `vendor/blake2b.js`, blakejs 1.2.1, MIT). No build step, no
backend, no cookies.

- `app.js` holds every visible text in English and Spanish (`TEXT.en`, `TEXT.es`), so both
  languages always carry the same content.
- `sign.js` builds the answer transaction itself (the CBOR is written out, no library), has the
  wallet sign it over CIP-30, checks that the stake key signed, and has the wallet submit it.
  It is on while `data.json` says `answers_open`; otherwise only in a browser switched on with
  `?sign=on` (`?sign=off` again).
- No inline script or style anywhere: buttons are wired in `app.js` (`data-act`), bar widths are
  set from script, and each page names itself in `<body data-page>`, so the site's
  Content-Security-Policy can be `script-src 'self'; style-src 'self'`.
- `data.json` (the tally), `answers.json` (every answer per stake key) and `elig/` (one file per
  first three hex digits of a stake key hash) are written by the generator and published next
  to the pages. They are not kept in this repository.
- `fonts/` is Chivo, self-hosted (SIL OFL 1.1, see `fonts/OFL.txt`).

## The generator

`generator/run_tally.sh light` runs three steps and publishes `data.json`, `answers.json` and
`elig/`:

1. `tally.py`: governance actions, eligible stake keys and the answers under label 1695, read
   from cardano-db-sync in one REPEATABLE READ transaction (read-only role).
2. `anchors.py`: each action's anchored document, kept only if its bytes hash to the value on
   chain; title and abstract come from it.
3. `translate.py`: Spanish machine translation of those texts with a local model (Qwen3-4B,
   int8, on ctranslate2), cached per document hash and marked on the site as machine
   translation.

`generator/run_tally.sh ada` makes the ADA snapshot (ADA per stake key) once per epoch.

What it needs:

- cardano-db-sync with a read-only role; `TVOAH_DSN` is the libpq connection string.
  `run_tally.sh` reaches db-sync through an ssh tunnel to `DBSYNC_HOST` and publishes with
  rsync to `SITE_HOST:SITE_DIR`; both are environment variables.
- Python 3 with psycopg2, cbor2, ctranslate2, tokenizers and wordfreq; `TVOAH_QWEN` points to
  the translation model.
- Caches under `~/.cache/tvoah` (each can be moved with a `TVOAH_*` variable): the answer
  records, the ADA snapshot, the frozen closed actions (`closed_actions.json`, see
  `freeze_closed` in `tally.py`), the eligibility files, the verified documents and the
  translations.
- `generator/systemd/`: user timers, the tally every quarter hour and the ADA snapshot daily at
  03:45 (it runs only in a new epoch). `generator/install.sh` installs the committed generator
  as a release and loads the timers.

## Tests

Run against a published tally (`data.json` from the site):

- `DATA=data.json node tools/render.test.js en|es`: every page drawn in one language, the
  basket, the wallet states, the disclaimer with and without a source address.
- `DATA=data.json node tools/sign.test.js out.json && python3 tools/sign_check.py out.json`:
  answer transactions built and signed against a mock wallet with real ed25519 keys, then
  checked independently with pycardano.
- With playwright and its chromium: `tools/open_check.py` (signing open or closed),
  `tools/menu_check.py` (the menu on a phone), `tools/phone_fit.py` (no page or dialog wider
  than a 320 or 360 px screen), `tools/phone_shots.py` (screenshots).

`tools/deploy_site.sh` is the maintainer's deploy: the committed pages to the web server,
checked by hash.

## License

Copyright 2026 Smit Blockchain Operations (Pool BKIND).

The code is licensed under the Apache License, Version 2.0 ([`LICENSE`](LICENSE)). The CIP draft
in `cip/` is licensed under CC-BY-4.0, as its header says. `fonts/` is Chivo under the SIL
Open Font License 1.1 (`fonts/OFL.txt`); `vendor/blake2b.js` is blakejs 1.2.1 under the MIT
license (`vendor/blakejs.LICENSE`).
