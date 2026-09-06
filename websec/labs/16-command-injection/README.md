# Lab 16 — Logdesk

**Class:** OS command injection · **Difficulty:** ②

A log search box. The team knows about shell injection: `&&`, `||`, `|`, `>`,
`<`, backticks and `$(` are all rejected.

    ./run.sh 16     →  http://127.0.0.1:9160

**Goal:** read `deploy.key`, which sits next to the log file.

**Hint:** the blocklist has no entry for the two characters that matter most.
