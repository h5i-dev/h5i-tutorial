# Lab 38 — Signer

**Class:** hash length extension · **Difficulty:** ⑤

Requests are signed with `sha256(secret || data)`. The secret is 16 random
bytes and you will not guess it.

    ./run.sh 38     →  http://127.0.0.1:9380

**Goal:** a valid request whose effective `role` is `admin`.

**Hint:** you do not need the secret. You need what the digest already is.
