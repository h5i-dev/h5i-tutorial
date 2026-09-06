#!/usr/bin/env bash
# Lab 10 — Oxylabs sandbox: the data is not in the markup, it is beside it.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://sandbox.oxylabs.io/products"

session games10 "$SITE"

# Look at what a selector-first scraper is up against here. This is a Next.js
# app, and its class names are content hashes: `product-card css-e8at8d
# eag3qlw10`. `css-e8at8d` is generated from the stylesheet and changes when
# anybody edits the CSS, so a scraper written against it breaks on a deploy
# that changed nothing you care about.
"$H5I" browser extract '{"class": {"selector": "div.product-card", "attr": "class"}}' \
    --session games10 | sed 's/^/# /' >&2

# So do not start with selectors. A server-rendered React app ships the props
# it rendered from, as JSON, in `#__NEXT_DATA__` — typed, complete, unhashed,
# and carrying fields the page never displays. Look for it before you write a
# single selector. The equivalents worth checking on any page: `#__NEXT_DATA__`
# (Next.js), `self.__next_f` (newer Next.js), `window.__NUXT__` (Nuxt),
# `<script type="application/ld+json">` (schema.org), and any `data-*`
# attribute holding a JSON array (lab 08).
"$H5I" browser extract '{"next_data": "#__NEXT_DATA__"}' --session games10 | python3 -c '
import csv, json, sys

page = json.loads(json.load(sys.stdin)["next_data"])
props = page["props"]["pageProps"]
print("# page %s of %s, %s products in all"
      % (props["currentPage"], props["pageCount"], props["totalCount"]), file=sys.stderr)

fields = ["id", "game_name", "developer", "platform", "genre", "type",
          "rating", "meta_score", "user_score", "inStock"]
out = csv.DictWriter(sys.stdout, fields, extrasaction="ignore", lineterminator="\n")
out.writeheader()
for product in props["products"]:
    out.writerow(product)
'

# And the pagination is in there too: `pageCount` is a number the site told you,
# not one you inferred by crawling until a link went missing.
