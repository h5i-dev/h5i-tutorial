# Lab 05 — writeup

## What `submit` answers

```json
{"method": "GET", "ok": true, "url": "https://www.scrapethissite.com/pages/forms/?q=New+York"}
```

A `GET` form is a URL template with a human-facing wrapper. Once you have seen
one submission, you have the template, and every later search is a string —
no snapshot, no @ref, no typing, no re-render to lose your place in.

Combine it with the pager, whose links read `?page_num=2&q=New+York`, and the
crawl is:

```bash
for n in 1 2 3; do
    h5i browser extract "$SCHEMA" --url "$TARGET&page_num=$n" --session lab05
done
```

Three requests, no interaction, and it reruns identically tomorrow.

**A `POST` form is not this**, and the difference is worth checking rather than
assuming: `submit` will answer `"method": "POST"`, the URL will not carry your
input, and you are back to driving the form each time — or to the API that
form posts to, if there is one.

## @refs, and why the script does not hard-code one

A snapshot line reads:

```
- textbox "Search for Teams:" [ref=e9]
```

`@e9` is valid for **that reading**. Take another snapshot, and the engine
refuses the old handle rather than resolving it against whatever now sits in
that position — which is the correct behaviour and occasionally an annoying
one. So `scrape.sh` takes the ref out of the snapshot it just took, matching on
`- textbox`, rather than assuming the box is still ninth.

The durable alternative is `find`:

```bash
h5i browser find --role textbox --session lab05
{"count": 1, "matches": [{"name": "Search for Teams:", "role": "textbox", "selector": "#q"}]}
```

It answers with a **CSS selector**, not a ref. `#q` is what to write down if
you are keeping this scraper; a @ref is for the next three commands only.

## Reading the pager instead of guessing at it

`page_num` is not a convention. It is this site's parameter, read off its own
pagination links. Other sites use `page`, `p`, `offset`, `start`, `from`, a
cursor token, or a POST body. Getting it from the markup takes one `extract`:

```bash
h5i browser extract '{"pager": [{"selector": "ul.pagination a", "attr": "href"}]}' --session lab05
```

The same read gives you the last page number, which is a stop condition that
does not depend on noticing an empty result.

## The rows

`tr.team` is one row and every column is anchored to it. The table also has a
header row, which is a `<tr>` without `class="team"` — the reason the selector
is `tr.team td.name` rather than `td.name`, and a reminder that "the table" and
"the data" are not the same set of elements.
