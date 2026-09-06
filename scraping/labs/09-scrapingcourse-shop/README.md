# Lab 09 — ScrapingCourse shop

**Site:** [scrapingcourse.com/ecommerce](https://www.scrapingcourse.com/ecommerce/) · **Skill:** knowing when you are finished · **★** ②

A WooCommerce storefront published by
[ScrapingCourse](https://www.scrapingcourse.com/) as a demo to learn scraping
against — their front page lists this shop alongside a "Load More" page, an
infinite-scroll page, and a demo login, each built to practise one mechanism.

Ordinary markup, ordinary pagination, 188 products across twelve pages. The
lab is not the extraction. It is the two numbers you should be able to state
when the crawl finishes: how many rows you got, and how many there were.

**Goal:** a CSV of the first two pages, and a count checked against the site's
own total.

**Start here**

```bash
h5i browser open https://www.scrapingcourse.com/ecommerce/ --session lab09 --new
h5i browser extract '{"count": "p.woocommerce-result-count"}' --session lab09
h5i browser extract '{"name": ["li.product .product-name"]}' --session lab09
```

**Hint:** the first of those is worth more than the second.

Then: [`NOTES.md`](NOTES.md).
