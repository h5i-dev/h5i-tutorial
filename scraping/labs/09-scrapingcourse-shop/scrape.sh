#!/usr/bin/env bash
# Lab 09 — ScrapingCourse shop: pagination with a stop condition you can trust.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://www.scrapingcourse.com/ecommerce/"
PAGES="${PAGES:-2}"

session shop09 "$SITE"

# The page states its own size: "Showing 1–16 of 188 results". Read it, and you
# have a total to check the crawl against — the difference between "the loop
# ended" and "the loop collected everything" is the whole reliability of a
# scraper, and a count you did not verify is a guess.
total="$("$H5I" browser extract '{"count": "p.woocommerce-result-count"}' --session shop09 \
    | python3 -c 'import json,re,sys
text = json.load(sys.stdin)["count"] or ""
m = re.search(r"of\s+([\d,]+)", text)
print(m.group(1).replace(",", "") if m else "?")')"
echo "# the page says there are $total products in all" >&2

SCHEMA='{
  "name":  ["li.product .product-name"],
  "price": ["li.product .product-price"],
  "url":   [{"selector": "li.product a.woocommerce-LoopProduct-link", "attr": "href"}],
  "image": [{"selector": "li.product img.product-image", "attr": "src"}]
}'

url="$SITE"
got=0
for n in $(seq 1 "$PAGES"); do
    answer="$("$H5I" browser extract "$SCHEMA" --url "$url" --session shop09)" || exit 1
    if [ "$n" = 1 ]; then
        printf '%s' "$answer" | rows name price url image
    else
        printf '%s' "$answer" | rows name price url image | tail -n +2
    fi
    got=$((got + $(printf '%s' "$answer" | rows name price url image | tail -n +2 | wc -l)))

    pace
    # `a.next.page-numbers` is absent on the last page, and absence is the stop
    # condition. Do not stop on "this page returned fewer rows than the last":
    # a page that is short because a request failed looks exactly the same.
    next="$("$H5I" browser extract '{"next": {"selector": "a.next.page-numbers", "attr": "href"}}' \
        --session shop09 2>/dev/null \
        | python3 -c 'import json,sys
try: print(json.load(sys.stdin)["next"] or "")
except Exception: print("")')"
    [ -n "$next" ] && [ "$next" != "None" ] || { echo "# no next link: this was the last page" >&2; break; }
    url="$next"
    pace
done

echo "# collected $got of $total (PAGES=$PAGES of the crawl)" >&2
