# Lab 33 — Newsroom

**Class:** web cache poisoning · **Difficulty:** ④

A news site behind a cache. An editor — signed in, `HttpOnly` cookie — reloads
the homepage every couple of seconds.

    ./run.sh 33     →  http://127.0.0.1:9330   (origin behind it on :9331)

**Goal:** `/admin/flag` answers only an editor session.

**What you have:** `/collect?id=&c=` and `/collected?id=` on the same origin.

**Hint:** you are not looking for an input that changes the response. You are
looking for one that changes the response **and not the cache key**.
