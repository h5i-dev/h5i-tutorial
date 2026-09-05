#!/usr/bin/env python3
"""Lab 20 — Findit. A filter that deletes tags is a filter you feed twice."""
import html as htmlmod
import pathlib
import re
import secrets
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.bot import Bot, Collector
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("findit")
ADMIN_COOKIE = "adm_" + secrets.token_hex(8)
BOT_KEY = secrets.token_hex(8)
COLLECTOR = Collector()
BOT: Bot | None = None


@app.get("/")
def index(req):
    return html('<h1>Findit</h1>'
                '<form action="/search"><input name="q"><button>search</button></form>'
                '<p>Broken result? <a href="/report">Report a page to an admin</a>.</p>'
                '<p>Exfil helper: <code>/collect?id=&lt;yours&gt;&amp;c=&lt;data&gt;</code> then '
                '<code>/collected?id=&lt;yours&gt;</code></p>')


@app.get("/search")
def search(req):
    q = req.query.get("q", "")
    # The bug: a single pass that deletes opening <script> tags. One pass over
    # a string cannot sanitise a string that changes as it is edited.
    safe = re.sub(r"(?i)<script[^>]*>", "", q)
    return html(f"<h1>Results</h1><p>Nothing found for: {safe}</p>")


@app.get("/report")
def report(req):
    url = req.query.get("url")
    if not url:
        return html('<form action="/report"><input name="url" size="60">'
                    "<button>send to admin</button></form>")
    if BOT:
        BOT.visit(url)
    return js({"queued": url, "note": "an administrator will open it shortly"})


@app.get("/internal/login")
def internal_login(req):
    if req.query.get("t") != BOT_KEY:
        return js({"error": "not for you"}, 403)
    return html("<h1>signed in</h1>").cookie("session", ADMIN_COOKIE, http_only=False)


@app.get("/collect")
def collect(req):
    COLLECTOR.put(req.query.get("id", "anon"), req.query.get("c", ""))
    return text("ok")


@app.get("/collected")
def collected(req):
    return js({"rows": COLLECTOR.get(req.query.get("id", "anon"))})


@app.get("/admin/flag")
def admin_flag(req):
    if req.cookies.get("session") != ADMIN_COOKIE:
        return js({"error": "admin session cookie required"}, 403)
    return js({"flag": FLAG})


if __name__ == "__main__":
    port = 9200
    BOT = Bot(f"http://127.0.0.1:{port}/internal/login?t={BOT_KEY}")
    serve(app, port)
