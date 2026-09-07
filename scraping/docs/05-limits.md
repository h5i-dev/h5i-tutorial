# 5. Where the reader ends

A page that comes back empty in h5i is not necessarily an empty page, and a
scraper that cannot tell those apart will eventually report the wrong thing
confidently. This chapter is what this course found while building ten labs
against **h5i 0.3.9**, each item reduced to the smallest reproduction that
still shows it.

Six of those reproductions were filed. Five are now fixed, which is the reason
this chapter is written the way it is: **a limit is a fact about a version, not
about a tool.** Every section below says what the engine did, where that
stands, and what the reproduction is, so you can find out in one command which
of the two you are holding.

| | Was | Now |
| --- | --- | --- |
| [5.1](#51-extract-returns-columns-not-rows) | `extract` had no notion of a row | fixed in 0.4: a `fields` spec reads one object per match |
| [5.2](#52-an-attribute-read-inside-an-array) | an array of attribute reads came back wrapped | fixed after 0.4.1: a flat list of values |
| [5.3](#53-jquery-1x) | jQuery 1.x threw before defining `$` | fixed after 0.4.1 |
| [5.4](#54-scroll-driven-loading) | `scroll` moved the page and told it nothing | fixed after 0.4.1 |
| [5.5](#55-a-session-grants-one-origin) | `read` had no `--allow` | fixed after 0.4.1 |
| [5.6](#56-the-verb-surface) | `click` took a `@ref` and nothing else | fixed in 0.4.1: `--role`, `--name`, `--selector` |
| [5.7](#57-what-this-engine-is-not-for) | what the engine is not for | unchanged, and not a defect |

"After 0.4.1" means merged into h5i's `main` and shipping in the next release
([h5i#619](https://github.com/h5i-dev/h5i/pull/619)). `h5i --version` tells you
which side of that you are on, and every section carries a probe that tells you
the same thing by behaviour.

---

## 5.1 `extract` returns columns, not rows

Every key in the schema is matched against the whole document independently, so
a flat schema returns a set of flat lists. Turning those into records means
zipping them, and a zip of unequal lists is silently wrong rather than an error.

```bash
# 20 titles, 19 prices. One card has no price.
{"title": [...20...], "price": [...19...]}
```

**Fixed in 0.4.** A spec with `fields` reads one object per match, with every
sub-selector scoped to that match, which is the row grouping this section was
written to say the engine lacked:

```bash
h5i browser extract '{"rows": [{"selector": "article.product_pod", "fields": {
    "title": "h3 a", "price": "p.price_color"}}]}' --session s
```

A row that is missing the field contributes `null` and keeps its place, so
there is nothing to zip and nothing to misalign.

**The old advice still applies to a flat schema**, because a flat schema is
still the shortest thing to type and still the thing that breaks: anchor every
selector at the row container, and check the lengths before writing anything.
`lib/rows.py` refuses unequal columns and prints them.

**Where neither helps:** a genuinely one-to-many field, like a quote's tags. One
row holds several, so no row-shaped answer flattens it for you. Lab 02's three
routes stand: find where the page already joined them (a `<meta
itemprop="keywords">`), read the rows one at a time, or take each row's
`outerHTML` and parse inside it.

## 5.2 An attribute read inside an array

```json
"links": [{"selector": "h3 a", "attr": "href"}]
```

On 0.4.1 that answers `[{"href": "…"}, {"href": "…"}]`: a list of one-key
objects, where the scalar form of the same spec answers a bare string.

**Fixed after 0.4.1.** The array form now differs from the scalar form in arity
and in nothing else, so the same schema answers `["https://…", "https://…"]`. A
match without the attribute keeps its place as `null`, so the list still lines
up with a sibling column read over the same selector.

`lib/rows.py` unwraps a one-key object and passes a string through, so the labs
in this course produce the same CSV on either version. Your own code may not:
if you wrote `row["href"]`, that is the line to look at.

## 5.3 jQuery 1.x

The sharpest limit this course found, and the reason Lab 06 is shaped the way
it is. On 0.4.1, a page that loads jQuery 1.11.3 from an allowed origin, with a
clean `200` in the request log:

```
$ h5i browser read http://localhost/page --script --json
console:     [{"level": "error", "text":
  "jquery.min.js: TypeError: cannot convert 'null' or 'undefined' to object (jquery.min.js:2:212)"}]
text:        "jQuery UNDEFINED"
```

**Fixed after 0.4.1**, and the diagnosis is worth reading even now, because it
is what this kind of failure looks like from the outside. jQuery's support
probe asks `"onsubmit" in window`, which was false because the engine's window
carried only the window-specific handler properties. The false answer sent
jQuery down its Internet-Explorer branch, which reads
`div.attributes["onsubmit"].expando`, and the engine's `NamedNodeMap` had no
named lookup, so the read was `undefined` and the property access threw. The
library never finished defining `$`, so nothing inside `$(document).ready` was
ever bound, and a click on such a page dispatched onto an element listening to
nothing. Two missing pieces of ordinary DOM, and the visible symptom was one of
the most widely deployed libraries on the web being absent.

The probe, on the version you have:

```bash
h5i browser read 'https://www.scrapethissite.com/pages/ajax-javascript/' \
  --script --allow https://ajax.googleapis.com --json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["snapshot"]["notes"])'
```

**Confirmed working** on both versions, by reducing each to a minimal page:

| | |
| --- | --- |
| inline `<script>` that mutates the DOM | runs |
| `addEventListener('click', …)`, and `click` dispatching to it | runs |
| `DOMContentLoaded`, `window` `load`, `setTimeout` | fire |
| a cross-origin `<script src>` from an `--allow`ed origin | fetched **and executed** |

So "JavaScript does not work here" was the wrong summary then and is the wrong
summary now. **What to do when a page seems inert** has not changed: read
`console` and `unsupported` from `h5i browser read URL --script --json` before
concluding anything. They name the failing script and the missing API, and that
is the difference between an hour and a week.

**Two more, found by re-running this chapter against the fixed engine.** With
jQuery alive, Lab 06's click reaches the handler and the handler fires its
request, and the films still did not appear. Following the link's `href="#"`
*refetched the page*, throwing away the table the handler had just drawn, and a
handler calling `preventDefault()` was overridden the same way. So the click
worked and the page did not keep it, which reads from outside exactly like the
dead click above and is a completely different fault.

The reproduction is three lines of HTML: an `<a href="#">` whose handler appends
a node, clicked once. Both are fixed in h5i's `fix-scripted-clicks`, later than
the five fixes above, so an engine can have jQuery working and this still
pending. Lab 06's writeup has the three-way table that tells them apart.

## 5.4 Scroll-driven loading

On 0.4.1:

```
# rendered before scrolling: 3
# after a scroll: 3
# after a scroll: 3
```

`h5i browser scroll` moved the viewport and dispatched nothing, so a page whose
lazy-loader listens for the `scroll` event never heard the gesture.

**Fixed after 0.4.1.** A scroll now fires the page's own `scroll` handlers and
re-checks its intersection observers at the new offset, so an infinite-scroll
page loads as you go:

```bash
h5i browser open https://webscraper.io/test-sites/e-commerce/scroll/computers/laptops \
    --session s --new --script
h5i browser extract '{"n": ["div.thumbnail a.title"]}' --session s   # 3
h5i browser scroll 4000 --session s
h5i browser extract '{"n": ["div.thumbnail a.title"]}' --session s   # 6
```

**The lesson this section was written for survives the fix, and Lab 08 is
still the lab it was.** Three points, in order of how much they cost:

*The stop condition still cannot tell "reached the end" from "the mechanism
never ran".* It was met immediately on 0.4.1; it is met just as silently on any
browser whose viewport is too short to trigger an observer, or whose fifth page
was rate-limited. A loop that stops when a scroll adds nothing is guessing.

*The gesture is expensive.* That page renders three more products per scroll,
so reaching all 117 is about 39 round trips through the verb layer.

*And the request log says they bought nothing.* `caused_requests` is empty on
every one of those scrolls, because all 117 products were in the first response
all along, in a `data-items` attribute. Look for the data in the first response
before automating the gesture: that is Lab 08, and the fix to the scroll verb
makes the point sharper rather than retiring it.

## 5.5 A session grants one origin

Everything except the URL's own origin is refused, and written to the log with
its reason:

```
DENIED GET https://ajax.googleapis.com/… — origin `https://ajax.googleapis.com`
       is not in the allowlist
```

Usually a gift: you did not want the analytics beacon, and not fetching it is
faster. Occasionally the whole problem, when the denied thing is the library the
page is written in. `--allow ORIGIN` at open time, repeatable.

**`read --allow` was added after 0.4.1.** Naming the URL still grants its
origin, which is the whole allowlist for most reads. When it is not, the flag is
now there rather than forcing a session:

```bash
h5i browser read 'https://www.scrapethissite.com/pages/ajax-javascript/' \
    --script --allow https://ajax.googleapis.com --text
```

Inside a box it can only narrow: the box's own egress list is enforced outside
the engine, and a flag cannot widen it.

## 5.6 The verb surface

On 0.3.9, `click` and `type` took a `@ref` and refused a locator, while the
shipped skill documented `click --role button --name 'Sign in'`.

**Fixed in 0.4.1.** `click`, `type` and `submit` take `--role`/`--name` or
`--selector`, the same locators `find`, `select` and `set-checked` take.
`h5i <command> --help` is still the authoritative list and still cannot go
stale, which is the durable half of this section.

`find` answers with a **CSS selector**, not a `@ref`:

```json
{"count": 1, "matches": [{"role": "textbox", "name": "Search for Teams:", "selector": "#q"}]}
```

That is the better artefact anyway: a `@ref` is valid only for the snapshot it
came from, and a selector survives.

## 5.7 What this engine is not for

| Situation | Reach for |
| --- | --- |
| a heavy SPA that will not render | Chromium in an h5i box (`agent-browser`), or Playwright |
| a page whose data only exists after a real interaction | the same |
| tens of thousands of pages | a crawler framework with a scheduler and a store |
| a site that offers an API or a dump | the API or the dump |
| a site that has told you to stop | nothing. See [`04-etiquette-and-scope.md`](04-etiquette-and-scope.md) |

The strength of this engine for scraping is not coverage. It is that the
request log is written before the bytes move, so every question of the form
"what did my scraper actually fetch, and what was refused" has an exact answer.
For a job whose commonest failure is *quietly collecting less than you think*,
that is the property worth having.

## 5.8 If you find a limit this chapter does not list

Reduce it to the smallest page that still shows it, capture `console` and
`unsupported` from `h5i browser read … --script --json`, and say what you
expected, what happened, and what it cost you.

That is not a formality here. §5.3 and §5.4 were this chapter's own two, found
that way, filed with those reproductions, and fixed in the engine within the
week. The two click bugs at the end of §5.3 were found by re-running the same
reproductions against the fixed engine, which is the other half of the habit:
**a limit that goes away deserves the same reduction as a limit that appears.**

Back to [`../README.md`](../README.md).
