# Lab 06 — Oscar Winning Films

**Site:** [scrapethissite.com/pages/ajax-javascript](https://www.scrapethissite.com/pages/ajax-javascript/) · **Skill:** the request under the click · **★** ③

Scrape This Site's AJAX lesson. Six year links; clicking one fetches that
year's films and draws them into a table, with a deliberate 1.5-second delay so
you can watch it happen. The site's own brief is the answer key: *"browse
through your network tab to see those AJAX requests and scrape them."*

Two things go wrong here, in a useful order.

The first is a **denied origin**: the page loads jQuery from
`ajax.googleapis.com`, which the session does not grant itself, so nothing runs
and the page looks like a page with no data. The fix is `--allow`.

The second depends on which h5i you have, and the lab is built around it either
way. Up to 0.4.1, with `--allow` in place, jQuery is fetched, 200, and then
**throws while initialising itself**, so `$` is never defined and not one of the
page's handlers is ever bound: the click dispatches onto an element listening to
nothing. After 0.4.1 jQuery runs, the click reaches the handler, and the year's
films arrive. See
[`../../docs/05-limits.md`](../../docs/05-limits.md#53-jquery-1x).

Run it and find out which one you are holding, because that is the real skill
here: *"the interaction did not work" is a claim about your tool as much as
about the site*, and the request log settles it in one read.

**Goal:** a year of films as CSV, and a clear account of which step produced
them.

**Start here**

```bash
h5i browser open https://www.scrapethissite.com/pages/ajax-javascript/ \
    --session lab06 --new --script
h5i browser snapshot --session lab06 | grep 2015
h5i browser click @e9 --session lab06
h5i browser wait-for --selector tr.film --session lab06
h5i browser requests --session lab06          # ← the lab is in here
```

**Hint:** when a click produces nothing, the question is not "what else can I
click". It is "what request was that click supposed to make", and the page's
own source says. When the click *does* work, ask the same question anyway: the
answer is one request instead of a rendered page, and `h5i browser requests`
hands it to you.

Then: [`NOTES.md`](NOTES.md).
