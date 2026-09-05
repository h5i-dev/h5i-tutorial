# Lab 08 — Ledger

## The bug

```python
user = SESSIONS.get(req.cookies.get("sid", ""))
if not user:
    return js({"error": "sign in"}, 401)
return js({… "audit_key": FLAG})
```

The guard answers *are you signed in*. Nobody asks *are you a manager*. The
missing check is invisible in review because the function does contain a check
— and the UI genuinely does not link interns to the page, which is how the team
convinced itself the control existed.

## The technique: two sessions, one request

This is the single most productive move in authorization testing, and h5i names
it in one flag.

```bash
# alice, the manager
h5i browser open http://127.0.0.1:9080/ --session alice --new --capture
h5i websec replay req_0 --session alice --create --set method=POST --set path=/login \
    --set header.Content-Type=application/json --set json.user=alice

# bob, the intern, in his own session with his own cookie jar
h5i browser open http://127.0.0.1:9080/ --session bob --new --capture
h5i websec replay req_0 --session bob --create --set method=POST --set path=/login \
    --set header.Content-Type=application/json --set json.user=bob

# alice reaches the page: this is the request under test
h5i websec replay req_0 --session alice --create --set path=/api/reports/quarterly

# the whole test
h5i websec replay req_2 --session alice --as bob
```

`--as` takes the *message* from `--session` and the *cookies, identity, policy
and receipts* from the named session. The source session's own `Cookie` and
`Authorization` headers are **dropped**, because carrying them would send a
request that is neither user's and whose answer means nothing.

`--keep-credentials` sends them anyway. Use it only when "does this endpoint
accept a token minted for someone else, over a different transport" is the
actual question.

## The four outcomes, and what each means

| Result | Reading |
| --- | --- |
| 200 with alice's data | broken authorization — the finding |
| 200 with **bob's** data | correct: the endpoint scoped by session, not by URL |
| 401 | the message carried no usable credential; check that bob is logged in |
| 403 | the control works |

That second row is the one people misread. Confirm which body you got before
you write it up.

## The matrix worth running on a real engagement

Two accounts per role, and every interesting request replayed as every other
account:

```
                  as alice(mgr)   as bob(intern)   as nobody
GET /reports/q         200             200 ←            401
POST /users/1/role     200             ?                ?
DELETE /invoice/9      200             ?                ?
```

Automate it once and run it against every endpoint your recon found. Most real
findings are a single cell in this table.

## The fix

```python
if not user:            return js({"error": "sign in"}, 401)
if USERS[user] != "manager":
    return js({"error": "forbidden"}, 403)
```

Better: make the role check a property of the route table rather than a line in
each handler, and default-deny (see Lab 04).

## h5i technique

`--as SESSION` and `--keep-credentials`. Also: named sessions
(`--session alice --new`) are how you hold several identities at once without
one jar contaminating another.
