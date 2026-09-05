# Lab 39 — Twostep

## The bug

```python
SESSIONS[token] = {"user": user, "mfa": False}    # login
…
session["mfa"] = True                             # after the code
…
def vault(req):
    session = SESSIONS.get(…)
    if not session: return 401
    return js({"vault": FLAG})                    # `mfa` is never read
```

One token, issued before the second factor, carrying a flag that exactly one
function ever sets and no function ever checks. The "temporary" token is a
session, and the second step is a formality it politely performs.

## Finding it

The whole test is: **stop after step one and try everything.**

```bash
TOKEN=$(h5i websec replay req_0 --session lab39 --create \
    --set method=POST --set path=/api/login --set header.Content-Type=application/json \
    --set json.user=dana --set json.password=correct-horse | …token…)

h5i websec replay req_0 --session lab39 --create --set path=/api/vault \
    --set "header.Authorization=Bearer $TOKEN"
```

A two-step flow gives you a partial credential in your hand. Take it to every
endpoint you know about, not just the one the UI would take you to next.

## The rest of the MFA checklist

Run all of these; each is a different bug and each is common:

| Test | What it finds |
| --- | --- |
| use the step-one token everywhere | this lab |
| brute-force the code | no rate limit on 10^6 (or 10^4) possibilities |
| re-use a code | codes not invalidated after use |
| use another user's code | code not bound to the account |
| change the `user` field on the verify request | verify step trusts a client-supplied identity |
| tamper with the response (`{"ok":false}` → `true`) | a *client-side* MFA decision |
| skip to `/mfa/complete` or an enrolment endpoint | a state machine that trusts step order |
| enrol a new factor with the step-one token | takeover without ever passing MFA |
| use a password-reset or "remember me" flow | a second path in with no MFA |
| use an older API version, or the mobile endpoint | MFA added to one surface (Lab 05) |
| replay the token after logout | no invalidation |

The "tamper with the response" line deserves a note: where the client decides,
`h5i websec replay --no-follow` and reading the 302/JSON shows you what the
client was told, and the finding is that changing it changes the outcome. Where
the *server* decides, that test does nothing — which is how you tell the two
apart.

## The fix

Make the pre-MFA credential a different kind of thing:

```python
PENDING[temp] = {"user": user, "expires": now + 300}   # a different store
# nothing but /api/mfa accepts a `temp`
# only /api/mfa mints a real session, after the code verifies
```

A separate, short-lived, single-purpose token — not a session with a boolean on
it. Bind the code to that token, make it single-use, rate-limit and lock out,
and require the full second factor for enrolling *new* factors and for password
reset. Where a boolean on the session is unavoidable, check it in one
middleware that every authenticated route passes through (Lab 04), not in each
handler.

## h5i technique

Nothing new — and that is the lesson. The most valuable authentication bugs need
no clever payload, only the discipline to stop halfway through a flow and try
the next request anyway.
