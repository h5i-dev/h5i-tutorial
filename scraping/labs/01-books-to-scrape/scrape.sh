#!/usr/bin/env bash
# Lab 01 — Books to Scrape: a list page, the page after it, and one detail page.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://books.toscrape.com"
PAGES="${PAGES:-2}"          # how many list pages to walk. Two is the demo.

session books01 "$SITE/"

# The list page. Every selector is anchored to `article.product_pod`, the
# element that *is* one book, so all four columns are the same length even if a
# card is missing a field. rows.py refuses to zip them otherwise.
LIST='{
  "title": [{"selector": "article.product_pod h3 a", "attr": "title"}],
  "price": ["article.product_pod p.price_color"],
  "stock": ["article.product_pod p.instock.availability"],
  "url":   [{"selector": "article.product_pod h3 a", "attr": "href"}]
}'

url="$SITE/"
for n in $(seq 1 "$PAGES"); do
    # `--url` navigates and reads in one round trip, and the answer names the
    # URL it ended up on, so a redirect is never silent.
    answer="$("$H5I" browser extract "$LIST" --url "$url" --session books01)" || exit 1
    if [ "$n" = 1 ]; then
        printf '%s' "$answer" | rows title price stock url
    else
        printf '%s' "$answer" | rows title price stock url | tail -n +2
    fi

    pace
    next="$("$H5I" browser extract '{"next": {"selector": "li.next a", "attr": "href"}}' \
        --session books01 | python3 -c 'import json,sys; print(json.load(sys.stdin)["next"])')"
    [ -n "$next" ] && [ "$next" != "None" ] || break
    url="$next"
    pace
done

# One detail page, to show what the list page does not carry. The list gives a
# truncated title and a rating in a class name; the detail page gives the UPC,
# the exact stock count, and the category.
pace
"$H5I" browser extract '{
  "title":    "div.product_main h1",
  "price":    "div.product_main p.price_color",
  "upc":      "table.table-striped tr:nth-child(1) td",
  "stock":    "table.table-striped tr:nth-child(6) td",
  "category": "ul.breadcrumb li:nth-child(3) a"
}' --url "$SITE/catalogue/a-light-in-the-attic_1000/index.html" --session books01 >&2
