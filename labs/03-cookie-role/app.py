#!/usr/bin/env python3
"""Lab 03 — Helpdesk. A cookie the server did not sign is a cookie you write."""
import base64
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("helpdesk")


def seal(claims: dict) -> str:
    # The bug: base64 is an encoding, not a signature. Nothing here binds the
    # value to this server, so anybody can mint one.
    return base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")


def unseal(token: str):
    try:
        pad = "=" * (-len(token) % 4)
        return json.loads(base64.urlsafe_b64decode(token + pad))
    except Exception:
        return None


@app.get("/")
def index(req):
    return html('<h1>Helpdesk</h1><p><a href="/login">log in as guest</a> · '
                '<a href="/tickets">tickets</a> · <a href="/admin">admin</a></p>')


@app.get("/login")
def login(req):
    token = seal({"user": "guest", "role": "agent", "tenant": "acme"})
    return js({"ok": True, "as": "guest"}).cookie("session", token, http_only=False)


@app.get("/tickets")
def tickets(req):
    claims = unseal(req.cookies.get("session", ""))
    if not claims:
        return js({"error": "log in first"}, 401)
    return js({"as": claims["user"], "role": claims["role"], "open": 3})


@app.get("/admin")
def admin(req):
    claims = unseal(req.cookies.get("session", "")) or {}
    if claims.get("role") != "admin":
        return js({"error": "agents cannot see this", "your_role": claims.get("role")}, 403)
    return js({"panel": "admin", "master_key": FLAG})


if __name__ == "__main__":
    serve(app, 9030)
