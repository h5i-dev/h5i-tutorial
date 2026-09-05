#!/usr/bin/env bash
# run.sh NN   — run lab NN's scraper and write out/NN-name.csv
# run.sh NN - — run it and print the CSV instead of saving it
# run.sh      — list the labs
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if [ $# -eq 0 ]; then
    for dir in "$ROOT"/labs/[0-9][0-9]-*/; do
        name="$(basename "$dir")"
        printf '  %s  %s\n' "${name%%-*}" "$(sed -n '2s/^# *//p' "$dir/scrape.sh")"
    done
    exit 0
fi

NN="$1"
DIR="$(echo "$ROOT/labs/$NN"-*)"
[ -d "$DIR" ] || { echo "no lab $NN — run ./run.sh for the list" >&2; exit 1; }

if [ "${2:-}" = "-" ]; then
    exec bash "$DIR/scrape.sh"
fi

mkdir -p "$ROOT/out"
OUT="$ROOT/out/$(basename "$DIR").csv"
bash "$DIR/scrape.sh" > "$OUT" || { echo "the scraper failed; $OUT may be partial" >&2; exit 1; }
printf '%s  (%d rows)\n' "$OUT" "$(( $(wc -l < "$OUT") - 1 ))"
