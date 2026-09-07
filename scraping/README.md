# Web scraping

A hands-on course in scraping, built around
[h5i](https://github.com/h5i-dev/h5i)'s browser: an engine that **is** the HTTP
client, so the log of what a scrape fetched — and what it was refused — is
written before the bytes move rather than reconstructed afterwards.

> One of the two courses in this repository. The other is
> [`../websec/`](../websec/), which uses the same engine to bend requests
> rather than to read pages. Neither assumes the other.

Ten labs, ten sites, each site published by its operator **so that people would
scrape it**. Every lab is a brief, a scraper that really runs, and a writeup
about the one thing that site teaches. Everything below is run from this
directory:

```bash
cd scraping

./run.sh                 # list the labs
./run.sh 01              # run lab 01, write out/01-books-to-scrape.csv
./run.sh 01 -            # run it, print the CSV instead
PAGES=10 ./run.sh 02     # take more of the site
PACE=3 ./run.sh 09       # go slower
./test-all.sh            # all ten, about thirty requests
cat labs/01-*/README.md  # the brief
cat labs/01-*/NOTES.md   # the writeup
```

Python's standard library and one binary. No Docker, no accounts, no keys.

---

## 1. Setup

You need **Python 3.11+** and **h5i**. The verbs this course uses are in the
base binary; there is no plugin to install.

```bash
curl -fsSL https://h5i.dev/install.sh | sh
h5i browser --help
```

Building from source instead:

```bash
git clone https://github.com/h5i-dev/h5i && cd h5i
cargo build --release --workspace
```

If h5i is not on your `PATH`, point the scripts at it:

```bash
export H5I=~/src/h5i/target/release/h5i
./test-all.sh
```

Check it works:

```bash
./run.sh 01 - | head -3
title,price,stock,url
A Light in the Attic,£51.77,In stock,https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
```

**This course needs the network**, unlike the one next door. Its ten targets are
public practice sites, and a lab can fail because a site redesigned, went down,
or throttled you — `test-all.sh` says which lab and what it got, and deciding
which of those happened is yours.

Written and verified against **h5i 0.3.9**, and re-run end to end against the
engine as it stands after **0.4.1**. All ten labs produce the same rows on
both. What changed between them is five of the six limits this course reported,
so [`docs/05-limits.md`](docs/05-limits.md) now says, version by version, which
answer to expect from your own build.

---

## 2. How to use this book

**Read `docs/` first.** Five short chapters, and they are the part that makes
the labs mean something:

| | |
| --- | --- |
| [`docs/01-the-reader.md`](docs/01-the-reader.md) | the tool: `read` vs `open`, the four reads, the extract schema in full, the request log |
| [`docs/02-method.md`](docs/02-method.md) | how to approach a site you have never scraped |
| [`docs/03-cheatsheet.md`](docs/03-cheatsheet.md) | one page: every verb, every schema form, every place data hides |
| [`docs/04-etiquette-and-scope.md`](docs/04-etiquette-and-scope.md) | rate, robots, terms, personal data — and why these ten sites |
| [`docs/05-limits.md`](docs/05-limits.md) | where this engine is thinner than a browser, which limits were fixed, and the reproductions for both |

**Then work the labs in order.** Each assumes the last. Give the brief a real
attempt before opening `NOTES.md`; unlike the websec course, the writeup here
is the teaching rather than a spoiler, but it lands better after you have been
stuck.

**The argument the whole course is making**, stated once so you can watch it
recur: *find the data before you write a selector.* Selectors are step four of
five, and on four of these ten sites the "hard" page turns out to ship its
entire dataset as clean JSON in the first response.

---

## 3. The curriculum

### Part I — Reading one page

| # | Lab | Site | Teaches | ★ |
| --- | --- | --- | --- | --- |
| 01 | [Books to Scrape](labs/01-books-to-scrape) | [books.toscrape.com](https://books.toscrape.com/) | one page to CSV; anchoring selectors to a row | ① |
| 02 | [Quotes to Scrape](labs/02-quotes-pagination) | [quotes.toscrape.com](https://quotes.toscrape.com/) | a field that repeats, and the three ways out | ① |
| 03 | [Quotes, JavaScript](labs/03-quotes-javascript) | [quotes.toscrape.com/js](https://quotes.toscrape.com/js/) | `--script`, what it costs, and when not to | ② |

### Part II — Pages that are really URLs

| # | Lab | Site | Teaches | ★ |
| --- | --- | --- | --- | --- |
| 04 | [Countries](labs/04-countries-to-csv) | [scrapethissite.com](https://www.scrapethissite.com/pages/simple/) | 250 rows in one request; counting what you fetched | ① |
| 05 | [Hockey Teams](labs/05-hockey-forms) | [scrapethissite.com](https://www.scrapethissite.com/pages/forms/) | a form is a URL; `@ref` vs a durable selector | ② |
| 06 | [Oscar Winning Films](labs/06-oscars-ajax) | [scrapethissite.com](https://www.scrapethissite.com/pages/ajax-javascript/) | the request under the click, when the click is dead | ③ |

### Part III — Crawls, and knowing when they finished

| # | Lab | Site | Teaches | ★ |
| --- | --- | --- | --- | --- |
| 07 | [E-commerce catalogue](labs/07-ecommerce-catalogue) | [webscraper.io](https://webscraper.io/test-sites) | a crawl whose shape comes from the site | ② |
| 08 | [Infinite scroll](labs/08-infinite-scroll) | [webscraper.io](https://webscraper.io/test-sites) | the stop condition that lies; `data-*` payloads | ③ |
| 09 | [ScrapingCourse shop](labs/09-scrapingcourse-shop) | [scrapingcourse.com](https://www.scrapingcourse.com/) | verifying a crawl against the site's own total | ② |

### Part IV — Stop writing selectors

| # | Lab | Site | Teaches | ★ |
| --- | --- | --- | --- | --- |
| 10 | [Oxylabs sandbox](labs/10-oxylabs-next-data) | [sandbox.oxylabs.io](https://sandbox.oxylabs.io/) | `#__NEXT_DATA__`, and the order to look in | ③ |

---

## 4. What each lab contains

```
labs/01-books-to-scrape/
  README.md    the brief — the site, why it is fair game, the goal, one hint
  scrape.sh    a scraper that really runs, commented where it is doing something
  NOTES.md     the writeup — what the page does, what breaks, the general rule
```

`lib/` holds the two shared pieces: `rows.py`, which turns `extract`'s columns
into CSV and **refuses** when they do not line up, and `h5i.sh`, which opens a
session, closes it however the script ends, and paces every request.

Output goes to `out/`, which is not tracked.

---

## 5. Scope

Every target here is a site whose operator published it to be scraped, and
[`docs/04-etiquette-and-scope.md`](docs/04-etiquette-and-scope.md) quotes each
one saying so. Each lab fetches two or three pages, a second apart, and says how
to raise that.

None of it transfers automatically to a site that did not say so. What transfers
is the method — and the habit of knowing, and being able to state, exactly what
your scraper fetched.

Apache-2.0, like h5i.
