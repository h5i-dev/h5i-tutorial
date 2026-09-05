#!/usr/bin/env bash
# Lab 04 — the authorization rule lists GET and POST. PUT is not on the list.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9040}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab04

"$H5I" browser open "$URL/admin/payslips" --session "$SESSION" --new --capture >/dev/null
send "$SESSION" req_0 --set method=PUT | flag
