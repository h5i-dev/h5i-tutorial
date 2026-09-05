#!/usr/bin/env bash
# Lab 09 — the register body is merged into the record whole, `is_admin` and all.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9090}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab09
WHO="climber$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# `json.is_admin=true` is written unquoted, so h5i sends a JSON boolean rather
# than the string "true". Python's `if not row["is_admin"]` treats "false" as
# truthy, so the type matters here as much as the name.
TOKEN="$(send "$SESSION" req_0 --create \
    --set method=POST --set path=/api/register \
    --set header.Content-Type=application/json \
    --set "json.username=$WHO" --set "json.email=$WHO@example.test" \
    --set json.password=hunter2 --set json.is_admin=true | jfield token)"

send "$SESSION" req_0 --create --set path=/api/admin/keys \
    --set "header.Authorization=Bearer $TOKEN" | flag
