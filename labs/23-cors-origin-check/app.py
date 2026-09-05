#!/usr/bin/env python3
"""Lab 23 — Partner API. An origin check written with `endswith`."""
import pathlib
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.bot import Bot
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("partner-api")
evil = App("attacker-pages")

ALLOWED_PREFIX = "http://127.0.0.1"   # meant to say "our own front end"
USER_COOKIE = "usr_" + secrets.token_hex(8)
BOT_KEY = secrets.token_hex(8)
PAGES: dict[str, str] = {}
DROPS: dict[str, list[str]] = {}
BOT: Bot | None = None


@app.get("/")
def index(req):
    return html('<h1>Partner API</h1>'
                "<p><code>/api/me</code> is readable cross-origin by our own front end "
                "(origins under <code>http://127.0.0.1</code>).</p>"
                '<p>A signed-in user will open any link left at <code>POST /report {"url"}</code>.</p>'
                '<p>Publish a page: <code>POST /page {"name","html"}</code> → '
                "<code>http://127.0.0.1:9231/p/&lt;name&gt;</code>. "
                "Drops: <code>/collect?id=&amp;c=</code>, <code>/collected?id=</code>.</p>")


@app.get("/api/me")
def me(req):
    origin = req.header("Origin")
    res = js({"user": "dana", "api_key": FLAG} if req.cookies.get("session") == USER_COOKIE
             else {"user": None})
    # The bug: the allowlist is a *prefix* test on the origin string. An origin
    # is scheme + host + port, and this check reads only as far as the host, so
    # every other port on this machine is inside the allowlist.
    if origin and origin.startswith(ALLOWED_PREFIX):
        res.with_header("Access-Control-Allow-Origin", origin)
        res.with_header("Access-Control-Allow-Credentials", "true")
    return res


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
    return html("<h1>signed in</h1>").cookie("session", USER_COOKIE, http_only=True)


@app.post("/page")
def put_page(req):
    body = req.json() or {}
    PAGES[str(body.get("name", "x"))] = str(body.get("html", ""))
    return js({"served_at": f"http://127.0.0.1:9231/p/{body.get('name', 'x')}"})


@app.get("/collect")
def collect(req):
    DROPS.setdefault(req.query.get("id", "anon"), []).append(req.query.get("c", ""))
    return text("ok")


@app.get("/collected")
def collected(req):
    return js({"rows": DROPS.get(req.query.get("id", "anon"), [])})


@evil.get("/p/([A-Za-z0-9_-]+)")
def serve_page(req, name):
    return html(PAGES.get(name, "<h1>404</h1>"))


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(evil, 9231, background=True)
    BOT = Bot(f"http://127.0.0.1:9230/internal/login?t={BOT_KEY}")
    run(app, 9230)
