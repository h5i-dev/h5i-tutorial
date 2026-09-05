#!/usr/bin/env python3
"""Lab 21 — Board. HttpOnly hides the cookie, not the session."""
import html as htmlmod
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.bot import Bot, Collector
from lib.miniweb import FLAG, App, App as _A, html, js, serve, text

app = App("board")
ADMIN_COOKIE = "adm_" + secrets.token_hex(8)
BOT_KEY = secrets.token_hex(8)
COLLECTOR = Collector()
COMMENTS: list[dict] = [{"who": "kim", "body": "First!"}]
BOT: Bot | None = None


@app.get("/")
def index(req):
    return html('<h1>Board</h1><p><a href="/board">the board</a> · '
                'POST /api/comment {"who","body"}</p>'
                "<p>A moderator reviews the board every few seconds.</p>"
                '<p>Exfil helper: <code>/collect?id=&lt;yours&gt;&amp;c=&lt;data&gt;</code>, '
                '<code>/collected?id=&lt;yours&gt;</code></p>')


@app.get("/board")
def board(req):
    rows = "".join(
        # The bug: `who` is escaped and `body` is not. One template, two
        # policies, and the second one is the one nobody wrote down.
        f"<li><b>{htmlmod.escape(c['who'])}</b>: {c['body']}</li>" for c in COMMENTS
    )
    return html(f"<h1>Board</h1><ul>{rows}</ul>")


@app.post("/api/comment")
def comment(req):
    payload = req.json() or {}
    COMMENTS.append({"who": str(payload.get("who", "anon")), "body": str(payload.get("body", ""))})
    if BOT:
        BOT.visit(req.header("X-Board-Url") or "http://127.0.0.1:9210/board")
    return js({"ok": True, "comments": len(COMMENTS)})


@app.get("/internal/login")
def internal_login(req):
    if req.query.get("t") != BOT_KEY:
        return js({"error": "not for you"}, 403)
    # HttpOnly: script cannot read this cookie. It still rides on every fetch.
    return html("<h1>moderator</h1>").cookie("session", ADMIN_COOKIE, http_only=True)


@app.get("/collect")
def collect(req):
    COLLECTOR.put(req.query.get("id", "anon"), req.query.get("c", ""))
    return text("ok")


@app.get("/collected")
def collected(req):
    return js({"rows": COLLECTOR.get(req.query.get("id", "anon"))})


@app.get("/admin/api/flag")
def admin_flag(req):
    if req.cookies.get("session") != ADMIN_COOKIE:
        return js({"error": "moderators only"}, 403)
    return js({"flag": FLAG})


if __name__ == "__main__":
    port = 9210
    BOT = Bot(f"http://127.0.0.1:{port}/internal/login?t={BOT_KEY}")
    serve(app, port)
