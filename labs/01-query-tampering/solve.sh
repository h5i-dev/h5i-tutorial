#!/usr/bin/env bash
# Lab 01 — the response names the levels; only one of them is ever requested.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9010}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab01

"$H5I" browser open "$URL/api/status?level=public" --session "$SESSION" --new --capture >/dev/null
send "$SESSION" req_0 --set query.level=internal | flag
