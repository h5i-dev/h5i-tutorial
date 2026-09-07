# 2. Approaching a site you have not scraped

The tool is an afternoon. This chapter is the part that transfers.

---

## 2.1 Find the data before you write a selector

Most scraping tutorials start with "inspect element, copy selector." That is
step four of five, and the three steps before it are cheaper, more durable, and
frequently make step four unnecessary.

The order, and one command each:

| | Look for | Command |
| --- | --- | --- |
| 1 | metadata the page publishes about itself | `h5i browser structured` |
| 2 | JSON in a `data-*` attribute | `extract '{"d": {"selector":"[data-items]","attr":"data-items"}}'` |
| 3 | a framework state blob | `extract '{"d": "#__NEXT_DATA__"}'` |
| 4 | an endpoint the page calls | `extract '{"js": ["script"]}'`, then read the URL out of it |
| 5 | the markup itself | `extract` with anchored selectors |

Labs 08 and 10 are step 2 and step 3, and in both the "hard" page — infinite
scroll, hashed class names — turns out to ship its entire dataset as clean JSON
in the first response. Lab 06 is step 4. Lab 03 is the case where you have done
all five and the answer really is "render it."

The reason to look in this order is not elegance. It is that each step up the
list is more stable than the one below: a `<meta itemprop="price">` was put
there for a machine and will not move, a class name belongs to a stylesheet and
the stylesheet gets rewritten.

## 2.2 First contact, in four commands

```bash
h5i browser read https://site.example/list --text | head -60   # what is this page?
h5i browser structured --url https://site.example/list         # does it describe itself?
h5i browser read https://site.example/list --json | python3 -c '…'   # what did it fetch?
h5i browser extract '{"x": ["SELECTOR"]}' --url …              # does my guess match?
```

Four questions in order: what is on the page, what does the page say about
itself, what does the page load, and does my selector find it. Answering them
before writing a loop is twenty seconds against an afternoon.

## 2.3 Find the element that is one row

Everything else follows from this. Look at the markup around a value you can
see on screen and find the smallest element that contains **exactly one
record**: `article.product_pod`, `div.quote`, `tr.team`, `li.product`,
`div.thumbnail`.

Then write every selector inside it. Not because it is tidier, but because
`extract` returns columns and a column is only a table if all the columns have
the same length — and an anchored selector produces exactly one value per row
even when the row is missing the field.

Test it with the count, every time:

```bash
… | python3 -c 'import json,sys; d=json.load(sys.stdin); print({k: len(v) for k,v in d.items()})'
{'title': 20, 'price': 20, 'stock': 20, 'url': 20}
```

Four twenties is a table. Anything else is not, and `lib/rows.py` will refuse
it rather than write a file that is wrong in a way nothing downstream can see.

## 2.4 Prefer identifiers to display text

`Albert Einstein` is what the page renders. `/author/Albert-Einstein` is what
the site routes on. The first changes when a designer decides on
`Einstein, Albert`; the second changes when the site's URLs change, which is a
much rarer and much louder event.

So: keep the href, the slug, the numeric id, the UPC, the SKU. They are the
columns that still join correctly next month, and the columns that let you
deduplicate across runs. Display text is a label, not a key.

## 2.5 Take the stop condition from the site

The three shapes, best first:

| Shape | Example | Why |
| --- | --- | --- |
| a stated total | `"Showing 1–16 of 188 results"`, `"totalCount": 3000` | you can *verify* the crawl, not just end it |
| a next link whose absence is meaningful | `li.next a`, `a.next.page-numbers` | the site asserts there is no more |
| a page count | `"pageCount": 94`, the last pager link | bounded before you start |

And the shape to refuse: **"stop when a page returns fewer rows than the last."**
A page that came back short because it was throttled, because a filter got
mangled, or because an error page was served with a 200, is indistinguishable
from the end of the data. Lab 08 is a scraper whose stop condition was met on
the first iteration and returned three rows out of 117 with no error.

Best practice is both: end on the site's signal, then check the count against
the site's total, and say both numbers when you are done.

## 2.6 A form is a URL, until it is not

Drive the form once. Read what `submit` answers:

```json
{"method": "GET", "url": "https://site.example/search?q=New+York"}
```

A GET form is a URL template with a human wrapper on it. After one submission
you have the template, and every later query is string construction — faster,
reproducible, and immune to the page re-rendering under your @refs.

A POST form is not, and `submit` tells you that too. Then you are either
driving the form each time, or looking for the API the form posts to.

Read the pager the same way, rather than guessing: `page_num`, `page`, `p`,
`offset`, `start`, a cursor token. One `extract` of the pagination links
settles it, and usually hands you the last page number as a bonus.

## 2.7 Interaction is a last resort, and a click is not evidence

When a click, a scroll or a widget seems necessary:

1. Do it once, and read `h5i browser requests` for what it fetched. That URL is
   usually the real target.
2. If it fetched nothing, read the page's own `<script>` for the request it
   *would* have made.
3. Call that directly.
4. Reconsider whether a browser was needed at all.

`{"ok": true}` from a click means the click was dispatched. Whether anything
happened is a separate question with a separate answer in the request log, and
in the reply's own `caused_requests`. Do not retry a click in a loop; look at
what it did.

Engine versions differ in what a click can reach, and
[`05-limits.md`](05-limits.md) is the version-by-version account: jQuery-bound
handlers did not fire at all up to 0.4.1, which made "the click did nothing" the
commonest false conclusion in this course.

## 2.8 Decide what one run costs before you start

Write the number down: pages × requests per page. Then cap it — `PAGES`,
`LIMIT`, `MIN_ROWS` — so the cap is a decision rather than a hope. A crawl on a
site you do not control does not have a natural stopping point; it has a
calendar widget, a session id in a URL parameter, and an infinite supply of
distinct URLs that all render the same page.

Every lab here caps at two or three pages by default and says how to raise it.

## 2.9 When you have it, say what you have

A finished scrape is three numbers and one sentence: rows collected, rows the
site said existed, requests made, and which of the five routes in 2.1 produced
the data. If the first two do not match, that is the finding — not a detail to
fix later.

Next: [`03-cheatsheet.md`](03-cheatsheet.md).
