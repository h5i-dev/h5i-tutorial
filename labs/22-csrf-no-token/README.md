# Lab 22 — Prefs

**Class:** cross-site request forgery · **Difficulty:** ③

`POST /account/recovery-email` changes where a password reset is sent. It
requires the moderator's session cookie. You do not have it and cannot read it.

    ./run.sh 22     →  http://127.0.0.1:9220   (and a second origin on :9221)

**Goal:** point the moderator's recovery address at `attacker@evil.example`,
then read `/account/reset`.

**What you have:** `POST /report {"url"}` — a moderator opens any link.
`POST /page {"name","html"}` — publishes a page on a *different origin*,
port 9221.

**Hint:** you never need to see the cookie. You need the moderator's browser to
send it.
