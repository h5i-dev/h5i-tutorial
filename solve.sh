#!/usr/bin/env bash
# solve.sh NN — start lab NN, run its PoC, stop it. The one-command demo.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
NN="${1:?usage: $0 NN}"
DIR="$(echo "$ROOT/labs/$NN"-*)"
[ -d "$DIR" ] || { echo "no lab $NN" >&2; exit 1; }

export FLAG="${FLAG:-FLAG{$(basename "$DIR" | cut -d- -f2- | tr '-' '_')}}"
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
    echo "port $PORT is already in use; stop it first (./run.sh stop)" >&2
    exit 1
fi

python3 "$DIR/app.py" > "$ROOT/.lab-$NN.log" 2>&1 &
APP=$!
trap 'kill $APP 2>/dev/null; wait $APP 2>/dev/null' EXIT
for _ in $(seq 1 40); do
    curl -fsS -o /dev/null --max-time 1 "http://127.0.0.1:$PORT/" 2>/dev/null && break
    kill -0 $APP 2>/dev/null || { echo "the lab exited:" >&2; cat "$ROOT/.lab-$NN.log" >&2; exit 1; }
    sleep 0.3
done

GOT="$(bash "$DIR/solve.sh" "http://127.0.0.1:$PORT" | tail -1)"
printf '%s\n' "$GOT"
[ "$GOT" = "$FLAG" ] && exit 0
echo "expected $FLAG" >&2
exit 1
