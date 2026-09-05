#!/usr/bin/env bash
# Lab 04 — Scrape This Site, Countries: 250 rows, one page, one request.
set -uo pipefail
. "$(dirname "$0")/../../lib/h5i.sh"

PAGE="https://www.scrapethissite.com/pages/simple/"

session countries04 "$PAGE"

# There is no pagination and no script here. The whole dataset is in the
# markup of one page, and the right number of requests is one. Check that
# number afterwards with `h5i browser requests`: a scraper that fetched more
# pages than the data has is a scraper with a bug.
"$H5I" browser extract '{
  "country":    ["div.country h3.country-name"],
  "capital":    ["div.country span.country-capital"],
  "population": ["div.country span.country-population"],
  "area_km2":   ["div.country span.country-area"]
}' --session countries04 | rows country capital population area_km2

# Count *navigations*, not responses: a page pulls stylesheets and images,
# and those are subresources rather than pages. `--json` labels each request
# with its initiator, which is the distinction you want.
"$H5I" browser requests --session countries04 --json | python3 -c '
import json, sys
rows = json.load(sys.stdin)
rows = rows["requests"] if isinstance(rows, dict) else rows
pages = [r for r in rows if r["phase"] == "response" and r["initiator"] == "navigation"]
denied = [r for r in rows if r["phase"] == "request" and not r["allowed"]]
print("# pages fetched: %d, third-party subresources refused: %d"
      % (len(pages), len(denied)), file=sys.stderr)
' 
