# 5. Where the reader ends

A page that comes back empty in h5i is not necessarily an empty page, and a
scraper that cannot tell those apart will eventually report the wrong thing
confidently. This chapter is what this course found while building ten labs
against **h5i 0.3.9**, each item reduced to the smallest reproduction that
still shows it.

---

## 5.1 `extract` returns columns, not rows

This is a design property rather than a defect, and it is the one that costs
people data.

Every key in the schema is matched against the whole document independently.
There is no way to say "for each product card, read these four things." So a
schema returns a set of flat lists, and turning them into records means zipping
them, and a zip of unequal lists is silently wrong rather than an error.

```bash
# 20 titles, 19 prices — one card has no price
{"title": [...20...], "price": [...19...]}
```

**Mitigation.** Anchor every selector at the row container, so a row missing
the field still contributes an empty value:

```json
"price": ["article.product_pod p.price_color"]
```

Then check the lengths before writing anything. `lib/rows.py` refuses unequal
columns and prints them.

**Where anchoring is not enough:** a genuinely one-to-many field, like a
quote's tags. The flat list has discarded which parent each match came from,
and no schema recovers it. Lab 02's three routes: find where the page already
joined them (a `<meta itemprop="keywords">`), read the rows one at a time, or
take each row's `outerHTML` and parse inside it.

## 5.2 An attribute read inside an array comes back wrapped

```json
"links": [{"selector": "h3 a", "attr": "href"}]
→ [{"href": "https://…"}, {"href": "https://…"}]

"next": {"selector": "li.next a", "attr": "href"}
→ "https://…"
```

The scalar form gives you the value; the array form gives you a list of
one-key objects. Consistent once you know, surprising the first time, and
`lib/rows.py` unwraps it.

## 5.3 jQuery 1.x does not initialise

The sharpest limit in this course, and the reason Lab 06 is shaped the way it
is. On a page that loads jQuery 1.11.3 — even from an allowed origin, even with
a clean `200` in the request log:

```
$ h5i browser read http://localhost/page --script --json
console:     [{"level": "error", "text":
  "jquery.min.js: TypeError: cannot convert 'null' or 'undefined' to object (jquery.min.js:2:212)"}]
unsupported: [{"api": "Element.attachEvent", "calls": 1}]
text:        "jQuery UNDEFINED"
```

jQuery 1.x feature-detects the IE-era `Element.attachEvent`, which this engine
does not implement, and throws before it finishes defining `$`. Everything the
page would have bound inside `$(document).ready` is therefore never bound, and
a click on such a page dispatches onto an element listening to nothing.

**Confirmed working** on the same engine, by reducing each to a minimal page:

| | |
| --- | --- |
| inline `<script>` that mutates the DOM | runs |
| `addEventListener('click', …)`, and `click` dispatching to it | runs |
| `DOMContentLoaded` | fires |
| `window` `load` | fires |
| `setTimeout` | fires |
| a cross-origin `<script src>` from an `--allow`ed origin | fetched **and executed** |

So "JavaScript does not work here" is the wrong summary. Ordinary page script
works. One widely-deployed library does not, and it takes every page written
against it with it.

**What to do.** Read `console` and `unsupported` from `h5i browser read URL
--script --json` before concluding anything about a page that seems inert. They
name the failing script and the missing API. Then use Lab 06's route: find the
request the page would have made, in its own `<script>` source, and make it
yourself.

## 5.4 Scroll-driven loading does not fire

```
# rendered before scrolling: 3
# after a scroll: 3
# after a scroll: 3
```

`h5i browser scroll` moves the page, and on the sites here it did not cause any
lazy-loader to fetch more. `wait-for` is unusually informative about why:

```
not found after 0ms, and the only work left on this page is 2 self-rescheduling
timer(s) — an animation or polling loop, which will not converge no matter how
long you wait
```

**Why this is more than an h5i problem.** A scroll loop's termination condition
— *stop when a scroll adds nothing* — cannot distinguish "reached the end" from
"the mechanism never ran". It is met immediately here, and it is met just as
silently on a real browser whose viewport is too short to trigger an
intersection observer, or whose fifth page was rate-limited.

**What to do.** Look for the data in the first response before automating the
gesture. Lab 08's page carries all 117 products in a `data-items` attribute:
the scroll was a rendering decision over data that had already arrived.

## 5.5 A session grants one origin

Everything except the URL's own origin is refused, and written to the log with
its reason:

```
DENIED GET https://ajax.googleapis.com/… — origin `https://ajax.googleapis.com`
       is not in the allowlist
```

Usually a gift — you did not want the analytics beacon, and not fetching it is
faster. Occasionally the whole problem, when the denied thing is the library the
page is written in. `--allow ORIGIN` at open time, repeatable.

**`read` has no `--allow`.** Naming the URL is what grants it, and nothing else
is reachable. When a page needs a third-party script, it needs `open --allow`,
or a box with an allowlist in `.h5i/env.toml`.

## 5.6 The verb surface is narrower than the shipped skill describes

`h5i skill show browser` documents `click --role button --name 'Sign in'`. On
0.3.9:

```
$ h5i browser click --role link --name 2015
error: unexpected argument '--role' found
```

`click` and `type` take a `@ref` only. `find`, `select` and `set-checked` do
take `--role` / `--selector` / `--name`. `h5i <command> --help` is the
authoritative list and cannot go stale; the skill text can.

Note also that `find` answers with a **CSS selector**, not a `@ref`:

```json
{"count": 1, "matches": [{"role": "textbox", "name": "Search for Teams:", "selector": "#q"}]}
```

That is the better artefact anyway — a `@ref` is valid only for the snapshot it
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
expected, what happened, and what it cost you. §5.3 and §5.4 are this chapter's
own two, found that way.

Back to [`../README.md`](../README.md).
