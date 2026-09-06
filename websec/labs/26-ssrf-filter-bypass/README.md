# Lab 26 — Webhook tester

**Class:** SSRF past a host blocklist · **Difficulty:** ③

Same primitive as Lab 25, with a filter in front of it. The blocked list is
printed on the homepage.

    ./run.sh 26     →  http://127.0.0.1:9260

An internal admin service listens on **port 9261**, reachable only from this
host.

**Goal:** `/ops/credentials` on the internal service.

**Hint:** the filter reads a string. The socket dials an address. Those are
different things, and one address has many strings.
