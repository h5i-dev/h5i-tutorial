# Lab 19 — Rename

**Class:** second-order SQL injection · **Difficulty:** ④

Three endpoints: register, change password, log in. Every one of them uses
bound parameters when it reads your input. There is an `admin` account whose
password you do not know.

    ./run.sh 19     →  http://127.0.0.1:9190

**Goal:** log in as `admin`.

**Hint:** a value that came out of the database is not the same thing as a safe
value.
