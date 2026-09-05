#!/usr/bin/env bash
# Lab 36 — the discounts are added together and nothing says a coupon is once.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9360}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab36

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# Four × 25% is 100%. Repeats are allowed because nobody said they were not.
send "$SESSION" req_0 --create --set method=POST --set path=/api/checkout \
    --set header.Content-Type=application/json \
    --set json.item=enterprise-license \
    --set 'json.coupons=["FRIEND25","FRIEND25","FRIEND25","FRIEND25"]' | flag
