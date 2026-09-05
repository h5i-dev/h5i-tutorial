#!/usr/bin/env bash
# Lab 08 — alice's request, bob's cookies. One flag does it: `--as`.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9080}"
. "$(dirname "$0")/../lib/h5i.sh"
ALICE="lab08-alice-$$"; BOB="lab08-bob-$$"
trap '"$H5I" browser close --session "$ALICE" >/dev/null 2>&1;
      "$H5I" browser close --session "$BOB" >/dev/null 2>&1' EXIT

login() {  # login SESSION USER
    "$H5I" browser open "$URL/" --session "$1" --new --capture >/dev/null
    send "$1" req_0 --create --set method=POST --set path=/login \
        --set header.Content-Type=application/json --set "json.user=$2" >/dev/null
}
login "$ALICE" alice
login "$BOB" bob

# The manager reaches the page. This is the request worth testing.
send "$ALICE" req_0 --create --set path=/api/reports/quarterly >/dev/null

# Same message, bob's jar. `--as` drops the source session's own credentials,
# which is exactly the question: does the endpoint check the caller or the URL?
send "$ALICE" "$(last "$ALICE")" --as "$BOB" | flag
