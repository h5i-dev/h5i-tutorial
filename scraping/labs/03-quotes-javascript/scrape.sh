#!/usr/bin/env bash
# Lab 03 — Quotes to Scrape (JavaScript): the same data, written by a script.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

PAGE="https://quotes.toscrape.com/js/"
SCHEMA='{"quote": ["div.quote span.text"], "author": ["div.quote small.author"]}'

# First, the negative result — and the point of the lab is that it *is* a
# result. With script off, the markup this page serves contains no quotes at
# all: they are written into the DOM by an inline `<script>` holding a `data`
# array. `extract` answers with empty columns, which is a fact about the page.
echo "# script off:" >&2
session quotes03 "$PAGE"
"$H5I" browser extract "$SCHEMA" --session quotes03 \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print("#   %d quotes" % len(d["quote"]))' >&2
"$H5I" browser close --session quotes03 >/dev/null 2>&1

# Then the same read with `--script`. Off is the default because a page that
# runs no script has no channel through which to deliver a prompt injection;
# turning it on is a decision, and this is a page that needs it.
pace
echo "# script on:" >&2
session quotes03s "$PAGE" --script
"$H5I" browser extract "$SCHEMA" --session quotes03s | rows quote author
