# Lab 01 — writeup

## The truncated title

`["h3 a"]` reads the link's **text**, and the site truncates that for layout:

```
"A Light in the ...",  "Sapiens: A Brief History ...",  "Scott Pilgrim's Precious Little ..."
```

The whole title is in the `title` attribute of the same element, which is
common enough to be the first thing to check when text looks cut off:

```json
"title": [{"selector": "article.product_pod h3 a", "attr": "title"}]
```

An object spec `{"selector": ..., "attr": ...}` reads an attribute instead of
text. Inside an array it comes back wrapped in the attribute's own name —
`[{"title": "A Light in the Attic"}, …]` — because a list of attribute reads is
a list of one-key objects. `lib/rows.py` unwraps them.

## Why every selector starts with `article.product_pod`

`extract` matches each key against the whole document, independently. It has no
notion of a row: what comes back is a set of columns, and turning columns into
rows means zipping them, and zipping is correct only while they are the same
length.

`["p.price_color"]` and `["article.product_pod p.price_color"]` return the same
twenty values on this page. They stop being the same the moment the page grows
a price outside a product card — a "from £10" banner, a related-items strip —
and then the price column is twenty-one long and every book from that point on
is priced as its neighbour. Nothing downstream can see it. The CSV looks fine.

So: **anchor every selector at the element that is one row.** `rows.py` refuses
to zip columns of different lengths for the same reason, and prints the lengths
rather than a table.

## The link is already absolute

`{"attr": "href"}` returns
`https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html`,
not `catalogue/a-light-in-the-attic_1000/index.html`. The engine resolves it
against the page it came from, so a crawl never has to do URL arithmetic. The
same is true of `li.next a`, which is why the pagination loop is three lines
and has no string concatenation in it.

The stop condition is the **absence** of `li.next a` on the last page. That is
the right shape for a stop condition: it comes from the site, and it cannot be
confused with a page that came back short because a request failed.

## What the list page does not have

The detail page carries the UPC, the exact stock count (`In stock (22
available)` rather than `In stock`), the category, and a description. The rating
is the same on both, and on neither is it text — it is a class name:

```html
<p class="star-rating Three">
```

Reading `{"selector": "p.star-rating", "attr": "class"}` gives you
`"star-rating Three"`, and the word after the space is the rating. A value
hidden in a class name is worth knowing about; it turns up wherever a designer
used CSS to draw something a number would have described.

## Cost

Two list pages and one detail page: three requests for forty books plus one
book in full. If you wanted all thousand, that is fifty list pages —
`PAGES=50 ./run.sh 01`, and at the default one-second pace it takes a minute.
There is no reason to go faster on a site that exists to be practised on, and
less reason on one that does not.

## The general technique

1. Read the page cheaply first (`markdown`, `structured`) to see what is there.
2. Find the element that is **one row**.
3. Write every selector inside it.
4. Take the stop condition from the site, never from a row count.
5. Check the column lengths before you write the file.
