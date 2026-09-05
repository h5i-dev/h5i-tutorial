#!/usr/bin/env bash
# test-all.sh [NN ...] — run every lab's PoC and check it prints that lab's flag.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
LABS=("$@")
if [ ${#LABS[@]} -eq 0 ]; then
    LABS=($(ls "$ROOT/labs" | grep -E '^[0-9]{2}-' | cut -d- -f1))
fi
PASS=0; FAIL=0; FAILED=()
for nn in "${LABS[@]}"; do
    name="$(basename "$(echo "$ROOT/labs/$nn"-*)")"
    if out="$("$ROOT/solve.sh" "$nn" 2>&1)"; then
        printf '  ok    %s\n' "$name"; PASS=$((PASS+1))
    else
        printf '  FAIL  %s\n%s\n' "$name" "$(printf '%s' "$out" | sed 's/^/          /')"
        FAIL=$((FAIL+1)); FAILED+=("$nn")
    fi
done
printf '\n%d passed, %d failed' "$PASS" "$FAIL"
[ $FAIL -gt 0 ] && printf ' (%s)' "${FAILED[*]}"
echo
exit $((FAIL > 0))
