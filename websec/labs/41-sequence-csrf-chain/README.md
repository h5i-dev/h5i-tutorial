# Lab 41 — Settings

**Class:** mass assignment behind a CSRF token · **Difficulty:** ③

The settings form is protected by a CSRF token that is minted fresh on every
render and accepted once. The protection works.

    ./run.sh 41     →  http://127.0.0.1:9410

**Goal:** `/admin/flag` wants `role=admin`. Credentials are `guest` / `guest`.

**The technique this lab teaches:** `h5i websec sequence` — a multi-step flow
with bindings between the steps, because a single `replay` cannot test an
endpoint whose token is minted by the request before it.
