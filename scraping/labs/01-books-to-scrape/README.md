# Lab 01 — Books to Scrape

**Site:** [books.toscrape.com](https://books.toscrape.com/) · **Skill:** one page to CSV · **★** ①

A fictional bookshop with a thousand books, put online by the makers of
[Scraping Hub's tutorial series](https://toscrape.com/) as a place to practise.
Its front page says so: *"This is a demo website for web scraping purposes.
Prices and ratings here were randomly assigned and have no real meaning."*

Nothing on it needs JavaScript. Every book is an `article.product_pod` with a
title, a price, a stock line and a link, and the pagination is an ordinary
`<a href>`. It is the shortest possible route from a URL to a CSV file, which
is why it is first.

**Goal:** a CSV of title, price, stock and URL, covering the first two list
pages, plus one detail page read to see what the list leaves out.

**Start here**

```bash
h5i browser open https://books.toscrape.com/ --session lab01 --new
h5i browser markdown --session lab01 | head -40
h5i browser extract '{"title": ["h3 a"]}' --session lab01
```

**Hint:** `["h3 a"]` gets you twenty truncated titles — `A Light in the ...`.
The untruncated one is somewhere else on the same element.

Then: [`NOTES.md`](NOTES.md).
