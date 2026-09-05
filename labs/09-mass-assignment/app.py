#!/usr/bin/env python3
"""Lab 09 — Signup. The object graph accepts whatever the JSON says it is."""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("signup")

USERS: dict[str, dict] = {}
TOKENS: dict[str, str] = {}
DEFAULTS = {"username": "", "email": "", "password": "", "plan": "free",
            "is_admin": False, "credits": 0}


@app.get("/")
def index(req):
    return html('<h1>Signup</h1><p>POST /api/register '
                '{"username","email","password"} → token</p>'
                '<p>Admins: <a href="/api/admin/keys">/api/admin/keys</a></p>')


@app.post("/api/register")
def register(req):
    payload = req.json()
    if not isinstance(payload, dict) or not payload.get("username"):
        return js({"error": "username required"}, 400)
    # The bug: the request body is merged into the record whole. The model has
    # `is_admin` and `credits` columns, and nothing between the wire and the
    # store decides which columns a stranger may name.
    row = {**DEFAULTS, **payload}
    USERS[row["username"]] = row
    token = secrets.token_hex(16)
    TOKENS[token] = row["username"]
    return js({"ok": True, "token": token, "plan": row["plan"]})


@app.get("/api/admin/keys")
def keys(req):
    who = TOKENS.get(req.header("Authorization", "").removeprefix("Bearer "))
    row = USERS.get(who or "", {})
    if not row.get("is_admin"):
        return js({"error": "admins only"}, 403)
    return js({"signing_keys": ["k1", "k2"], "root": FLAG})


if __name__ == "__main__":
    serve(app, 9090)
