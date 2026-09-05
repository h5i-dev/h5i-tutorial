#!/usr/bin/env python3
"""Lab 33 — Newsroom. A header that changes the page and not the cache key."""
import pathlib
import secrets
import sys
import threading
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.bot import Bot, Collector
from lib.miniweb import FLAG, App, Res, html, js, serve, text

origin = App("newsroom-origin")     # :9331 — the application
cache = App("newsroom-cache")       # :9330 — what the world talks to

ADMIN_COOKIE = "adm_" + secrets.token_hex(8)
BOT_KEY = secrets.token_hex(8)
COLLECTOR = Collector()
STORE: dict[tuple, tuple] = {}      # key -> (expires_at, status, headers, body)
TTL = 6.0


# ---------------------------------------------------------------- the origin
@origin.get("/")
def home(req):
    # The bug, half one: an untrusted header is reflected into the page.
    site = req.header("X-Forwarded-Host", "127.0.0.1:9330")
    return html(f'<html><head><link rel="canonical" href="http://{site}/"></head>'
                "<body><h1>Newsroom</h1><p>Today: nothing happened.</p></body></html>")


@origin.get("/internal/login")
def internal_login(req):
    if req.query.get("t") != BOT_KEY:
        return js({"error": "not for you"}, 403)
    return html("<h1>editor</h1>").cookie("session", ADMIN_COOKIE, http_only=True)


@origin.get("/admin/flag")
def admin_flag(req):
    if req.cookies.get("session") != ADMIN_COOKIE:
        return js({"error": "editors only"}, 403)
    return js({"flag": FLAG})


@origin.get("/collect")
def collect(req):
    COLLECTOR.put(req.query.get("id", "anon"), req.query.get("c", ""))
    return text("ok")


@origin.get("/collected")
def collected(req):
    return js({"rows": COLLECTOR.get(req.query.get("id", "anon"))})


# ----------------------------------------------------------------- the cache
FORWARD = ("X-Forwarded-Host", "Cookie", "User-Agent", "Accept", "Origin", "Referer")


def fetch_origin(req) -> tuple:
    up = urllib.request.Request(f"http://127.0.0.1:9331{req.raw_path}", method=req.method)
    for name in FORWARD:
        if req.headers.get(name):
            up.add_header(name, req.headers[name])
    try:
        with urllib.request.urlopen(up, timeout=4) as answer:
            return answer.status, list(answer.headers.items()), answer.read()
    except urllib.error.HTTPError as err:
        return err.code, list(err.headers.items()), err.read()


@cache.any(".*")
def through(req):
    # The bug, half two: the key is host plus path. `X-Forwarded-Host` changes
    # the response and does not change where the response is filed.
    cacheable = req.method == "GET" and req.path == "/"
    key = (req.header("Host", ""), req.path)
    now = time.time()
    if cacheable:
        hit = STORE.get(key)
        if hit and hit[0] > now:
            status, headers, body = hit[1:]
            return Res(body, status, [(k, v) for k, v in headers
                                      if k.lower() not in ("content-length", "content-type")]
                       + [("X-Cache", "HIT")],
                       content_type=dict((k.lower(), v) for k, v in headers)
                       .get("content-type", "text/html"))
    status, headers, body = fetch_origin(req)
    if cacheable and status == 200:
        STORE[key] = (now + TTL, status, headers, body)
    return Res(body, status,
               [(k, v) for k, v in headers if k.lower() not in ("content-length", "content-type")]
               + [("X-Cache", "MISS")],
               content_type=dict((k.lower(), v) for k, v in headers).get("content-type", "text/html"))


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(origin, 9331, background=True)
    bot = Bot(f"http://127.0.0.1:9330/internal/login?t={BOT_KEY}")

    def editor():
        while True:
            bot.visit("http://127.0.0.1:9330/")
            time.sleep(2)

    threading.Thread(target=editor, daemon=True).start()
    run(cache, 9330)
