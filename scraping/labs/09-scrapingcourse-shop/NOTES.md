# Lab 09 — writeup

## "Showing 1–16 of 188 results"

```json
{"count": "Showing 1–16 of 188 results"}
```

That sentence is a scraper's best friend and it is on more sites than people
notice: a result count, a "page 3 of 12", a `rel="last"` link, an `X-Total-Count`
header. It gives you the one thing a crawl cannot derive from its own progress —
**what finished looks like**.

With it, the end of a run has a verdict:

```
# the page says there are 188 products in all
# collected 32 of 188 (PAGES=2 of the crawl)
```

Without it, the end of a run has an anecdote: the loop stopped. Lab 08 is what
that costs.

## Two stop conditions, and only one of them is safe

```json
"next": {"selector": "a.next.page-numbers", "attr": "href"}
```

Absent on the last page, present on every other. Stopping on its absence is
safe because the signal comes from the site.

Stopping on **"this page returned fewer rows than the last"** is not. A page
that came back short because a request was throttled, or because a filter in
the URL got mangled, or because the site briefly served an error page with a
200, looks identical. The rule: a stop condition should be something the site
asserted, never something you inferred from a count.

Combining both — stop when `next` is gone, then check the total — catches the
third case too, where `next` kept pointing at pages but they stopped containing
products.

## Selectors on a WordPress theme

```html
<h2 class="product-name woocommerce-loop-product__title">Abominable Hoodie</h2>
```

Two class names on one element: `product-name`, which this demo added, and
`woocommerce-loop-product__title`, which the theme generates. Prefer the one
that describes the **content**, not the one that describes the theme's block
structure — the theme is the part that gets replaced.

`li.product` is the row container, and it is where every selector in this lab
starts. `.product-name` alone would also match a product name in a "recently
viewed" sidebar, and on the day the site adds one, the name column and the
price column stop having the same length. `lib/rows.py` would refuse to write
the file, which is the intended outcome.

## Cost

`PAGES` defaults to 2, which is 32 of 188 products in three requests.
`PAGES=12 ./run.sh 09` takes the shop. Twelve requests a second apart on a site
that exists to be scraped is unremarkable; the same twelve against a real shop's
search results, unpaced, is what gets a scraper blocked.
