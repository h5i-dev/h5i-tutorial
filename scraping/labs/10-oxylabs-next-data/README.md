# Lab 10 — Oxylabs sandbox

**Site:** [sandbox.oxylabs.io/products](https://sandbox.oxylabs.io/products) · **Skill:** stop writing selectors · **★** ③

Oxylabs publish this as a
[scraping sandbox](https://sandbox.oxylabs.io/) — a fake video-game shop with
categories, pagination and dynamic content, built for practice.

It is a Next.js application, and its class names look like this:

```html
<div class="product-card css-e8at8d eag3qlw10">
```

`css-e8at8d` is a hash of the stylesheet rule. It changes when anyone edits the
CSS. A scraper written against it breaks on a deploy that changed nothing you
were reading.

There is a much better target on the same page, and the last lab of this course
is about looking for it **first** rather than after the selectors break.

**Goal:** the products with their scores, platforms and genres, as CSV, plus
the page and product totals the site states.

**Start here**

```bash
h5i browser open https://sandbox.oxylabs.io/products --session lab10 --new
h5i browser extract '{"class": {"selector": "div.product-card", "attr": "class"}}' --session lab10
h5i browser extract '{"blob": "#__NEXT_DATA__"}' --session lab10 | head -c 400
```

**Hint:** the second answer is not markup, and it has fields in it the page
never renders.

Then: [`NOTES.md`](NOTES.md).
