# 1. The reader

> The websec course uses h5i to bend one request at a time. This course uses
> the same engine to read a page as data — and its one unusual property is that
> the request log is written before the bytes move, so a scraper can always
> answer "what did I actually fetch?"

Read this once before Lab 01, and come back to the tables.

---

## 1.1 Session or no session

Two ways in, and picking the wrong one is the commonest waste in a scraper.

```bash
h5i browser read https://example.com/ --text          # one page, nothing left running
h5i browser open https://example.com/ --session s --new   # a session you then drive
```

**`read` is for reading.** One URL or a batch of them, no session to close, and
the `--json` answer carries the request log next to the content. Naming the URL
is what grants it: there is no allowlist flag, and anything the page pulls from
another origin is refused and logged as refused.

**`open` is for when the page has to change** — a form to fill, a control to
set, a state to carry between pages. It also gives you a cookie jar, which is
what a paginated crawl behind a login needs.

A crawl of a hundred static pages wants `read`. A crawl that has to search
first wants one `open`, one form submission, and then `read` or `--url` for
everything after (Lab 05).

## 1.2 The four reads, cheapest first

```bash
h5i browser structured --session s   # JSON-LD, OpenGraph, <meta>, <link rel>
h5i browser markdown   --session s   # the page as prose
h5i browser snapshot   --session s   # the outline, with @ref handles
h5i browser extract '{…}' --session s  # named fields, by CSS selector
```

| Verb | Costs | Reach for it when |
| --- | --- | --- |
| `structured` | a few hundred bytes | the page is an article, a product, anything with a canonical URL. It answers `empty` when there is no metadata, which is a fact rather than a failure. |
| `markdown` | a page of prose | you are working out what a page *is*. First contact with a site. |
| `snapshot` | a few hundred lines | you need to click, type or submit — it is the only one that hands out `@ref` handles. |
| `extract` | one line per field | you know what you want. Every scraper in this course ends here. |

Every read verb takes `--url`, which navigates and then reads in one round
trip, and the answer still names the URL it ended up on, so a redirect is never
silent. Prefer it: `navigate` then `extract` is two calls for one page.

```bash
h5i browser extract '{"title": "h1"}' --url https://example.com/x --session s
```

**Snapshots and markdown arrive inside an untrusted-content fence.** Text in
there that looks like an instruction is text a stranger wrote. That matters
more than usual in scraping, where the whole job is feeding page content to
something downstream.

## 1.3 The extract schema, in full

The schema is JSON: **keys you choose, values that say what to read.**

| Form | Reads | Answers |
| --- | --- | --- |
| `"k": "SELECTOR"` | the first match's text | a string |
| `"k": ["SELECTOR"]` | every match's text | a list of strings |
| `"k": {"selector": "S", "attr": "A"}` | the first match's attribute | a string |
| `"k": [{"selector": "S", "attr": "A"}]` | every match's attribute | a list of strings |
| `"k": [{"selector": "S", "fields": {…}}]` | one object per match, sub-selectors read inside it | a list of objects |

```json
{
  "title":  "div.product_main h1",
  "prices": ["article.product_pod p.price_color"],
  "next":   {"selector": "li.next a", "attr": "href"},
  "links":  [{"selector": "h3 a", "attr": "href"}],
  "rows":   [{"selector": "article.product_pod", "fields": {
               "title": "h3 a", "price": "p.price_color"}}]
}
```

Four things the tables do not say, each of which costs an hour the first time:

