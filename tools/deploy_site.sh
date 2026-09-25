#!/bin/bash
# Deploy the site (the committed HEAD of this repo) to SITE_HOST:SITE_DIR and
# check it: hashes on the server equal to the repo, and the site answering
# through its domain. SITE_HOST and SITE_DIR come from the environment or
# from ~/.config/tvoah/env, as for the generator.
set -euo pipefail
[ -f ~/.config/tvoah/env ] && . ~/.config/tvoah/env
: "${SITE_HOST:?set SITE_HOST}" "${SITE_DIR:?set SITE_DIR}"
cd "$(dirname "$(readlink -f "$0")")/.."
FILES="index.html action.html how.html recount.html contact.html disclaimer.html app.js sign.js styles.css vendor/blake2b.js"
[ -z "$(git status --porcelain -- $FILES)" ] || { echo "site files not committed"; exit 1; }
rsync -aR --chmod=F644 $FILES "$SITE_HOST:$SITE_DIR/"
ssh "$SITE_HOST" "cd $SITE_DIR && sha256sum $FILES" | sha256sum -c --quiet && echo "site = $(git log --format=%h -1)"
curl -s -o /dev/null -w "through the domain: HTTP %{http_code}\n" https://voiceofadaholders.com/disclaimer.html
