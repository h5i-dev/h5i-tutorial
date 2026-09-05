# 3. One page

Everything in this course, on one screen.

---

## Open, read, close

```bash
h5i browser read URL --text                     # one page, no session
h5i browser read URL --json                     # + the request log
h5i browser read URL1 URL2 URL3                 # a batch
h5i browser read URL --script                   # run the page's JavaScript

h5i browser open URL --session s --new          # a session you will drive
h5i browser open URL --session s --new --script
h5i browser open URL --session s --new --allow https://cdn.example
h5i browser close --session s
h5i browser list                                # what is still running
```

## Reads, cheapest first

```bash
h5i browser structured --session s              # JSON-LD, OpenGraph, <meta>
h5i browser markdown   --session s              # the page as prose
h5i browser markdown   --session s --max-bytes 4000
h5i browser snapshot   --session s              # outline + @ref handles
h5i browser extract '{…}' --session s
```

Any read verb takes `--url URL` and does navigate-then-read in one trip.

## The extract schema

| Form | Answers |
| --- | --- |
| `"k": "SEL"` | first match's text, as a string |
| `"k": ["SEL"]` | every match's text, as a list |
| `"k": {"selector": "SEL", "attr": "A"}` | first match's attribute, as a string |
| `"k": [{"selector": "SEL", "attr": "A"}]` | every match's attribute, as `[{"A": …}]` |

```json
{
  "title":  "div.product_main h1",
  "prices": ["article.product_pod p.price_color"],
  "next":   {"selector": "li.next a", "attr": "href"},
  "links":  [{"selector": "h3 a", "attr": "href"}],
  "js":     ["script"]
}
```

* text is trimmed at the ends, not internally
* `href` and `src` come back absolute
* attributes worth knowing: `href`, `src`, `title`, `content`, `value`, `class`,
  `data-*`, `outerHTML`, `innerHTML`
* no key matched anything → an error; one key matched nothing → an empty column
* **no row grouping.** Anchor every selector at the row container.

## Turning columns into rows

```bash
h5i browser extract '{…}' --session s | python3 lib/rows.py col1 col2 col3
```

Refuses unequal columns. Unwraps `{"href": "…"}`. Writes CSV with a header.

```bash
# the check, by hand
… | python3 -c 'import json,sys; print({k: len(v) for k,v in json.load(sys.stdin).items()})'
```

## Where the data hides

| Where | How to look |
| --- | --- |
| page metadata | `h5i browser structured` |
| a `data-*` attribute | `{"d": {"selector": "[data-items]", "attr": "data-items"}}` |
| Next.js (pages) | `{"d": "#__NEXT_DATA__"}` |
| Next.js (app) | `{"js": ["script"]}`, look for `self.__next_f` |
| Nuxt / Redux SSR | `{"js": ["script"]}`, look for `__NUXT__`, `__INITIAL_STATE__` |
| JSON-LD | `{"d": "script[type='application/ld+json']"}` |
| an inline literal | `{"js": ["script"]}` |
| an endpoint | `{"js": ["script"]}`, read the URL; or click once and read `requests` |

## Driving

```bash
h5i browser snapshot   --session s                 # -> [ref=e9]
h5i browser type   @e9 "text" --session s
h5i browser submit @e9 --session s                 # -> {"method", "url"}
h5i browser click  @e3 --session s
h5i browser select @e5 'Express shipping' --session s
h5i browser set-checked @e4 true --session s
h5i browser press  @e1 Enter --session s
h5i browser scroll 4000 --session s
h5i browser wait-for --selector 'tr.film' --session s
h5i browser wait-for --text 'Results' --session s
h5i browser find --role textbox --session s        # -> a durable CSS selector
h5i browser screenshot --session s                 # when a read surprises you
```

* a `@ref` is valid for the snapshot it came from; take it fresh
* `find` answers with a selector — that is what to keep
* `set-checked` sets; a click toggles
* `{"ok": true}` means dispatched, not effective

## What did I actually fetch

```bash
h5i browser requests --session s
h5i browser requests --session s --since 42
h5i browser audit    --session s
```

* written before the bytes move: not in the log ⇒ did not happen
* `DENIED … not in the allowlist` ⇒ add `--allow ORIGIN` at open time
* count the `200 GET`s against the pages you meant to fetch

## Pagination

```bash
next=$(h5i browser extract '{"n": {"selector": "li.next a", "attr": "href"}}' --session s \
       | python3 -c 'import json,sys; print(json.load(sys.stdin)["n"] or "")')
[ -n "$next" ] || break
```

Stop on the site's signal. Verify against the site's total. Never stop on "this
page had fewer rows."

## This course

```bash
./run.sh                 # list the labs
./run.sh 01              # run lab 01, write out/01-books-to-scrape.csv
./run.sh 01 -            # run it, print the CSV
PAGES=10 ./run.sh 02     # take more of the site
PACE=3 ./run.sh 09       # be slower
./test-all.sh            # all ten, ~30 requests
cat labs/01-*/README.md  # the brief
cat labs/01-*/NOTES.md   # the writeup
```

Next: [`04-etiquette-and-scope.md`](04-etiquette-and-scope.md).
