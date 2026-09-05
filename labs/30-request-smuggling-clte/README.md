# Lab 30 — Frontdoor

**Class:** HTTP request smuggling (CL.TE desync) · **Difficulty:** ⑤

An edge proxy on 9300 forwards to a backend on 9301 over a reused connection.
The proxy blocks `/admin/*` and is correct about every request it can see.

    ./run.sh 30     →  http://127.0.0.1:9300

**Goal:** the backend's `/admin/flag`.

**Hint:** the proxy and the backend do not agree about where one request stops
and the next begins.
