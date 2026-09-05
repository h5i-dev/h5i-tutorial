# Lab 31 — Reports

**Class:** CRLF / header injection · **Difficulty:** ③

The front end composes a request to an internal report service and always asks
as `guest`. The internal service decides what you may see from an `X-Role`
header that you cannot set.

    ./run.sh 31     →  http://127.0.0.1:9310

**Goal:** a report rendered as `admin`.

**Hint:** the response tells you exactly what the front end sent. Read it, and
count the newlines.
