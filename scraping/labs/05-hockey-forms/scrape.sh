#!/usr/bin/env bash
# Lab 05 — Scrape This Site, Hockey Teams: drive the form once, then stop
# using it.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://www.scrapethissite.com/pages/forms/"
QUERY="${QUERY:-New York}"
PAGES="${PAGES:-2}"

session hockey05 "$SITE"

# Step one: use the form, once, to find out what the form does.
#
# A @ref comes from a snapshot and belongs to that snapshot: the engine refuses
# a stale one rather than resolving it against whatever now sits in that
# position. So take it from the reading you are about to act on, and take it by
# what the element *is* — `textbox` — rather than by counting lines.
ref="$("$H5I" browser snapshot --session hockey05 \
    | sed -n 's/.*- textbox .*\[ref=\([a-z0-9]*\)\].*/\1/p' | head -1)"
[ -n "$ref" ] || { echo "no search box on $SITE — the page changed" >&2; exit 1; }

# `find` is the other way in, and answers with a CSS selector rather than a
# @ref: `{"role": "textbox", "name": "Search for Teams:", "selector": "#q"}`.
# Keep that selector when you are writing a scraper to run again tomorrow; a
# @ref does not survive the next reading.
"$H5I" browser find --role textbox --session hockey05 >&2

"$H5I" browser type "@$ref" "$QUERY" --session hockey05 >/dev/null
target="$("$H5I" browser submit "@$ref" --session hockey05 \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["url"])')"
echo "# the form is a GET: $target" >&2

# Step two: stop clicking. The form put the search into the query string, so
# every later page is a URL you can build. `page_num` is the site's own
# pagination parameter, visible in the pager links.
SCHEMA='{
  "team":   ["tr.team td.name"],
  "year":   ["tr.team td.year"],
  "wins":   ["tr.team td.wins"],
  "losses": ["tr.team td.losses"],
  "pct":    ["tr.team td.pct"]
}'

for n in $(seq 1 "$PAGES"); do
    url="$target&page_num=$n"
    answer="$("$H5I" browser extract "$SCHEMA" --url "$url" --session hockey05 2>/dev/null)" || break
    if [ "$n" = 1 ]; then
        printf '%s' "$answer" | rows team year wins losses pct
    else
        printf '%s' "$answer" | rows team year wins losses pct | tail -n +2
    fi
    pace
done
