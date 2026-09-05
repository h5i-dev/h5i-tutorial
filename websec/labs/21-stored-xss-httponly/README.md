# Lab 21 — Board

**Class:** stored XSS against an HttpOnly session · **Difficulty:** ③

A comment board. A moderator reviews it. The moderator's session cookie is
`HttpOnly`, so `document.cookie` will not help you.

    ./run.sh 21     →  http://127.0.0.1:9210

**Goal:** `/admin/api/flag` answers only a moderator session.

**Hint:** you do not need to *read* the moderator's credential. You need to
*act* with it.
