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

## Failure two: the click, on the engine you happen to have

Up to h5i 0.4.1, with jQuery loaded, the click is a no-op:

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
happened as a result. There, nothing was listening. jQuery arrived, the log says
`200 GET …/jquery.min.js`, and then it threw while initialising itself:

```
TypeError: cannot convert 'null' or 'undefined' to object (jquery.min.js:2:212)
```

jQuery 1.11.3 probes two pieces of ordinary DOM that engine did not have, and
never finished defining `$`. Every handler the page would have bound inside
`$(document).ready` was therefore never bound, and the same went for the `#2015`
hash entry point. Both pieces were added after 0.4.1
([`../../docs/05-limits.md`](../../docs/05-limits.md#53-jquery-1x)).

**Run it and read the number the scraper prints.** `films after the click` is
the whole diagnosis, and there are three answers:

| `films after the click` | What your engine did |
| --- | --- |
| 0, and no `?ajax=true` in `requests` | jQuery never initialised. 0.4.1 and earlier |
| 0, but `?ajax=true&year=2015` **is** in `requests` | the handler ran and fetched, and then following the link's `href="#"` reloaded the page over the table it had just drawn |
| 16 | jQuery ran, the click was handled, and the reload no longer happens |

The middle row is the one worth staring at, because the request log and the page
disagree: something was fetched and nothing is on screen. That is always a
rendering or navigation question, never a "the site has no data" question. It is
fixed in h5i by treating `href="#"` as the same-document move it is, and by
honouring the handler's `preventDefault()`.

On an engine with all of it, the same three commands read:

```
$ h5i browser click --role link --name 2015 --session lab06 --json
{"ok": true, "ref": "the link named \"2015\"",
 "url": "https://www.scrapethissite.com/pages/ajax-javascript/",
 "settled": "settled after 1500ms",
 "caused_requests": [{"url": "…/pages/ajax-javascript/?ajax=true&year=2015", "seq": 19}],
 "default_prevented": true}

$ h5i browser wait-for --selector tr.film --session lab06
found after 0ms
```

Three things in that reply are worth naming. `caused_requests` is the URL this
lab exists to find, handed over by the click itself. `default_prevented` says
the page's own handler took the click, which is why the link's `href` was not
followed. And `settled after 1500ms` is the site's deliberate delay, spent on a
virtual clock, so it cost you nothing in real time.

Either way the lesson is the same, and it is worth separating from "the click
does not work". Ordinary handlers worked on both engines: `addEventListener`,
`DOMContentLoaded`, `window.onload`, `setTimeout` all fire. What failed was one
library, on one page, for a stated reason. `h5i browser read URL --script
--json` prints that reason in its `console` and `unsupported` fields, and it is
the first thing to read when a page is inert.

So: do not retry a dead click in a loop, and do not conclude the site has no
data. Find out which of the three rows above you are in, then take the endpoint
anyway.

## Finding the request without running anything

The handler is in the page's markup, and markup is something you can read
without executing anything. This is the route that works on every engine, on a
page whose interaction you cannot reproduce, and on a page you would rather not
execute at all:

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
| 1 | Click it once, and read `caused_requests` on the reply, or `h5i browser requests`, for what the click fetched. |
| 2 | If nothing was fetched, read the page's `<script>` for the URL it would have fetched. |
| 3 | Call that URL directly, and check the shape of what comes back. |
| 4 | Only then consider whether you needed a browser at all. |

Step 1 answers in five seconds wherever the click works. Step 2 is what this lab
needed on 0.4.1, and it is what you need on any page whose interaction you
cannot reproduce: a hover, a drag, a widget behind a login you would rather not
automate. Knowing both is the point; one of them is always available.

## Where this stops being reasonable

An endpoint you found in a page's source is still the site's endpoint, subject
to the same terms as the page. Finding it does not make it public and does not
raise your rate limit. This one belongs to a site that published a lesson
telling you to find it, which is not the general case.
[`../../docs/04-etiquette-and-scope.md`](../../docs/04-etiquette-and-scope.md)
applies exactly as much to a JSON endpoint as to an HTML page.
