#!/usr/bin/env python3
"""Lab 24 — SSO. `in` is not `==`, and a redirect target is a credential sink."""
import pathlib
import secrets
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.bot import Bot
from lib.miniweb import FLAG, App, html, js, redirect, serve, text

app = App("sso")
evil = App("attacker-pages")

REGISTERED = "http://127.0.0.1:9240/callback"
USER_COOKIE = "usr_" + secrets.token_hex(8)
BOT_KEY = secrets.token_hex(8)
CODES: dict[str, str] = {}
TOKENS: dict[str, str] = {}
PAGES: dict[str, str] = {}
DROPS: dict[str, list[str]] = {}
BOT: Bot | None = None


@app.get("/")
def index(req):
    return html("<h1>SSO</h1>"
                f"<p>Registered redirect URI: <code>{REGISTERED}</code></p>"
                "<p><code>/oauth/authorize?client_id=notes&redirect_uri=&amp;state=</code><br>"
                "<code>POST /oauth/token {code}</code> → access token<br>"
                "<code>GET /api/profile</code> with <code>Authorization: Bearer</code></p>"
                '<p>A signed-in user opens any link at <code>POST /report {"url"}</code>. '
                'Publish pages with <code>POST /page {"name","html"}</code> → :9241. '
                "Drops at <code>/collect?id=&amp;c=</code> / <code>/collected?id=</code>.</p>")


@app.get("/oauth/authorize")
def authorize(req):
    if req.cookies.get("session") != USER_COOKIE:
        return js({"error": "sign in first"}, 401)
    target = req.query.get("redirect_uri", "")
    # The bug: `in` instead of `==`. Any URI that merely *contains* the
    # registered one passes, including one that contains it as a query value.
    if REGISTERED not in target:
        return js({"error": "redirect_uri not registered"}, 400)
    code = secrets.token_hex(12)
    CODES[code] = "dana"
    joiner = "&" if "?" in target else "?"
    return redirect(f"{target}{joiner}code={code}&state={req.query.get('state', '')}")


@app.post("/oauth/token")
def token(req):
    code = (req.form or {}).get("code") or (req.json() or {}).get("code", "")
    user = CODES.pop(code, None)
    if not user:
        return js({"error": "bad code"}, 400)
    access = secrets.token_hex(12)
    TOKENS[access] = user
    return js({"access_token": access, "token_type": "Bearer"})


@app.get("/api/profile")
def profile(req):
    user = TOKENS.get(req.header("Authorization", "").removeprefix("Bearer "))
    if not user:
        return js({"error": "bad token"}, 401)
    return js({"user": user, "api_key": FLAG})


@app.get("/callback")
def callback(req):
    return text("the notes app would exchange this code now")


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
    return js({"served_at": f"http://127.0.0.1:9241/p/{body.get('name', 'x')}"})


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
    serve(evil, 9241, background=True)
    BOT = Bot(f"http://127.0.0.1:9240/internal/login?t={BOT_KEY}")
    run(app, 9240)
