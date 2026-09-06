# Lab 34 — Fleet console

**Class:** command injection over a WebSocket · **Difficulty:** ③

A fleet dashboard. The page is static; everything it does travels over
`ws://127.0.0.1:9341/control` as JSON frames.

    ./run.sh 34     →  http://127.0.0.1:9340

**Goal:** `fleet.key` sits in the service's working directory.

**Hint:** `h5i websec socket` sends a frame the same way `replay` sends a
request — through the same policy, budget and receipts, on a session running no
page script at all.
