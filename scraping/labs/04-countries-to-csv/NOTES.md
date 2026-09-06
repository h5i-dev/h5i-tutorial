# Lab 04 — writeup

## The interesting part is the request count

Four columns, 250 rows, one `extract`, one page:

```
# pages fetched: 1, third-party subresources refused: 7
```

The lesson is that you should have known the first number before writing
anything, and that `h5i browser requests` is how you check it afterwards:

```
   200 GET https://www.scrapethissite.com/pages/simple/ (…)
DENIED GET https://fonts.googleapis.com/css?family=Lato:400,700 — origin
       `https://fonts.googleapis.com` is not in the allowlist
```

Two facts in that log, and both matter.

Note that the count is of **navigations**, not of `200`s. A page pulls
stylesheets and images too, and `--json` labels each request with its
initiator so you can tell a page from the things a page dragged in.

**One page produced 250 rows.** A scraper that paginated here would be making
requests for data it already had. Before writing a crawl, read one page and
count what is on it: the commonest waste in scraping is a loop around a page
that never needed one.

**The webfont was refused, and the extract worked anyway.** A session grants
itself the origin of the URL you opened and nothing else. Every third-party
subresource — fonts, analytics, CDN scripts — is denied and written to the log
with the reason. For a scraper this is mostly free: you did not want the font,
and not fetching it is faster and quieter than fetching it.

It stops being free the moment the denied thing is a script the page needs.
That is Lab 06, and the reason to get used to reading this log now, while the
denials are harmless, is so that you recognise the shape when they are not.

## The columns are text, and text is not a number

```
Andorra,Andorra la Vella,84000,468.0
```

`84000` and `468.0` are strings that look like numbers, and `extract` does not
convert them, because it cannot know that a page rendering `1,234` means 1234
and a page rendering `1.234` might mean either. Convert at the point where you
know the site's convention, and record which convention you assumed.

Trimming, on the other hand, has happened: the markup is

```html
<span class="country-population">
    84000
</span>
```

and the answer is `84000`. Leading and trailing whitespace is stripped from
text reads. Internal whitespace is not collapsed, so a two-line address still
arrives with its newline in it.
