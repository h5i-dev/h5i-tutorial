# Lab 23 — Partner API

**Class:** CORS misconfiguration · **Difficulty:** ③

`GET /api/me` returns the signed-in user's API key. It is meant to be readable
cross-origin by the company's own front end, and only by that.

    ./run.sh 23     →  http://127.0.0.1:9230   (your page host is :9231)

**Goal:** read a signed-in user's `api_key` from a page on another origin.

**What you have:** `POST /page {"name","html"}` publishes a page on
`http://127.0.0.1:9231`; `POST /report {"url"}` gets a signed-in user to open
it; `/collect?id=&c=` and `/collected?id=` are your drop.

**Hint:** an origin is three things, and the check reads only one of them.
