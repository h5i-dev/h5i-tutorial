# Lab 17 — Postcard

**Class:** server-side template injection · **Difficulty:** ③

A greeting preview. You supply the template, the server renders it, and the
renderer has no builtins: `{{ open('/etc/passwd') }}` fails.

    ./run.sh 17     →  http://127.0.0.1:9170

**Goal:** read the module-level `VAULT_KEY`.

**Hint:** you are given one object. Objects in this language know a great deal
about the program they live in.
