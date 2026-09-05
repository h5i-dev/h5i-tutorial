# Lab 13 — Waitlist

**Class:** blind SQL injection (boolean) · **Difficulty:** ③

`/api/check?email=` answers `{"on_list": true}` or `{"on_list": false}`. That is
the entire output of this application.

    ./run.sh 13     →  http://127.0.0.1:9130

**Goal:** read the voucher code out of the `vouchers` table.

**Hint:** one bit per request. Decide what question is worth a bit.
