#!/usr/bin/env python3
"""Lab 08 — Ledger. Authenticated is not authorized, and only two sessions show it."""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("ledger")

USERS = {"alice": "manager", "bob": "intern"}
SESSIONS: dict[str, str] = {}


@app.get("/")
def index(req):
    return html('<h1>Ledger</h1><p>POST /login {"user":"alice"} · '
                'managers see <a href="/api/reports/quarterly">the quarterly report</a></p>')


@app.post("/login")
def login(req):
    user = (req.json() or {}).get("user", "")
    if user not in USERS:
        return js({"error": "unknown user"}, 401)
    sid = secrets.token_hex(16)
    SESSIONS[sid] = user
    return js({"ok": True, "user": user, "role": USERS[user]}).cookie("sid", sid)


@app.get("/api/reports/quarterly")
def quarterly(req):
    user = SESSIONS.get(req.cookies.get("sid", ""))
    # The bug: the guard asks whether the caller is signed in. It never asks
    # whether the signed-in caller is a manager. The interns' UI simply has no
    # link to this page, which the team reads as a control.
    if not user:
        return js({"error": "sign in"}, 401)
    return js({"as": user, "role": USERS[user], "revenue": 4_120_000, "audit_key": FLAG})


if __name__ == "__main__":
    serve(app, 9080)
