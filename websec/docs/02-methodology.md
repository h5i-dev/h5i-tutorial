# 2. Methodology

Technique is the easy half. What separates someone who finds bugs from someone
who knows about bugs is a **loop they run every time**, and the discipline to
finish the boring part of it.

This chapter is that loop.

---

## 2.1 The shape of an engagement

```
   scope  →  map  →  understand  →  probe  →  confirm  →  chain  →  report
                ↑                                   │
                └──────────  new surface  ───────────┘
```

Most people skip *map* and *understand*, start at *probe*, and spend the
afternoon throwing payloads at the first input they saw. That is why they find
reflected XSS on a marketing page and miss the IDOR in the billing API.

---

## 2.2 Scope, before anything

Write down, in your own file, before the first request:

* which hosts, which ports, which subdomains
* which accounts you were given, and what roles they hold
* what you may **not** do — denial of service, data destruction, social
  engineering, testing on production, touching other tenants' data
* who to contact, and what "stop" looks like
* whether request smuggling (Lab 30) and cache poisoning (Lab 33) are permitted
  at all — both affect other users' traffic

If any of that is unclear, ask before you test, not after. See
[`04-reporting-and-scope.md`](04-reporting-and-scope.md).

---

## 2.3 Map — spend the first hour here

The goal is a list of every place the application accepts input. Not a
vulnerability; a list.

**Use the application like a user, with capture on.** Log in, click everything,
submit every form, upload something, change a setting, cancel an order. The
record builds itself.

```bash
h5i browser open https://target.example/ --session work --new --capture
h5i browser snapshot --session work
h5i browser click @e7 --session work
…
h5i websec sitemap  --session work --human
h5i websec requests --session work --human
```

**Then read the record, not the site.** Applications show a person a fraction of
what they expose. `websec requests` shows the XHR endpoints, the analytics
beacons, the third-party origins, the API version prefixes.

**Then look where the UI does not:**

```
/robots.txt  /sitemap.xml  /.well-known/security.txt  /.well-known/openid-configuration
/.git/HEAD  /.env  /.env.bak  /backup.zip  /server-status  /actuator/env
/swagger.json  /openapi.json  /graphql  /api  /api/v1  /api/v2  /api/v0
```

and inside what you already have: HTML comments, source maps, JavaScript
bundles (grep them for paths, feature flags, and role names), `window.__STATE__`
blobs, error messages, `Server`/`X-Powered-By` headers.

**Write the inventory down** as a table with a row per endpoint and columns for:
method, parameters, what role can reach it, what it returns, whether it changes
state. This table is the engagement. Everything after this is filling it in.

---

## 2.4 Understand — what is this application *for*?

Before probing, be able to answer:

* **Who are the actors?** anonymous, user, admin, support, service, another
  tenant
* **What are the objects?** invoice, document, order, ticket — and how is each
  identified?
* **What are the invariants?** "a coupon is used once", "you cannot spend what
  you do not have", "a user sees only their own tenant's data"
* **What is the money?** where is value created, moved, or destroyed
* **What is the trust boundary?** which requests come from a browser, which from
  a partner, which from an internal service

Every serious finding in Part VII of this book is an invariant somebody stated
in a meeting and never wrote as code. You cannot find those by fuzzing; you find
them by knowing what the feature means.

---

## 2.5 Probe — one variable at a time

For each row of your inventory, run the standard sweeps. Each is one `--set`.

**Identity sweep** — the highest-yield thing in web security:

```
as the owner        →  expected
as another user     →  IDOR (Lab 06/07)
as a lower role     →  privilege escalation (Lab 08)
as nobody           →  missing authentication
```

Do it with `--as` and two logged-in sessions, and build the matrix for **every**
state-changing endpoint, not the interesting-looking ones.

**Object sweep**: change every identifier — increment it, decrement it, use
another tenant's, use one you found in a search result, use `0`, `-1`, `null`,
an array.

**Field sweep**: add fields the endpoint did not ask for (`is_admin`, `role`,
`credits`, `owner_id` — Lab 09); change field *types* (string → object → array →
boolean — Labs 09, 15); remove required fields.

