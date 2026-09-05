# Lab 07 — E-commerce catalogue

**Site:** [webscraper.io/test-sites/e-commerce/allinone](https://webscraper.io/test-sites/e-commerce/allinone) · **Skill:** a crawl with a shape · **★** ②

Web Scraper's public test site, and the page says what it is: *"This site was
created for testing purposes. You may use this site for training to learn how
to use the Web Scraper. Items listed here are not for sale."* It is listed
among [their test sites](https://webscraper.io/test-sites) for exactly this.

Two levels of category, then products. Nothing here is hard; the point is that
the crawl's **shape** comes from the site rather than from a list of URLs you
typed. A hard-coded list is a scraper that silently stops covering a site the
week somebody adds a category.

**Goal:** name, price, description, review count and URL, from the leaf
categories, as one CSV.

**Start here**

```bash
h5i browser open https://webscraper.io/test-sites/e-commerce/allinone --session lab07 --new
h5i browser extract '{"cat": [{"selector": "a.category-link", "attr": "href"}]}' --session lab07
h5i browser extract '{"sub": [{"selector": "a.subcategory-link", "attr": "href"}]}' --session lab07
```

**Hint:** the second one returns an empty column, and it is not a wrong
selector.

Then: [`NOTES.md`](NOTES.md).
