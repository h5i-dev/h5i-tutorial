# Lab 25 — Link preview

**Class:** server-side request forgery · **Difficulty:** ②

Paste a URL and the service fetches it and shows you what it found.

    ./run.sh 25     →  http://127.0.0.1:9250

There is an instance metadata service on this host at port **9251** — the local
stand-in for `169.254.169.254`, which is what a cloud instance would have.

**Goal:** the role credentials.

**Hint:** ask yourself who is making the request, and what that process can
reach that you cannot.