**Shape sweep**: change the method (Lab 04); change `Content-Type` (JSON →
form → XML → multipart, Lab 18); change the path's spelling (case, `//`, `..`,
`%2f`, trailing slash — Lab 04); change the API version (Lab 05).

**Injection sweep**, once, on every parameter, watching status and size:

```
'   "   \   `   ;   |   &   <   >   {{7*7}}   ${7*7}   ../   %00
```

You are not looking for a shell. You are looking for a *response that changes*.
Follow the ones that do.

**Header sweep**: `Host` (Lab 32), `X-Forwarded-Host`, `X-Forwarded-For`,
`Origin` (Lab 23), `Referer`, `User-Agent` (Lab 29), `X-Original-URL`,
`Authorization` from another session.

Read sweeps by **status, size, and time** — three numbers per probe, out of the
replay reply. Never a hundred bodies.

```bash
for v in …; do
  h5i websec replay req_0 --session work --reset-budget --set query.x=$v |
    python3 -c 'import json,sys;r=json.load(sys.stdin);
s=r["response"];print(s["status"], s["bytes"], r["samples"][0]["total_ms"])'
done | sort | uniq -c
```

The outlier is the finding. This one loop finds IDOR, blind SQLi, user
enumeration, mass assignment, and rate-limit gaps.

---

## 2.6 Confirm — make the difference mean something

A changed response is a lead, not a finding. Confirm it three ways:

1. **Isolate the variable.** Replay with only that edit; `diff` against the
   unmodified response. `applied` in the reply proves what changed.
2. **Show the mechanism.** `1=1` and `1=2`; true and false; the payload and its
   neutered twin. A single anomalous response is a coincidence until its
   opposite behaves oppositely.
3. **Reach something.** Read a record you should not be able to read, write a
   value you should not be able to write, print a flag. "The parameter is
   reflected" is not a finding; "an anonymous user can read any customer's
   invoice" is.

And confirm negatives too. Before you write "not vulnerable", check that your
payload actually left: `websec show req_N --raw` (Lab 27 exists entirely because
of this), and `h5i browser requests` for anything the policy refused.

---

## 2.7 Chain — the step people skip

After every finding, ask one question:

> **What does this let me reach that I could not reach before?**

* an open redirect → an OAuth token (Lab 24)
* a file read → a log you can write into → code execution (Lab 29)
* an upload → an allowlist file → an admin role (Lab 28)
* a low-privilege account → an SSRF endpoint → an internal service → its debug
  endpoint → the vault (Lab 42)
* an XSS → not a cookie, but *actions as the victim* (Lab 21)

Written as five findings, Lab 42 is a medium, two lows and an informational.
Written as one chain it is "an anonymous internet user obtains the root
credential in five requests". Same bugs. Different report, different priority,
different afternoon for the team that has to fix it.

---

## 2.8 Habits that compound

**One session per identity, named.** `--session alice`, `--session bob`. Never
mix jars; a contaminated jar produces findings that are not real.

**Never leave the record.** If a probe is worth sending, it is worth being a
replay inside the session, so that the reproduction exists without extra work.

**`--reset-budget` on every loop.** A silent stop halfway through a sweep is
indistinguishable from a clean bill of health.

**Read the whole response, once.** The first time you see an endpoint, read the
entire body and every header. `levels: ["public","internal"]` (Lab 01) and
`method_checked: "GET"` (Lab 04) are the sort of thing that is there, exactly
once, in the response you skimmed.

**Keep a findings file as you go**, one paragraph per lead, with the message ids.
You will not remember on Thursday why `req_118` mattered on Tuesday.

**Timebox rabbit holes.** Twenty minutes on one lead, then back to the
inventory. The inventory is where the next lead is.

---

## 2.9 When you are stuck

In order:

1. Re-read the last response in full.
2. Check that your payload actually went out (`show req_N --raw`).
3. Check the budget and the policy (`h5i browser requests` shows refusals).
4. Ask what the *last* thing you learned was for.
5. Go back to the inventory and pick a row you have not touched.
6. Change the *type* rather than the value. Change the *method* rather than the
   parameter. Change the *actor* rather than the object.
7. Look for the second half of a chain rather than a bigger version of the first.

Next: [`03-cheatsheet.md`](03-cheatsheet.md).
