# Lab 08 — Ledger

**Class:** authentication mistaken for authorization · **Difficulty:** ②

Two accounts: `alice` (manager) and `bob` (intern). The quarterly report is a
manager page. The intern's dashboard does not link to it.

    ./run.sh 08     →  http://127.0.0.1:9080

**Goal:** read the report as `bob`.

**The technique this lab teaches:** run two h5i sessions at once and send one
session's request with the other session's credentials —
`h5i websec replay req_N --as <other-session>`.
