#!/usr/bin/env bash
# Lab 06 — Scrape This Site, Oscar Winning Films: a click that loads nothing,
# and the endpoint underneath it.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

SITE="https://www.scrapethissite.com/pages/ajax-javascript/"
YEAR="${YEAR:-2015}"

# jQuery comes from ajax.googleapis.com, which this session does not grant
# itself. Without `--allow` the script never arrives, `h5i browser requests`
# says so in as many words, and every later step reads as "the site has no
# data" — which is the worst way for a scraper to fail. Name the origin.
session oscars06 "$SITE" --script --allow https://ajax.googleapis.com

# Step one: try it the way a person would. Click the year, wait for the rows.
ref="$("$H5I" browser snapshot --session oscars06 \
    | sed -n "s/.*- link \"$YEAR\" \[ref=\([a-z0-9]*\)\].*/\1/p" | head -1)"
[ -n "$ref" ] || { echo "no link for $YEAR on $SITE" >&2; exit 1; }

"$H5I" browser click "@$ref" --session oscars06 >/dev/null
echo "# wait-for tr.film: $("$H5I" browser wait-for --selector 'tr.film' --session oscars06 2>&1 | head -1)" >&2

got="$("$H5I" browser extract '{"title": ["tr.film td.film-title"]}' --session oscars06 2>/dev/null \
    | python3 -c 'import json,sys
try: print(len(json.load(sys.stdin)["title"]))
except Exception: print(0)')"
echo "# films after the click: $got" >&2

# Step two, when step one gives you zero. Do not conclude the site is empty and
# do not retry the click. Read what the page fetched, then read the script that
# was supposed to fetch it — the URL is written in the source, in plain text.
if [ "$got" = 0 ]; then
    echo "# the click fired no request. The handler is in the page's own script:" >&2
    "$H5I" browser extract '{"js": ["script"]}' --session oscars06 \
        | python3 -c '
import json, re, sys
js = "\n".join(json.load(sys.stdin)["js"])
call = re.search(r"\$\.ajax\(\{.*?\}\);", js, re.S)
for line in (call.group(0) if call else "no $.ajax call in the page").splitlines()[:12]:
    print("#   " + line.strip().replace("\\", ""))
' >&2
fi

# The endpoint answers JSON, needs no script, and is one request per year. That
# is what the site's own brief tells you to look for, and it is what a scraper
# should be asking for even on a day the click works.
pace
"$H5I" browser read "$SITE?ajax=true&year=$YEAR" --text --json \
    | python3 -c '
import csv, json, sys
page = json.load(sys.stdin)
films = json.loads(page["text"] if "text" in page else page["content"])
out = csv.DictWriter(sys.stdout, ["year", "title", "awards", "nominations", "best_picture"],
                     extrasaction="ignore", lineterminator="\n")
out.writeheader()
for film in films:
    film.setdefault("best_picture", False)
    film["title"] = film["title"].strip()
    out.writerow(film)
'
