# Lab 11 — Keyring

**Class:** JWT key injection (`kid`) · **Difficulty:** ③

The signing secret is 32 random bytes and it is not in the token. `alg: none`
is rejected. `/api/hsm` wants `role: admin`.

    ./run.sh 11     →  http://127.0.0.1:9110

**Goal:** unseal the HSM.

**Hint:** decode the token header and read every field, not just `alg`.
