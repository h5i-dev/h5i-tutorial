# Lab 24 — SSO

**Class:** OAuth `redirect_uri` validation · **Difficulty:** ④

An authorization server. The `notes` client is registered with exactly one
redirect URI, and the server checks it.

    ./run.sh 24     →  http://127.0.0.1:9240   (your page host is :9241)

**Goal:** obtain a signed-in user's access token and read `/api/profile`.

**What you have:** `POST /report {"url"}` (a signed-in user opens it),
`POST /page {"name","html"}` → served on :9241, and `/collect` / `/collected`.

**Hint:** read the validation as a *string operation*, not as a rule.
