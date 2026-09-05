#!/usr/bin/env bash
# Lab 41 — four steps, one file, the token carried between them by the engine.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9410}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab41

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null
"$H5I" websec sequence "$(dirname "$0")/flow.json" --session "$SESSION" \
    --var user=guest --var password=guest |
    python3 -c 'import json,sys
ran = json.load(sys.stdin)
print(next((s["bound"]["flag"] for s in ran.get("steps", ran.get("ran", []))
            if s.get("bound", {}).get("flag")), "no flag found"))'