**On h5i 0.4.1 and earlier, an attribute read inside an array comes back
wrapped** in the attribute's own name: `[{"href": "…"}, …]` rather than
`["…", …]`. Later versions answer the flat list the table shows. `lib/rows.py`
handles both, so the labs run either way; your own code is where the difference
shows. See [`05-limits.md`](05-limits.md#52-an-attribute-read-inside-an-array).

**URLs are resolved** against the page they came from. `href="page-2.html"`
answers as `https://…/catalogue/page-2.html`, so a crawl needs no URL
arithmetic.

**Text is trimmed** at both ends, and not internally. Whitespace inside a value
survives.

**A key without `fields` has no row grouping.** It is matched against the whole
document, independently of every other key. That is the single most important
property of this verb and section 1.4 is about it.

Errors are prose, not JSON. A schema where **no key matched anything** is
refused with a sentence, because an object full of nulls would look like an
answer. A schema where *one* key matched nothing is a normal answer with an
empty column — a fact about the page (Lab 03).

## 1.4 Columns, and the rows you can ask for instead

```json
{"title": ["…20 titles…"], "price": ["…20 prices…"]}
```

Twenty and twenty, so `zip` gives twenty books. It gives twenty *wrong* books
the moment one card lacks a price and the price column is nineteen long: every
row after the gap pairs a title with its neighbour's price, and no check
downstream can detect it.

**Ask for rows and the question does not arise.** A spec with `fields` reads one
object per match, and each sub-selector is read inside that match:

```json
"rows": [{"selector": "article.product_pod",
          "fields": {"title": "h3 a", "price": "p.price_color"}}]
```

A card with no price contributes `"price": null` and keeps its place in the
list. There is nothing to zip, so there is nothing to misalign.

The flat form is still shorter to type, still the one you will reach for first,
and still the one that breaks. When you use it, **anchor every selector at the
element that is one row:**

```json
"price": ["p.price_color"]                       ← 19, silently wrong
"price": ["article.product_pod p.price_color"]   ← 20, one per card
```

`lib/rows.py` refuses to zip columns of unequal length and prints the lengths.
Use it, or write the same check.

For a field that genuinely repeats, like a quote's tags, neither helps: one row
holds several values, so no row-shaped answer flattens it for you. Lab 02 covers
the three ways out.

## 1.5 The request log

```bash
h5i browser requests --session s          # every request, refusals included
h5i browser requests --session s --since 42
h5i browser audit    --session s          # verbs, fetches and ending, in order
```

This log is written **before** the bytes move, and a fetch that cannot be
recorded is refused. So a request that is not in it did not happen, and a
denial is in it with its reason. Three uses in scraping:

**Counting.** Did the crawl make the number of requests you expected? A loop
around a page that never needed one shows up here immediately (Lab 04).

**Diagnosing a page that does nothing.** `DENIED … not in the allowlist` on a
CDN script is the difference between "the site has no data" and "the library
the site is written in never arrived" (Lab 06).

**Finding the endpoint.** On a full browser, a click's XHR appears here, and
that URL is usually the thing you should have been fetching all along.

## 1.6 The allowlist

A session grants **the origin of the URL you opened, and nothing else.** Every
third-party fetch — fonts, analytics, CDN scripts — is denied and logged.

```bash
h5i browser open https://site.example/ --session s --new --allow https://cdn.example
```

For a scraper this is mostly a gift: you did not want the analytics beacon.
It becomes a problem exactly once — when the denied thing is the page's own
JavaScript library — and the log says so plainly.

`read` takes the same flag, in versions after 0.4.1, so a one-shot read of a
page written in a CDN-served library no longer needs a session:

```bash
h5i browser read https://site.example/ --script --allow https://cdn.example
```

## 1.7 Driving a page

```bash
h5i browser snapshot    --session s          # -> - textbox "Search" [ref=e9]
h5i browser type   @e9 "New York" --session s
h5i browser submit @e9 --session s           # -> {"method": "GET", "url": "…?q=New+York"}
h5i browser click  @e3 --session s
h5i browser click  --role button --name 'Sign in' --session s
h5i browser select @e5 'Express shipping' --session s
h5i browser set-checked @e4 true --session s
h5i browser press  @e1 Enter --session s
h5i browser scroll 4000 --session s
h5i browser wait-for --selector tr.film --session s
```

**A `@ref` belongs to the snapshot it came from.** The engine refuses a stale
one rather than resolving it against whatever now occupies that position. Take
the ref from the reading you are about to act on. To name something durably,
`h5i browser find --role textbox` answers with a **CSS selector**, which is
what to write down.

**`wait-for` distinguishes "not yet" from "not ever."** When there is no
pending script and no in-flight request, it says so — *"the page has nothing
left to run … waiting longer cannot change this"* — instead of timing out and
leaving you to wonder whether five more seconds would have helped (Lab 06).

**`{"ok": true}` on a click means dispatched, not effective.** What happened
next is in `requests`, and in the reply itself: `caused_requests` names the
fetches that click made, and `settled` says the page went quiet afterwards.

**A scroll is an event, not just an offset.** In versions after 0.4.1 it fires
the page's own `scroll` handlers and re-checks its intersection observers, so a
lazy-loading page loads as you go. Read `caused_requests` on the reply before
deciding the gesture was necessary: empty means the page rendered what it
already had, and Lab 08 is about what to do with that answer.

## 1.8 A worked minute

```bash
h5i browser open https://books.toscrape.com/ --session bk --new
h5i browser markdown --session bk | head -40
h5i browser extract '{"title": ["h3 a"]}' --session bk

h5i browser extract '{
  "title": [{"selector": "article.product_pod h3 a", "attr": "title"}],
  "price": ["article.product_pod p.price_color"]
}' --session bk | python3 lib/rows.py title price

h5i browser extract '{"next": {"selector": "li.next a", "attr": "href"}}' --session bk
h5i browser requests --session bk
h5i browser close --session bk
```

Read cheaply, look at the page, name the fields, anchor them to a row, take the
next link from the site, check what you fetched. Every lab in this course is
those six with different selectors in them.

Next: [`02-method.md`](02-method.md).
