# Lab 07 — writeup

## The empty column, again

`a.subcategory-link` matches nothing on the front page because subcategories
are only rendered once you are inside a category. The crawl is therefore two
reads deep before it sees a product, and discovering that costs one extract.

This is the ordinary case, not a trick. **Read the navigation before writing
the loop**, and let the depth of the loop come from what you found rather than
from what you assumed the site looked like.

## The price is not in the price element

```html
<h4 class="price float-end card-title" itemprop="offers" itemscope>
    <span itemprop="price">$1347.78</span>
    <meta itemprop="priceCurrency" content="USD">
</h4>
```

Reading `h4.price` gives you the text of everything inside it. Reading
`h4.price span[itemprop=price]` gives you the price. On this page the
difference happens to be invisible — a `<meta>` contributes no text — but the
habit generalises to the `<h4>` that also contains a strikethrough old price, a
"was" label, or a per-unit note, and those are the ones that quietly corrupt a
price column.

The microdata attributes are the tell. `itemprop="price"` and
`itemprop="reviewCount"` were put there for machines by somebody who wanted the
data read correctly. **When a page carries schema.org markup, use it**: it is
more stable than a class name, because a class name belongs to the stylesheet
and the stylesheet gets rewritten.

## Review counts

```html
<p class="review-count float-end"><span itemprop="reviewCount">11</span> reviews</p>
```

`p.review-count` gives `11 reviews`; the span gives `11`. Take the number.
Parsing `"11 reviews"` later means writing a regex for a string whose format
belongs to a site you do not control, and which is `1 review` in the singular.

## Cost, and the cap

`LIMIT` defaults to two leaf categories: four requests total. `LIMIT=6
./run.sh 07` covers the site. A crawl on a site you do not control should have
a cap you set on purpose and can raise, rather than a natural stopping point
you hope exists — the natural stopping point is what a crawl that has found a
calendar widget or a session-id URL parameter does not have.
