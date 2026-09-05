#!/usr/bin/env python3
"""Lab 26 — Webhook tester. A blocklist of spellings, against a resolver."""
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("webhook-tester")
internal = App("internal-admin")

BANNED = ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "[::1]", "internal", "metadata"]


@app.get("/")
def index(req):
    return html("<h1>Webhook tester</h1>"
                "<p><code>/api/test?url=</code> sends a GET to your endpoint and reports it.</p>"
                f"<p>Blocked hosts: <code>{', '.join(BANNED)}</code></p>")


@app.get("/api/test")
def test(req):
    url = req.query.get("url", "")
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    # The bug: the check is on the *spelling* of the host, and the fetch is on
    # what a resolver makes of it. There are many spellings of one address.
    for bad in BANNED:
        if bad in url.lower() or bad in host:
            return js({"error": "blocked host", "matched": bad}, 400)
    try:
        with urllib.request.urlopen(url, timeout=4) as answer:
            return js({"url": url, "status": answer.status,
                       "body": answer.read(4096).decode("utf-8", "replace")})
    except urllib.error.HTTPError as err:
        return js({"url": url, "status": err.code,
                   "body": err.read(2048).decode("utf-8", "replace")})
    except Exception as err:
        return js({"url": url, "error": type(err).__name__, "detail": str(err)}, 502)


@internal.get("/")
def internal_root(req):
    return text("internal admin: /ops/credentials\n")


@internal.get("/ops/credentials")
def creds(req):
    return js({"service": "billing", "token": FLAG})


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(internal, 9261, background=True)
    run(app, 9260)
