#!/usr/bin/env bash
# test-all.sh [NN ...] — run every scraper and check it returned a table.
#
# This is not the websec course's test-all.sh, and cannot be. Those labs run on
# loopback against an application in the repository, so a failure is a bug in
# the lab. These ten run against ten sites nobody here controls: a failure may
# be a bug, or a redesign, or a site that is down, or your network. The script
# says which lab and what it got; deciding which of those it was is yours.
#
# It makes roughly thirty requests in all, paced one second apart.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
MIN_ROWS="${MIN_ROWS:-5}"

LABS=("$@")
if [ ${#LABS[@]} -eq 0 ]; then
    LABS=($(ls "$ROOT/labs" | grep -E '^[0-9]{2}-' | cut -d- -f1))
fi

PASS=0; FAIL=0; FAILED=()
for nn in "${LABS[@]}"; do
    dir="$(echo "$ROOT/labs/$nn"-*)"
    name="$(basename "$dir")"
    if out="$(bash "$dir/scrape.sh" 2>/dev/null)"; then
        n=$(( $(printf '%s\n' "$out" | grep -c '') - 1 ))
        if [ "$n" -ge "$MIN_ROWS" ]; then
            printf '  ok    %-28s %5d rows\n' "$name" "$n"; PASS=$((PASS+1))
        else
            printf '  FAIL  %-28s %5d rows (wanted %s or more)\n' "$name" "$n" "$MIN_ROWS"
            FAIL=$((FAIL+1)); FAILED+=("$nn")
        fi
    else
        printf '  FAIL  %-28s the scraper exited non-zero\n' "$name"
        FAIL=$((FAIL+1)); FAILED+=("$nn")
    fi
done

printf '\n%d passed, %d failed' "$PASS" "$FAIL"
[ $FAIL -gt 0 ] && printf ' (%s)' "${FAILED[*]}"
echo
exit $((FAIL > 0))
