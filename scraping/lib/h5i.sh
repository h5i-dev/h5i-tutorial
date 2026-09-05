# Shared helpers for every `scrape.sh`. Source it; do not run it.
#
# Four functions and one variable. Each is here because of a seam in the tool
# or a courtesy owed to the site, not because the labs have anything in common.
#
#   session   open a named session and close it however the script ends. A
#             leaked session is a live engine process, and enough of them make
#             `h5i browser list` unreadable.
#   pace      sleep between requests. The whole course is ten sites and about
#             thirty pages; none of it needs to be fast, and a scraper with no
#             floor on its request rate is the one that gets an IP blocked.
#   rows      `lib/rows.py` under whichever python is here.
#   need      fail with a sentence rather than at the first confusing empty
#             result.

H5I="${H5I:-h5i}"
LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Seconds between requests, for every lab. Raise it, never lower it below the
# default without a reason you would be willing to write in a mail to the site.
PACE="${PACE:-1}"

need() {
    if ! "$H5I" browser --help >/dev/null 2>&1; then
        echo "This course needs h5i on your PATH, or H5I= pointed at a build." >&2
        echo "  curl -fsSL https://h5i.dev/install.sh | sh" >&2
        echo "  or: H5I=~/src/h5i/target/release/h5i ./run.sh 01" >&2
        exit 2
    fi
}

# session NAME URL [open flags...] — open it, and close it on the way out.
#
# Every remote origin except the URL's own is refused by this session, and the
# refusal is written to `h5i browser requests` with its reason. That is the
# behaviour, not a misconfiguration: a page that pulls a script from a CDN
# needs that CDN named with `--allow`, and lab 06 is the one where it matters.
session() {
    need
    SESSION="$1"; shift
    local url="$1"; shift
    "$H5I" browser close --session "$SESSION" >/dev/null 2>&1 || true
    trap '"$H5I" browser close --session "$SESSION" >/dev/null 2>&1 || true' EXIT
    "$H5I" browser open "$url" --session "$SESSION" --new "$@" >/dev/null
}

pace() { sleep "$PACE"; }

rows() { python3 "$LIB/rows.py" "$@"; }
