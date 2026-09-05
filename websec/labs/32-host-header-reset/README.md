# Lab 32 — Passreset

**Class:** host header injection → password reset poisoning · **Difficulty:** ③

A password reset flow. Ask for a link, the owner of the mailbox clicks it.
`admin@acme.test` exists; the mailbox is not yours.

    ./run.sh 32     →  http://127.0.0.1:9320

Anything that reaches port **9321** is recorded and readable at
`http://127.0.0.1:9321/seen`.

**Goal:** complete a reset for `admin@acme.test`.

**Hint:** which part of your request decides what the email says?
