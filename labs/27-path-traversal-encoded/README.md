# Lab 27 — Docs

**Class:** path traversal past an encoding filter · **Difficulty:** ④

A document viewer. `../` is stripped from the filename before the file is
opened. The flag is in a sibling directory of `pages/`.

    ./run.sh 27     →  http://127.0.0.1:9270

**Goal:** read `secret/flag.txt`.

**This lab exists to teach one h5i flag.** A payload that survives the filter
must reach the socket *unparsed*, and every ordinary sender will normalise it
first.
