# Lab 04 — Countries

**Site:** [scrapethissite.com/pages/simple](https://www.scrapethissite.com/pages/simple/) · **Skill:** the whole dataset, one request · **★** ①

The first page of [Scrape This Site](https://www.scrapethissite.com/pages/),
Hartley Brody's public sandbox — a set of pages built to be scraped, each with
a named lesson attached to it. This one is the plain case: 250 countries, no
pagination, no script, all in one document.

**Goal:** country, capital, population and area, as 250 CSV rows — and a check
that you fetched exactly one page to get them.

**Start here**

```bash
h5i browser open https://www.scrapethissite.com/pages/simple/ --session lab04 --new
h5i browser extract '{"country": ["h3.country-name"]}' --session lab04
h5i browser requests --session lab04
```

**Hint:** the answer to "how many pages should this take" is available before
you write the loop. There is no loop.

Then: [`NOTES.md`](NOTES.md).
