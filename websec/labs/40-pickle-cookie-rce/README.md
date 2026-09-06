# Lab 40 — Prefs jar

**Class:** insecure deserialisation · **Difficulty:** ④

Preferences travel in a signed cookie. The signature is real HMAC-SHA256 —
truncated, but real. The key is printed on the homepage, because it came from
the framework's sample config and nobody changed it.

    ./run.sh 40       →  http://127.0.0.1:9400

**Goal:** read the environment variable `FLAG` out of the server process.

**Hint:** the format of the cookie is the finding, not the key.
