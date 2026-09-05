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

The second does not have a fix. With `--allow` in place jQuery is fetched, 200,
and then **throws while initialising itself**, so `$` is never defined and not
one of the page's handlers is ever bound — see
[`../../docs/05-limits.md`](../../docs/05-limits.md). The click dispatches onto
an element that is listening to nothing. The lab is built around that, because
"the interaction did not work" is a situation every scraper meets and the
response to it is a skill.

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
own source says.

Then: [`NOTES.md`](NOTES.md).
