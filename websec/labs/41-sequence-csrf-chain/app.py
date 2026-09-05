#!/usr/bin/env python3
"""Lab 41 — Settings. A rotating CSRF token in front of a mass assignment."""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("settings")

SESSIONS: dict[str, dict] = {}
CSRF: dict[str, str] = {}      # session id -> the one token currently valid


@app.get("/")
def index(req):
    return html("<h1>Settings</h1>"
                '<p><code>POST /api/login {"user","password"}</code> — try '
                "<code>guest</code> / <code>guest</code>.</p>"
                "<p><code>GET /account/settings</code> renders the form. "
                "<code>POST /account/settings</code> takes "
                "<code>display_name</code> and <code>csrf</code>.</p>"
                "<p><code>GET /admin/flag</code> needs <code>role=admin</code>.</p>")


@app.post("/api/login")
def login(req):
    body = req.json() or {}
    if (body.get("user"), body.get("password")) != ("guest", "guest"):
        return js({"error": "bad credentials"}, 401)
    sid = secrets.token_hex(12)
    SESSIONS[sid] = {"user": "guest", "role": "user", "display_name": "Guest"}
    return js({"ok": True}).cookie("session", sid)


@app.get("/account/settings")
def form(req):
    sid = req.cookies.get("session", "")
    if sid not in SESSIONS:
        return js({"error": "sign in"}, 401)
    # A fresh token every render, and the previous one stops working. Correct,
    # and the reason a single replay cannot test the endpoint behind it.
    token = secrets.token_hex(16)
    CSRF[sid] = token
    return html(f'<form method="POST" action="/account/settings">'
                f'<input name="display_name" value="{SESSIONS[sid]["display_name"]}">'
                f'<input type="hidden" name="csrf" value="{token}">'
                f"<button>save</button></form>")


@app.post("/account/settings")
def save(req):
    sid = req.cookies.get("session", "")
    if sid not in SESSIONS:
        return js({"error": "sign in"}, 401)
    form_data = req.form
    if not secrets.compare_digest(form_data.get("csrf", ""), CSRF.get(sid, "\0")):
        return js({"error": "bad csrf token"}, 403)
    CSRF.pop(sid, None)                       # single use
    # The bug: the CSRF check is perfect and the *field list* is not checked at
    # all. Every posted field is merged into the session record, `role` included.
    for key, value in form_data.items():
        if key != "csrf":
            SESSIONS[sid][key] = value
    return js({"ok": True, "profile": SESSIONS[sid]})


@app.get("/admin/flag")
def admin(req):
    session = SESSIONS.get(req.cookies.get("session", ""), {})
    if session.get("role") != "admin":
        return js({"error": "admins only", "your_role": session.get("role")}, 403)
    return js({"flag": FLAG})


if __name__ == "__main__":
    serve(app, 9410)
