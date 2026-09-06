# Lab 06 — writeup

## Failure one: the allowlist

```
DENIED GET https://ajax.googleapis.com/ajax/libs/jquery/1.11.3/jquery.min.js
       — origin `https://ajax.googleapis.com` is not in the allowlist
```

A session grants the origin of the URL you opened, and nothing else. In Lab 04
that cost a webfont, which nobody wanted. Here it costs the library the entire
page is written in, and the symptom is not an error — it is a page that renders
its year links and then does nothing when you use them.

```bash
h5i browser open … --script --allow https://ajax.googleapis.com
```

**This is the first thing to check whenever a page behaves as though it has no
behaviour.** The request log names the refusal and its reason, and it is
written before the bytes move, so a request that is not in the log did not
happen. There is no ambiguity to reason around: read it.

## Failure two: the click, which stays broken

With jQuery loaded, the click is still a no-op:

```
$ h5i browser click @e9 --session lab06
{"ok": true, "url": "https://www.scrapethissite.com/pages/ajax-javascript/#"}

$ h5i browser wait-for --selector tr.film --session lab06
not found, and the page has nothing left to run after 0ms — waiting longer cannot change this
```

Read that `wait-for` answer closely, because it is doing something unusual and
valuable. It distinguishes **"not yet"** from **"not ever"**: there is no
pending script and no in-flight request, so no amount of waiting will change
the page. A timeout would have left you wondering whether five more seconds
would have done it. This says they would not.

`{"ok": true}` on the click means the click was dispatched, not that anything
happened as a result. Here nothing was listening. jQuery arrives — the log says
`200 GET …/jquery.min.js` — and then throws while initialising itself:

```
TypeError: cannot convert 'null' or 'undefined' to object (jquery.min.js:2:212)
unsupported: [{"api": "Element.attachEvent", "calls": 1}]
```

jQuery 1.11.3 feature-detects the IE-era `Element.attachEvent`, this engine does
not have it, and the library never finishes defining `$`. Every handler the
page would have bound inside `$(document).ready` was therefore never bound, and
the same goes for the `#2015` hash entry point.

This is worth separating from "the click does not work." Ordinary handlers do
work here — `addEventListener`, `DOMContentLoaded`, `window.onload`,
`setTimeout` all fire. What failed is one library, on one page, for a stated
reason. `h5i browser read URL --script --json` prints that reason in its
`console` and `unsupported` fields, and it is the first thing to read when a
page is inert.

So the click is not available here. Do not retry it, and do not conclude the
site has no data.

## Finding the request that was supposed to happen

The handler is in the page's markup, and markup is something you can read
without executing anything:

```bash
h5i browser extract '{"js": ["script"]}' --session lab06
```

```js
$.ajax({
    method: "GET",
    url: document.location.pathname,
    data: { ajax: true, year: year },
    success: function(data){ setTimeout(function(){ showFilms(data); }, 1500); }
});
```

That is the whole answer:

```
GET https://www.scrapethissite.com/pages/ajax-javascript/?ajax=true&year=2015
```

It returns JSON — typed numbers, a `best_picture` boolean, no markup to parse —
needs no `--script`, and costs one request per year.

```bash
h5i browser read 'https://www.scrapethissite.com/pages/ajax-javascript/?ajax=true&year=2015' --text
```

`read` is the right verb here: one page, no session left behind, and naming the
URL is what grants it.

## The point

The endpoint is the better target **even on a browser where the click works**.
It is fewer requests, no rendering, no 1.5-second artificial delay, no
dependence on a third-party CDN, and it returns data that is already typed.
Driving the UI to produce data the server was willing to hand over directly is
the most common way a scraper ends up slow and fragile at the same time.

The general move, in order:

| | |
| --- | --- |
| 1 | Click it once, and read `h5i browser requests` for what the click fetched. |
| 2 | If nothing was fetched, read the page's `<script>` for the URL it would have fetched. |
| 3 | Call that URL directly, and check the shape of what comes back. |
| 4 | Only then consider whether you needed a browser at all. |

Step 1 is the one that works on a full browser and tells you the answer in five
seconds. Step 2 is what this lab needed, and it is also what you need on any
page whose interaction you cannot reproduce — a hover, a drag, a widget behind
a login you would rather not automate.

## Where this stops being reasonable

An endpoint you found in a page's source is still the site's endpoint, subject
to the same terms as the page. Finding it does not make it public and does not
raise your rate limit. This one belongs to a site that published a lesson
telling you to find it, which is not the general case.
[`../../docs/04-etiquette-and-scope.md`](../../docs/04-etiquette-and-scope.md)
applies exactly as much to a JSON endpoint as to an HTML page.
