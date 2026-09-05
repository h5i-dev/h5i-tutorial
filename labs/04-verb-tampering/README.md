# Lab 04 — Payroll

**Class:** broken access control (verb tampering) · **Difficulty:** ①

`/admin/payslips` returns 403. You are not an admin and there is no login to
attack.

    ./run.sh 04     →  http://127.0.0.1:9040

**Goal:** read the payslips endpoint anyway.

**Hint:** the 403 body tells you which method was checked. What checks the
others?
