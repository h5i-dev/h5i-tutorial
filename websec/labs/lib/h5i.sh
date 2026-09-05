# Shared helpers for every `solve.sh`. Source it; do not run it.
#
# Five functions. Each exists because of a seam in the workbench, not because
# the labs have anything in common.
#
#   send   `websec replay` answers with what it changed and how the response
#          looked — status, size, headers — and never with the body, which is
#          right for a verb that may have just pulled down a database dump. An
#          exploit almost always wants the body, so it must name the message
#          the replay created. That is two calls, and this is them.
#   last   the newest request in the session, as `req_N`. Needed after a
#          `browser navigate`, which is the one thing `requests` does not name.
#   body   everything after the blank line of an HTTP message.
#   flag   the first FLAG{...} on standard input.
#   ready  wait for a lab to answer, so a run that started too early does not
#          read as a lab that resists.

H5I="${H5I:-h5i}"

# Fail loudly and early rather than at the first confusing empty result.
if ! "$H5I" websec --help >/dev/null 2>&1; then
    echo "This tutorial needs h5i with the websec plugin." >&2
    echo "  h5i plugin install websec --from ./h5i-websec   (see SETUP.md)" >&2
    echo "  or point H5I= at a build that has it: H5I=../h5i/target/release/h5i" >&2
    exit 2
fi

# send SESSION ID [replay flags...] -> the response as an HTTP message
send() {
    local session="$1" id="$2"
    shift 2
    local reply seq
    reply="$("$H5I" websec replay "$id" --session "$session" "$@")" || return 1
    seq="$(printf '%s' "$reply" | python3 -c \
        'import json,sys; print(json.load(sys.stdin).get("seq",""))')"
    [ -n "$seq" ] || { printf '%s\n' "$reply" >&2; return 1; }
    "$H5I" websec show "res_$seq" --session "$session" --raw
}

# last SESSION -> req_N for the newest message in the session
last() {
    "$H5I" websec requests --session "$1" | python3 -c '
import json, sys
rows = json.load(sys.stdin)["requests"]
print("req_%d" % max(row["seq"] for row in rows))
'
}

# The body of an HTTP message on standard input. Either line ending: h5i
# writes the request half with CRLF, because that half is a file
# `replay --raw-request` can read back, and the response half with LF.
body() {
    python3 -c '
import re, sys
print(re.split(r"\r?\n\r?\n", sys.stdin.read(), maxsplit=1)[-1], end="")
'
}

# The first flag on standard input.
flag() {
    python3 -c '
import re, sys
found = re.search(r"FLAG\{[A-Za-z0-9_.@!-]+\}", sys.stdin.read())
print(found.group(0) if found else "no flag found")
'
}

# jfield NAME — read one top-level field out of a JSON body on standard input.
jfield() {
    python3 -c '
import json, re, sys
raw = re.split(r"\r?\n\r?\n", sys.stdin.read(), maxsplit=1)[-1]
try:
    print(json.loads(raw).get(sys.argv[1], ""))
except Exception:
    print("")
' "$1"
}

# ready URL [SECONDS] — wait until the lab answers at all.
ready() {
    local url="$1" seconds="${2:-20}" waited=0
    while [ "$waited" -lt "$seconds" ]; do
        curl -fsS -o /dev/null --max-time 2 "$url" 2>/dev/null && return 0
        sleep 1
        waited=$((waited + 1))
    done
    return 1
}

# Set $SESSION to a name unique to this run and arrange for it to be closed.
# Call it plainly — `new_session lab01` — not inside `$(...)`: a trap set in a
# subshell fires when the subshell ends, which is before the session exists.
new_session() {
    SESSION="${1:-lab}-$$"
    trap '"$H5I" browser close --session "$SESSION" >/dev/null 2>&1' EXIT
}
