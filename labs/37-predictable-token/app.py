#!/usr/bin/env python3
"""Lab 37 — Recover. A token seeded with the clock is a token you can recompute."""
import pathlib
import random
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("recover")
ISSUED: dict[str, str] = {}


def make_token() -> str:
    # The bug, twice over. `random` is a Mersenne Twister — fast, uniform, and
    # entirely reproducible — and it is seeded here with the wall clock, a value
    # the person asking for the token also knows to within a second.
    rng = random.Random(int(time.time()))
    return "%08x%08x" % (rng.getrandbits(32), rng.getrandbits(32))


@app.get("/")
def index(req):
    return html("<h1>Recover</h1>"
                '<p><code>POST /api/recover {"email"}</code> issues a recovery token. '
                "You are shown the token for addresses you own.</p>"
                "<p><code>GET /api/recover/use?token=</code> completes recovery. "
                "<code>admin@acme.test</code> exists.</p>")


@app.post("/api/recover")
def recover(req):
    email = str((req.json() or {}).get("email", ""))
    if not email:
        return js({"error": "email required"}, 400)
    token = make_token()
    ISSUED[token] = email
    if email.endswith("@example.test"):
        # Your own addresses: you see the token, which is ordinary and is also
        # everything an attacker needs to calibrate.
        return js({"email": email, "token": token})
    return js({"email": email, "sent": True})


@app.get("/api/recover/use")
def use(req):
    email = ISSUED.get(req.query.get("token", ""))
    if not email:
        return js({"error": "unknown token"}, 400)
    if email != "admin@acme.test":
        return js({"recovered": email})
    return js({"recovered": email, "master_key": FLAG})


if __name__ == "__main__":
    serve(app, 9370)
