# Lab 20 — Findit

**Class:** reflected XSS, filter bypass, session theft · **Difficulty:** ③

A search box reflects your query. `<script>` tags are stripped. There is a
"report this page to an admin" feature, and an administrator really does open
what you send — in a real browser, carrying a real session cookie.

    ./run.sh 20     →  http://127.0.0.1:9200

**Goal:** `/admin/flag` needs the admin's session cookie. Get it.

Two conveniences stand in for infrastructure you would own on a real
engagement:

* `/collect?id=<yours>&c=<data>` records a value; `/collected?id=<yours>`
  reads it back. That is your exfiltration host.
* the admin bot is an `h5i browser --script` session — a real engine running
  your JavaScript.

**Note:** the bot needs `h5i` on `$PATH`, or `H5I=` pointing at the binary.
