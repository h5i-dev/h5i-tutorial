# Lab 03 — Quotes to Scrape, JavaScript

**Site:** [quotes.toscrape.com/js/](https://quotes.toscrape.com/js/) · **Skill:** `--script`, and when not to · **★** ②

The publisher's own JavaScript exercise: the same hundred quotes as Lab 02,
served by a page whose HTML contains none of them. They are written into the
DOM on load by an inline `<script>` holding a `data` array.

h5i runs page JavaScript only when you ask, with `--script`. Off is the
default, and the reason is not performance: **a page that runs no script has no
channel through which to deliver a prompt injection.** Turning it on is a
decision about a specific page, which is what this lab is for.

**Goal:** the same read, twice — once with script off, once on — and a CSV from
the second.

**Start here**

```bash
h5i browser open https://quotes.toscrape.com/js/ --session lab03 --new
h5i browser extract '{"quote": ["span.text"]}' --session lab03      # look at this answer

h5i browser close --session lab03
h5i browser open https://quotes.toscrape.com/js/ --session lab03 --new --script
h5i browser extract '{"quote": ["span.text"]}' --session lab03
```

**Hint:** the first answer is not an error and not a broken selector. Decide
what it *is* before you turn anything on.

Then: [`NOTES.md`](NOTES.md).
