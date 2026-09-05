# Lab 14 — Coupons

**Class:** blind SQL injection (time) · **Difficulty:** ③

`/api/coupon?code=` answers `{"checked": true}`. Always. Whatever you send.

    ./run.sh 14     →  http://127.0.0.1:9140

**Goal:** the staff PIN is six digits, and `/api/vault?pin=` wants it.

**Hint:** the response body is constant. The response *time* is not obliged to be.
