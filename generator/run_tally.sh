#!/bin/bash
# The Voice of ADA Holders — one generator run.
#
#   run_tally.sh light   every quarter hour: actions, wallets, documents,
#                        translations, publish data.json to the site
#   run_tally.sh ada     once per epoch: ADA per wallet into the snapshot
#
# db-sync is reached through an ssh tunnel to DBSYNC_HOST, where postgres
# listens on localhost only. The site is published with rsync to
# SITE_HOST:SITE_DIR. These come from the environment (the timers read
# ~/.config/tvoah/env); there are no defaults, so no host is assumed.
# Guards, because the db-sync machine also carries the node:
#   - one run at a time (flock); a run that finds the lock held exits 0
#   - the ada run starts only with enough free memory on the VM, and only
#     when the snapshot is from an earlier epoch or lacks the ADA per key
#     (addr_id, which the ADA behind the answers and closed actions need)
#   - translation runs only when nothing else is on the GPU (any compute
#     process, or the systemd unit TVOAH_GPU_UNIT if set); otherwise cached
#     translations are used and new ones wait for the next run
#   - data.json on the site is replaced only by a complete, valid file
#   - translation is not allowed to hold back the tally: if it fails, the
#     run goes on with cached translations only
set -euo pipefail

MODE="${1:-light}"
HERE="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
STATE="${TVOAH_STATE:-$HOME/.local/state/tvoah}"
DBSYNC_HOST="${DBSYNC_HOST:?set DBSYNC_HOST: the ssh host that runs db-sync}"
LOCAL_PORT="${LOCAL_PORT:-15432}"
SITE_HOST="${SITE_HOST:?set SITE_HOST: the ssh host that serves the site}"
SITE_DIR="${SITE_DIR:?set SITE_DIR: the web root on SITE_HOST}"
MIN_FREE_GB="${MIN_FREE_GB:-12}"
export TVOAH_ADA_SNAPSHOT="${TVOAH_ADA_SNAPSHOT:-$HOME/.cache/tvoah/ada_snapshot.json.gz}"

mkdir -p "$STATE"
exec 9>"$STATE/run.lock"
if ! flock -n 9; then
    echo "another tvoah run holds the lock; skipping this $MODE run"
    exit 0
fi

WORK="$(mktemp -d)"
TUN=""
cleanup() { if [ -n "$TUN" ]; then kill "$TUN" 2>/dev/null || true; fi; rm -rf "$WORK"; }
trap cleanup EXIT

ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
    -L "${LOCAL_PORT}:127.0.0.1:5432" "$DBSYNC_HOST" &
TUN=$!
for _ in $(seq 1 20); do
    (exec 3<>"/dev/tcp/127.0.0.1/${LOCAL_PORT}") 2>/dev/null && break
    sleep 0.5
done
export TVOAH_DSN="host=127.0.0.1 port=${LOCAL_PORT} dbname=cexplorer user=tvoah_ro"

if [ "$MODE" = ada ]; then
    free_kb="$(ssh "$DBSYNC_HOST" "awk '/MemAvailable/{print \$2}' /proc/meminfo")"
    if [ "$free_kb" -lt $((MIN_FREE_GB * 1024 * 1024)) ]; then
        echo "db-sync VM has $((free_kb / 1024 / 1024)) GB available, below ${MIN_FREE_GB} GB; not starting the ada snapshot"
        exit 0
    fi
    current="$(python3 -c 'import os,psycopg2; c=psycopg2.connect(os.environ["TVOAH_DSN"]).cursor(); c.execute("select max(epoch_no) from block"); print(c.fetchone()[0])')"
    have="$(python3 -c 'import gzip,json,os; p=os.environ["TVOAH_ADA_SNAPSHOT"]; s=json.loads(gzip.decompress(open(p,"rb").read())) if os.path.exists(p) else {}; print(s["epoch"] if "addr_id" in s else -1)')"
    if [ "$have" -ge "$current" ]; then
        echo "ada snapshot is from epoch $have, current epoch $current; nothing to do"
        exit 0
    fi
    python3 -u "$HERE/tally.py" --ada "$TVOAH_ADA_SNAPSHOT"
    exit 0
fi

OUT="$WORK/data.json"
python3 -u "$HERE/tally.py" "$OUT"
python3 -u "$HERE/anchors.py" "$OUT"

gpu_busy="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null | grep -c . || true)"
if [ "$gpu_busy" -gt 0 ] || { [ -n "${TVOAH_GPU_UNIT:-}" ] && systemctl is-active --quiet "$TVOAH_GPU_UNIT"; }; then
    echo "GPU in use by another job; using cached translations only"
    TVOAH_TRANSLATE_CACHE_ONLY=1 python3 -u "$HERE/translate.py" "$OUT"
elif ! python3 -u "$HERE/translate.py" "$OUT"; then
    echo "translation failed; publishing with cached translations only"
    TVOAH_TRANSLATE_CACHE_ONLY=1 python3 -u "$HERE/translate.py" "$OUT"
fi

python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['actions'], 'no actions'" "$OUT"

# The verified proposal documents, served from this site for the full-proposal
# view. Only documents whose bytes matched the hash on chain; each is copied
# once (the chain fixes its bytes, so a copy never goes stale).
python3 -c "
import json, sys
for a in json.load(open(sys.argv[1]))['actions']:
    if a.get('title_status') == 'verified' and a.get('anchor_hash'):
        print(a['anchor_hash'] + '.json')" "$OUT" | sort -u > "$WORK/docs.list"
ssh "$SITE_HOST" "mkdir -p ${SITE_DIR}/docs"
rsync -a --ignore-existing --chmod=F644 --files-from="$WORK/docs.list" \
    "$HOME/.cache/tvoah/anchors/" "${SITE_HOST}:${SITE_DIR}/docs/"
# Eligibility per stake key, in 4096 files; only changed files are rewritten
# by tally.py, so rsync copies only those.
rsync -a --chmod=D755,F644 "$HOME/.cache/tvoah/elig/" "${SITE_HOST}:${SITE_DIR}/elig/"
scp -q "$WORK/answers.json" "${SITE_HOST}:${SITE_DIR}/.answers.json.new"
scp -q "$OUT" "${SITE_HOST}:${SITE_DIR}/.data.json.new"
ssh "$SITE_HOST" "mv ${SITE_DIR}/.answers.json.new ${SITE_DIR}/answers.json && mv ${SITE_DIR}/.data.json.new ${SITE_DIR}/data.json"
echo "published to ${SITE_HOST}:${SITE_DIR}/data.json"
