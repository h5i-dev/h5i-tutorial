# Lab 02 — Curio Shop

**Class:** parameter tampering (form) · **Difficulty:** ①

A shop with 20 credits in your account and two things you can afford. There is
a third thing, and the checkout endpoint knows its name.

    ./run.sh 02     →  http://127.0.0.1:9020

**Goal:** own the vault key.

**Hint:** `h5i websec show req_N --raw` prints the POST body exactly as it went
out. Everything in it came from the client.
