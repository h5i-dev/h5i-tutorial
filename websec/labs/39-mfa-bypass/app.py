#!/usr/bin/env python3
"""Lab 39 — Twostep. The token issued before the second factor already works."""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("twostep")

USERS = {"dana": "correct-horse"}
CODES = {"dana": "914722"}
SESSIONS: dict[str, dict] = {}


@app.get("/")
def index(req):
    return html("<h1>Twostep</h1>"
                '<p><code>POST /api/login {"user","password"}</code> → a token, then '
                '<code>POST /api/mfa {"code"}</code> with that token.</p>'
                "<p>Try <code>dana</code> / <code>correct-horse</code>. "
                "The six-digit code goes to a phone you do not have.</p>"
                "<p><code>GET /api/vault</code> needs a fully authenticated session.</p>")


@app.post("/api/login")
def login(req):
    body = req.json() or {}
    user, password = str(body.get("user", "")), str(body.get("password", ""))
    if USERS.get(user) != password:
        return js({"error": "bad credentials"}, 401)
    token = secrets.token_hex(12)
    # The bug: one token, marked as not-yet-verified, and the marker is never
    # consulted anywhere but here. The "temporary" token is a session.
    SESSIONS[token] = {"user": user, "mfa": False}
    return js({"token": token, "mfa_required": True})


@app.post("/api/mfa")
def mfa(req):
    session = SESSIONS.get(req.header("Authorization", "").removeprefix("Bearer "))
    if not session:
        return js({"error": "no session"}, 401)
    if str((req.json() or {}).get("code", "")) != CODES[session["user"]]:
        return js({"error": "bad code"}, 401)
    session["mfa"] = True
    return js({"ok": True})


@app.get("/api/vault")
def vault(req):
    session = SESSIONS.get(req.header("Authorization", "").removeprefix("Bearer "))
    if not session:
        return js({"error": "sign in"}, 401)
    # `session["mfa"]` is right there and nothing reads it.
    return js({"user": session["user"], "vault": FLAG})


if __name__ == "__main__":
    serve(app, 9390)
