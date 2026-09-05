# Lab 35 — Wallet

**Class:** race condition (check-then-act) · **Difficulty:** ③

alice has 100 credits. `/api/rewards` gives the prize to anyone holding 500.

    ./run.sh 35     →  http://127.0.0.1:9350

**Goal:** get 500 into the vault.

**Hint:** the transfer endpoint reads a balance, thinks for a moment, and only
then subtracts. Ask how wide that moment is.
