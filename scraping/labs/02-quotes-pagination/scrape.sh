#!/usr/bin/env bash
# Lab 02 — Quotes to Scrape: quote, author, tags, across pages.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://quotes.toscrape.com"
PAGES="${PAGES:-2}"

session quotes02 "$SITE/"

# Tags are the interesting column: a quote has zero or more of them, so
# `["div.tags a.tag"]` returns thirty values for ten quotes and lines up with
# nothing. There is no schema that fixes this, because `extract` has no notion
# of a row. Read the tags per quote instead: `div.quote` is one quote, and its
# `.tags` attribute carries them already joined.
SCHEMA='{
  "quote":  ["div.quote span.text"],
  "author": ["div.quote small.author"],
  "about":  [{"selector": "div.quote span a", "attr": "href"}],
  "tags":   [{"selector": "div.quote div.tags meta[itemprop=keywords]", "attr": "content"}]
}'

url="$SITE/"
for n in $(seq 1 "$PAGES"); do
    answer="$("$H5I" browser extract "$SCHEMA" --url "$url" --session quotes02)" || exit 1
    if [ "$n" = 1 ]; then
        printf '%s' "$answer" | rows quote author about tags
    else
        printf '%s' "$answer" | rows quote author about tags | tail -n +2
    fi

    pace
    next="$("$H5I" browser extract '{"next": {"selector": "li.next a", "attr": "href"}}' \
        --session quotes02 | python3 -c 'import json,sys; print(json.load(sys.stdin)["next"])')"
    [ -n "$next" ] && [ "$next" != "None" ] || break
    url="$next"
    pace
done
