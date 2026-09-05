# Lab 28 — Avatars

**Class:** arbitrary file write through an upload · **Difficulty:** ③

An avatar uploader that checks the file's *contents*, not its extension — the
first three bytes must be a JPEG header.

    ./run.sh 28     →  http://127.0.0.1:9280

**Goal:** `GET /api/admin/flag` accepts an `X-Api-Key` from
`config/trusted_keys.txt`, re-read on every request. You do not know a key.

**Hint:** the upload validates *what* you send. Ask what validates *where* it
goes.
