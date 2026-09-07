#!/usr/bin/env bash
# Lab 07 — Web Scraper test site: walk down the category tree, take price,
# description and review count.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://webscraper.io/test-sites/e-commerce/allinone"
LIMIT="${LIMIT:-2}"          # how many leaf categories to visit

session shop07 "$SITE"

# Read the crawl out of the page rather than hard-coding a list of URLs, so a
# site that adds a category is a site you still cover. Note the two levels:
# `a.subcategory-link` matches nothing on the front page, because the
# subcategories are only rendered once you are inside a category. An empty
# column is a fact about the page, and the fact here is "you are not there yet".
links() {   # links SELECTOR [--url URL] -> one href per line
    local selector="$1"; shift
    "$H5I" browser extract "{\"href\": [{\"selector\": \"$selector\", \"attr\": \"href\"}]}" \
        --session shop07 "$@" 2>/dev/null \
        | python3 -c 'import json,sys
# An attribute read over every match answers a list of bare strings, and on
# h5i 0.4.1 and earlier a list of one-key objects. Take both: a crawl should
# not stop working because the engine got tidier.
try:
    for row in json.load(sys.stdin)["href"]:
        print(row["href"] if isinstance(row, dict) else row)
except Exception: pass'
}

LEAVES=()
while read -r category; do
    [ -n "$category" ] || continue
    pace
    while read -r leaf; do
        [ -n "$leaf" ] && LEAVES+=("$leaf")
    done < <(links a.subcategory-link --url "$category")
    [ "${#LEAVES[@]}" -ge "$LIMIT" ] && break
done < <(links a.category-link)

[ "${#LEAVES[@]}" -gt 0 ] || { echo "no categories found on $SITE" >&2; exit 1; }

# Anchored at `div.thumbnail`, which is one product. `span[itemprop=price]`
# rather than `h4.price`, because the h4 holds the price *and* a `<meta>` with
# the currency, and reading the h4 gets you both smashed together.
SCHEMA='{
  "name":        [{"selector": "div.thumbnail a.title", "attr": "title"}],
  "price":       ["div.thumbnail h4.price span[itemprop=price]"],
  "description": ["div.thumbnail p.description"],
  "reviews":     ["div.thumbnail p.review-count span[itemprop=reviewCount]"],
  "url":         [{"selector": "div.thumbnail a.title", "attr": "href"}]
}'

first=1
for url in "${LEAVES[@]:0:$LIMIT}"; do
    pace
    answer="$("$H5I" browser extract "$SCHEMA" --url "$url" --session shop07 2>/dev/null)" || continue
    if [ "$first" = 1 ]; then
        printf '%s' "$answer" | rows name price description reviews url
        first=0
    else
        printf '%s' "$answer" | rows name price description reviews url | tail -n +2
    fi
done
