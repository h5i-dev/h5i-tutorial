#!/usr/bin/env python3
"""Lab 22 — Prefs. The browser attaches the cookie; only a token proves intent."""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.bot import Bot
from lib.miniweb import FLAG, App, html, js, serve

app = App("prefs")
evil = App("evil.example")

ADMIN_COOKIE = "adm_" + secrets.token_hex(8)
BOT_KEY = secrets.token_hex(8)
STATE = {"recovery_email": "admin@acme.test"}
PAGES: dict[str, str] = {}
BOT: Bot | None = None


@app.get("/")
def index(req):
    return html('<h1>Prefs</h1><p>POST /account/recovery-email {email} — changes the '
                "address a password reset is sent to.</p>"
                '<p>A moderator will open any link you leave at '
                '<code>POST /report {"url"}</code>.</p>'
                "<p>Your page host is on port 9221: "
                '<code>POST /page {"name","html"}</code> serves it at '
                "<code>http://127.0.0.1:9221/p/&lt;name&gt;</code>.</p>")


@app.any("/account/recovery-email")
def set_email(req):
    if req.cookies.get("session") != ADMIN_COOKIE:
        return js({"error": "sign in"}, 401)
    # Two bugs, and the second is what makes the first easy to reach.
    #  1. A state-changing request authenticated by an ambient cookie and
    #     nothing else: no token, no `SameSite`, no `Origin` check.
    #  2. The route answers any method, so the write happens on a GET, and a
    #     plain link or an <img> is then a complete attack.
    email = req.query.get("email") or (req.form or {}).get("email", "")
    if not email:
        return js({"error": "email required"}, 400)
    STATE["recovery_email"] = email
    return js({"ok": True, "recovery_email": STATE["recovery_email"]})


@app.get("/account/reset")
def reset(req):
    # Whoever owns the recovery address owns the account.
    if STATE["recovery_email"] != "attacker@evil.example":
        return js({"sent_to": STATE["recovery_email"]})
    return js({"sent_to": STATE["recovery_email"], "reset_token": FLAG})


@app.post("/report")
def report(req):
    url = (req.json() or {}).get("url", "")
    if BOT and url:
        BOT.visit(url)
    return js({"queued": url})


@app.get("/internal/login")
def internal_login(req):
    if req.query.get("t") != BOT_KEY:
        return js({"error": "not for you"}, 403)
    # No SameSite attribute at all — the historical default, and still what a
    # framework gives you when nobody sets one.
    return html("<h1>moderator</h1>").cookie("session", ADMIN_COOKIE)


@app.post("/page")
def put_page(req):
    body = req.json() or {}
    PAGES[str(body.get("name", "x"))] = str(body.get("html", ""))
    return js({"served_at": f"http://127.0.0.1:9221/p/{body.get('name', 'x')}"})


@evil.get("/p/([A-Za-z0-9_-]+)")
def serve_page(req, name):
    return html(PAGES.get(name, "<h1>404</h1>"))


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(evil, 9221, background=True)
    BOT = Bot(f"http://127.0.0.1:9220/internal/login?t={BOT_KEY}")
    run(app, 9220)
