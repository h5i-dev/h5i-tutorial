# Lab 15 — Vaultdoor

**Class:** NoSQL operator injection · **Difficulty:** ②

A JSON login against a document store. Passwords are stored as SHA-256 hashes,
so no password you can type will ever equal a stored value.

    ./run.sh 15     →  http://127.0.0.1:9150

**Goal:** log in as `admin`.

**Hint:** the login has never worked by matching a password. Ask what else a
document store can be told to do with one.
