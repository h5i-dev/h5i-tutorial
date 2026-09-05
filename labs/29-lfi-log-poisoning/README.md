# Lab 29 — Wiki

**Class:** local file inclusion → log poisoning → SSTI · **Difficulty:** ④

A wiki. Pages live in `pages/` and are rendered as templates before they are
served.

    ./run.sh 29     →  http://127.0.0.1:9290

**Goal:** read the module global `RELEASE_KEY`. There is no page that contains
it and no template you are allowed to submit.

**Hint:** you cannot write a page. You can write into a file the server keeps
anyway.
