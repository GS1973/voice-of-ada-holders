#!/bin/bash
# Install the committed generator as a release and (re)load its user timers.
# The timers run ~/.local/opt/tvoah/current, never the work tree.
set -euo pipefail
REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
if [ -n "$(git -C "$REPO" status --porcelain -- generator)" ]; then
    echo "generator/ has uncommitted changes; commit first" >&2
    exit 1
fi
SHA="$(git -C "$REPO" rev-parse --short HEAD)"
BASE="$HOME/.local/opt/tvoah"
DEST="$BASE/$SHA"
mkdir -p "$DEST"
git -C "$REPO" archive HEAD generator | tar -x -C "$DEST" --strip-components=1
ln -sfn "$DEST" "$BASE/current.new"
mv -T "$BASE/current.new" "$BASE/current"
mkdir -p "$HOME/.config/systemd/user"
cp "$DEST"/systemd/*.service "$DEST"/systemd/*.timer "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
echo "installed $SHA -> $BASE/current"
