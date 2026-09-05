# Lab 02 — Quotes to Scrape

**Site:** [quotes.toscrape.com](https://quotes.toscrape.com/) · **Skill:** a field that repeats · **★** ①

The other half of the [toscrape.com](https://toscrape.com/) sandbox: quotes,
authors, and tags. Same publisher, same invitation, no JavaScript.

It looks like Lab 01 with different nouns, and it is not. A book has exactly
one price. A quote has **zero or more tags**, and a column of tags therefore
has a different length from the column of quotes on it. That is the first thing
`extract` cannot do for you, and the shape of the fix is worth more than the
data.

**Goal:** a CSV of quote, author, author-page URL, and tags, across two pages,
where the tags on each line are that quote's tags.

**Start here**

```bash
h5i browser open https://quotes.toscrape.com/ --session lab02 --new
h5i browser extract '{"quote": ["span.text"], "tags": ["div.tags a.tag"]}' --session lab02
```

**Hint:** count what comes back. Ten and thirty do not zip. Look at what else
is inside `div.tags` — the page already joined them for a machine to read.

Then: [`NOTES.md`](NOTES.md).
