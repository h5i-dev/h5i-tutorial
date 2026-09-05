#!/usr/bin/env bash
# run.sh NN [...]  — start lab NN in the background and print its URL.
# run.sh stop      — stop every lab this script started.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS="$ROOT/.labs.pids"

if [ "${1:-}" = "stop" ]; then
    [ -f "$PIDS" ] && while read -r pid; do kill "$pid" 2>/dev/null; done < "$PIDS"
    rm -f "$PIDS"
    # Also close any h5i sessions the labs or their victim bots left behind. An
    # abandoned session is a live engine process, and enough of them make
    # `h5i browser list` unreadable.
    H5I="${H5I:-h5i}"
    for id in $("$H5I" browser list --json 2>/dev/null | python3 -c \
        'import json,sys
try: print(" ".join(x["id"] for x in json.load(sys.stdin)))
except Exception: pass' 2>/dev/null); do
        "$H5I" browser close --session "$id" >/dev/null 2>&1
    done
    echo "stopped"
    exit 0
fi

NN="${1:?usage: $0 NN | stop}"
DIR="$(echo "$ROOT/labs/$NN"-* )"
[ -d "$DIR" ] || { echo "no lab $NN" >&2; exit 1; }
PORT="$((9000 + 10#$NN * 10))"


port_free() {   # refuse to run against a process this script did not start
    python3 - "$1" <<'PYX'
import socket, sys
s = socket.socket()
# SO_REUSEADDR, because the lab servers set it too: a socket left in TIME_WAIT
# by the previous lab is one they can bind and this check must not refuse.
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("127.0.0.1", int(sys.argv[1])))
except OSError:
    sys.exit(1)
finally:
    s.close()
PYX
}

if ! port_free "$PORT"; then
    echo "port $PORT is already in use; ./run.sh stop, or find what is holding it" >&2
    exit 1
fi

FLAG="${FLAG:-FLAG{$(basename "$DIR" | cut -d- -f2- | tr '-' '_')}}" \
    python3 "$DIR/app.py" > "$ROOT/.lab-$NN.log" 2>&1 &
echo $! >> "$PIDS"

for _ in $(seq 1 20); do
    curl -fsS -o /dev/null --max-time 1 "http://127.0.0.1:$PORT/" 2>/dev/null && break
    sleep 0.3
done
echo "http://127.0.0.1:$PORT"
