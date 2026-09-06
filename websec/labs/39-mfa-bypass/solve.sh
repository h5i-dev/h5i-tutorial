#!/usr/bin/env bash
# Lab 39 — the "temporary" token from step one is a session everywhere else.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9390}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab39

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

TOKEN="$(send "$SESSION" req_0 --create --set method=POST --set path=/api/login \
    --set header.Content-Type=application/json \
    --set json.user=dana --set json.password=correct-horse | jfield token)"

# Step two never happens.
send "$SESSION" req_0 --create --set path=/api/vault \
    --set "header.Authorization=Bearer $TOKEN" | flag
