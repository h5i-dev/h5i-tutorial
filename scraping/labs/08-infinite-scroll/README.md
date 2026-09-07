# Lab 08 — Infinite scroll

**Site:** [webscraper.io/test-sites/e-commerce/scroll](https://webscraper.io/test-sites/e-commerce/scroll/computers/laptops) · **Skill:** the stop condition that lies · **★** ③

The same catalogue as Lab 07, rendered as an infinite scroll. Also from Web
Scraper's [test sites](https://webscraper.io/test-sites), and carrying the same
notice: it exists to be practised on, and nothing is for sale.

The obvious scraper is: scroll, count, scroll again, stop when the count stops
growing. Write it, and watch what your engine does with it.

Up to h5i 0.4.1 it stops on the first comparison and returns three rows out of a
hundred and seventeen, with no error and no warning, because "nothing new
loaded" and "nothing can load" are the same observation from inside that loop.
After 0.4.1 the scroll fires the page's own handler and the loop grows, three
products at a time, for as long as you keep scrolling.

Then find where the hundred and seventeen actually were, and count what the
scrolling cost you to see them.

**Goal:** every laptop, and an understanding of why the scroll loop was never
going to get them.

**Start here**

```bash
h5i browser open https://webscraper.io/test-sites/e-commerce/scroll/computers/laptops \
    --session lab08 --new --script
h5i browser extract '{"n": ["div.thumbnail a.title"]}' --session lab08
h5i browser scroll 4000 --session lab08
h5i browser extract '{"n": ["div.thumbnail a.title"]}' --session lab08
```

**Hint:** the page knows how many products it has. Look at the attributes on
the element that wraps them, not at the elements inside it.

Then: [`NOTES.md`](NOTES.md).
