# 4. Etiquette and scope

Every target in this course is a site whose operator published it **so that
people would scrape it**. That is not a technicality; it is the reason a
tutorial can print real commands against real hosts without asking anyone for
permission first. Nothing here transfers automatically to a site that did not
say so.

---

## 4.1 The ten, and what each one says about itself

| # | Site | What the operator says |
| --- | --- | --- |
| 1 | [books.toscrape.com](https://books.toscrape.com/) | "a demo website for web scraping purposes"; prices and ratings are random |
| 2 | [quotes.toscrape.com](https://quotes.toscrape.com/) | the same sandbox, published at [toscrape.com](https://toscrape.com/) |
| 3 | [quotes.toscrape.com/js](https://quotes.toscrape.com/js/) | the same sandbox's JavaScript exercise |
| 4 | [scrapethissite.com/pages/simple](https://www.scrapethissite.com/pages/simple/) | "a public sandbox for learning web scraping", with a lesson per page |
| 5 | [scrapethissite.com/pages/forms](https://www.scrapethissite.com/pages/forms/) | same, the forms and pagination lesson |
| 6 | [scrapethissite.com/pages/ajax-javascript](https://www.scrapethissite.com/pages/ajax-javascript/) | same, and the page tells you to go find its AJAX requests |
| 7 | [webscraper.io/test-sites/e-commerce](https://webscraper.io/test-sites) | "created for testing purposes … items listed here are not for sale" |
| 8 | [webscraper.io/test-sites/e-commerce/scroll](https://webscraper.io/test-sites) | same, listed among their official test sites |
| 9 | [scrapingcourse.com](https://www.scrapingcourse.com/) | demo sites published to learn scraping against |
| 10 | [sandbox.oxylabs.io](https://sandbox.oxylabs.io/) | published by Oxylabs as a scraping sandbox |

Every lab here fetches **two or three pages**, paced a second apart, and says
how to raise that. Thirty-odd requests for the whole course. Even on sites that
invite scraping, a tutorial that ships an unpaced thousand-page crawl teaches
the wrong reflex on the first day.

## 4.2 Before pointing this at anything else

Four questions, in order, and the first is the one people skip.

**Is there an API?** A documented endpoint with a rate limit and a stable
schema beats the best scraper anybody has ever written. Look before you build.
Several of the sites in this course have one — `quotes.toscrape.com/api/quotes`
is right there — and Lab 06 is about an undocumented one being better than the
UI it backs.

**What do the terms say?** Read them. "Publicly reachable" is a fact about a
server's configuration, not a grant of permission, and the two are not related.
Where the terms prohibit automated collection, that is the answer.

**What does `robots.txt` say?** It is a convention, not a law, and it is also
the operator telling you plainly which paths they do not want crawled. Honour
it. When you have a reason not to, that reason should be one you would be
willing to state to the operator.

**What is the smallest thing that answers the question?** Most scraping tasks
need a hundred rows and get pointed at a hundred thousand. Fetching what you
need is the single most effective courtesy available, and it is also faster.

## 4.3 Rate, and the reason it is not about robots.txt

A scraper's request rate is the part of it that other people experience. Every
lab in this course sleeps a second between requests, through one variable:

```bash
PACE=3 ./run.sh 09
```

One second is a floor for a sandbox that exists to be hit. On a site that does
not, think in terms of what a human doing the same task would generate, and
stay under it. Concurrency multiplies your rate; running ten workers at one
request a second is ten requests a second, whatever the sleep in each of them
says.

Signals to stop, not to work around:

* `429`, or a `Retry-After` header
* `403` appearing after a run that worked
* a CAPTCHA, or an interstitial
* response times climbing while you run

Each of those is a site telling you it does not want this traffic. Rotating an
address, forging a user agent, or solving the interstitial is not troubleshooting
— it is proceeding after being told no, and the answer stays no.

`--identity` exists so a session can present a coherent browser identity, not
so it can pretend to be a person. If a scrape only works while the site cannot
tell it is a scrape, that is a finding about whether to run it.

## 4.4 What you collect is a separate question

Being in a response is not permission to keep, and permission to keep is not
permission to publish. Lab 10's state blob carries fields the page never
renders; the fact that a server sent them says nothing about what may be done
with them.

Three things that change the answer regardless of how the data was obtained:

* **Personal data.** Names, emails, avatars, reviews attached to accounts.
  Collecting these puts you under data-protection law — GDPR, CCPA, and their
  equivalents — with obligations that begin at collection and do not care that
  the page was public.
* **Copyrighted content.** Article text, images, and descriptions are somebody's
  work. Extracting facts is one thing; republishing prose is another.
* **Aggregation.** Fields that are individually harmless can identify a person
  once joined. The dataset you build is a new thing, and it is yours to answer
  for.

The practical rule: **collect the narrowest set of fields that answers your
question, and be able to say why each column is there.** A column you cannot
justify is a column to drop before it becomes a file on a disk somewhere.

## 4.5 Load-bearing courtesies

* **Identify yourself** where the tool lets you, and give a way to be contacted.
  An operator who can email you will usually email you before blocking you.
* **Cache while developing.** Iterating on a selector should re-read a local
  file, not the site. `h5i browser read ./saved.html` reads a local file with
  the same verbs.
* **Do not scrape what you were given.** If the site offers a CSV, a dump, or a
  feed, take it.
* **Run at a sensible hour** when the site is small and its operator is a person.
* **Stop when something breaks.** A scraper that keeps retrying through errors
  is generating load that helps nobody, including you.

## 4.6 Where this course ends and the other one begins

The websec course next door attacks applications, and every one of its targets
runs on `127.0.0.1` and ships in this repository. That is a deliberate line: the
techniques there are for systems you own or have written authorisation to test.

This course does the opposite — it touches real hosts, and therefore only
touches hosts that asked for it. The rule that connects the two is the same
rule: **the target's consent is what makes the difference, and it is your job
to know you have it.**

Next: [`05-limits.md`](05-limits.md).
