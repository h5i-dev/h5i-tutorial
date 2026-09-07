#!/usr/bin/env bash
# Lab 08 — Web Scraper test site, infinite scroll: what the scroll was hiding.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

PAGE="https://webscraper.io/test-sites/e-commerce/scroll/computers/laptops"

session scroll08 "$PAGE" --script

# The naive loop: scroll, count, scroll again, stop when the count stops
# growing. What it prints depends on the engine. Up to h5i 0.4.1 the scroll
# dispatched no event, so the condition is met on the first comparison and the
# answer is whatever the first render held. After that the page's own handler
# runs and the count grows three at a time, which takes about 39 scrolls to
# reach the 117 the page already had.
#
# Either way the condition is right and the answer is wrong, which is the
# failure a scroll loop is prone to everywhere: "no new items" and "no
# mechanism to produce new items" look identical from inside the loop.
count() {
    "$H5I" browser extract '{"n": ["div.thumbnail a.title"]}' --session scroll08 2>/dev/null \
        | python3 -c 'import json,sys
try: print(len(json.load(sys.stdin)["n"]))
except Exception: print(0)'
}

seen="$(count)"
echo "# rendered before scrolling: $seen" >&2
for _ in 1 2 3; do
    "$H5I" browser scroll 4000 --session scroll08 >/dev/null
    now="$(count)"
    echo "# after a scroll: $now" >&2
    [ "$now" -gt "$seen" ] || break
    seen="$now"
done

# So look at what the page actually shipped. This one carries the entire
# dataset in a `data-items` attribute on the product wrapper: the scroll is a
# rendering decision, and the payload arrived in the first response. One
# request, every row, no script needed at all.
"$H5I" browser extract '{
  "items": {"selector": "[data-items]", "attr": "data-items"},
  "type":  {"selector": "[data-type]",  "attr": "data-type"}
}' --session scroll08 | python3 -c '
import csv, json, sys
page = json.load(sys.stdin)
items = json.loads(page["items"])
print("# data-type=%s, and %d items were in the markup all along"
      % (page["type"], len(items)), file=sys.stderr)
out = csv.DictWriter(sys.stdout, ["id", "title", "price", "description"],
                     extrasaction="ignore", lineterminator="\n")
out.writeheader()
for item in items:
    out.writerow(item)
'
