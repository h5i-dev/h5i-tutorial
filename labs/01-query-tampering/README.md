# Lab 01 — Statuspage

**Class:** parameter tampering · **Difficulty:** ①

Acme publishes a status page. It reads live data from a JSON endpoint and
renders two green ticks.

    ./run.sh 01     →  http://127.0.0.1:9010

**Goal:** print the flag.

**Start here**

```bash
h5i browser open http://127.0.0.1:9010/ --session lab01 --new --capture
h5i browser markdown --session lab01
h5i websec requests --session lab01
```

**Hint:** read the whole JSON response, not just the part the page renders.
