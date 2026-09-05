# Lab 18 — Avatar

**Class:** XML external entity (XXE) via upload · **Difficulty:** ③

Upload an SVG avatar. The server parses it and echoes the title back.

    ./run.sh 18     →  http://127.0.0.1:9180

**Goal:** read `service.env` from the service's working directory (the homepage
prints the path).

**Hint:** SVG is XML, and XML has a feature for including other files.
