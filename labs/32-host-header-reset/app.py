#!/usr/bin/env python3
"""Lab 32 — Passreset. The link in the email is built from a header."""
import pathlib
import secrets
import sys
import threading
import time
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("passreset")
mailbox_host = App("attacker-host")

TOKENS: dict[str, str] = {}
SEEN: list[str] = []


@app.get("/")
def index(req):
    return html("<h1>Passreset</h1>"
                '<p><code>POST /api/reset {"email"}</code> emails a reset link. '
                "The address <code>admin@acme.test</code> exists.</p>"
                "<p><code>GET /api/reset/use?token=</code> completes a reset.</p>"
                "<p>Anything that arrives on port 9321 is recorded at "
                "<code>http://127.0.0.1:9321/seen</code>.</p>")


@app.post("/api/reset")
def reset(req):
    email = str((req.json() or {}).get("email", ""))
    if not email:
        return js({"error": "email required"}, 400)
    token = secrets.token_hex(12)
    TOKENS[token] = email
    # The bug: the link the user is asked to click is built from the `Host`
    # header of the request that asked for it — a value the requester chose.
    host = req.header("Host", "127.0.0.1:9320")
    link = f"http://{host}/api/reset/use?token={token}"

    # The owner of the mailbox clicks the link, as people do.
    def click():
        time.sleep(0.4)
        try:
            urllib.request.urlopen(link, timeout=3).read()
        except Exception:
            pass

    threading.Thread(target=click, daemon=True).start()
    return js({"sent_to": email, "note": "check your mail"})


@app.get("/api/reset/use")
def use(req):
    email = TOKENS.get(req.query.get("token", ""))
    if not email:
        return js({"error": "unknown or spent token"}, 400)
    if email != "admin@acme.test":
        return js({"reset": email})
    return js({"reset": email, "recovery_code": FLAG})


@mailbox_host.any(".*")
def record(req):
    SEEN.append(req.raw_path)
    if req.path == "/seen":
        return js({"seen": SEEN})
    return text("recorded")


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(mailbox_host, 9321, background=True)
    run(app, 9320)
