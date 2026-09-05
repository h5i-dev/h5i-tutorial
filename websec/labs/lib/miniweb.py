"""A ~200-line web toolkit so every lab app fits on one screen.

Standard library only. Nothing here is the vulnerability: the bug in each lab
lives in that lab's `app.py`, and this file is the boring part it stands on.
"""

from __future__ import annotations

import json
import os
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FLAG = os.environ.get("FLAG", "FLAG{you_should_not_read_me_here}")


class Req:
    """One request, already parsed."""

    def __init__(self, handler: BaseHTTPRequestHandler):
        self.method = handler.command
        parsed = urllib.parse.urlsplit(handler.path)
        self.path = parsed.path
        self.raw_path = handler.path
        self.raw_query = parsed.query
        self.headers = handler.headers
        self.client = handler.client_address[0]
        length = int(handler.headers.get("Content-Length") or 0)
        self.body = handler.rfile.read(length) if length else b""

    @property
    def query(self) -> dict[str, str]:
        """Last value wins, which is what most frameworks do."""
        return {k: v[-1] for k, v in urllib.parse.parse_qs(self.raw_query, keep_blank_values=True).items()}

    def query_all(self, name: str) -> list[str]:
        return urllib.parse.parse_qs(self.raw_query, keep_blank_values=True).get(name, [])

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")

    def json(self):
        try:
            return json.loads(self.body or b"null")
        except Exception:
            return None

    @property
    def form(self) -> dict[str, str]:
        return {k: v[-1] for k, v in urllib.parse.parse_qs(self.text, keep_blank_values=True).items()}

    @property
    def cookies(self) -> dict[str, str]:
        jar: dict[str, str] = {}
        for part in (self.headers.get("Cookie") or "").split(";"):
            if "=" in part:
                k, _, v = part.partition("=")
                jar[k.strip()] = v.strip()
        return jar

    def header(self, name: str, default: str = "") -> str:
        return self.headers.get(name, default)

    def multipart(self) -> dict[str, dict]:
        """`{name: {"filename": str, "content_type": str, "data": bytes}}`."""
        ctype = self.headers.get("Content-Type", "")
        match = re.search(r'boundary="?([^";]+)"?', ctype)
        if not match:
            return {}
        sep = b"--" + match.group(1).encode()
        parts: dict[str, dict] = {}
        for chunk in self.body.split(sep):
            if b"\r\n\r\n" not in chunk:
                continue
            head, _, data = chunk.partition(b"\r\n\r\n")
            head_text = head.decode("utf-8", "replace")
            name = re.search(r'name="([^"]*)"', head_text)
            if not name:
                continue
            filename = re.search(r'filename="([^"]*)"', head_text)
            ct = re.search(r"Content-Type:\s*([^\r\n]+)", head_text, re.I)
            parts[name.group(1)] = {
                "filename": filename.group(1) if filename else None,
                "content_type": ct.group(1).strip() if ct else "",
                "data": data.rstrip(b"\r\n-"),
            }
        return parts


class Res:
    """One response, before it is written."""

    def __init__(self, body=b"", status=200, headers=None, content_type="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode()
        self.body = body
        self.status = status
        self.headers: list[tuple[str, str]] = [("Content-Type", content_type)]
        self.headers += list(headers or [])

    def with_header(self, name: str, value: str) -> "Res":
        self.headers.append((name, value))
        return self

    def cookie(self, name: str, value: str, **opts) -> "Res":
        bits = [f"{name}={value}", "Path=/"]
        if opts.get("http_only", True):
            bits.append("HttpOnly")
        if opts.get("same_site"):
            bits.append(f"SameSite={opts['same_site']}")
        if opts.get("max_age") is not None:
            bits.append(f"Max-Age={opts['max_age']}")
        return self.with_header("Set-Cookie", "; ".join(bits))


def js(obj, status=200, headers=None) -> Res:
    return Res(json.dumps(obj), status, headers, "application/json")


def html(markup: str, status=200, headers=None) -> Res:
    return Res(markup, status, headers)


def text(body: str, status=200, headers=None) -> Res:
    return Res(body, status, headers, "text/plain; charset=utf-8")


def redirect(location: str, status=302, headers=None) -> Res:
    return Res(b"", status, [("Location", location)] + list(headers or []))


class App:
    """Routes are `(method, compiled path)`; capture groups become arguments."""

    def __init__(self, name: str = "app"):
        self.name = name
        self.routes: list[tuple[str, re.Pattern, callable]] = []
        self.fallback = None
        self.state: dict = {}
        self.lock = threading.Lock()

    def route(self, method: str, pattern: str):
        def register(fn):
            self.routes.append((method.upper(), re.compile(f"^{pattern}$"), fn))
            return fn

        return register

    def get(self, pattern: str):
        return self.route("GET", pattern)

    def post(self, pattern: str):
        return self.route("POST", pattern)

    def any(self, pattern: str):
        return self.route("*", pattern)

    def default(self, fn):
        self.fallback = fn
        return fn

    def dispatch(self, req: Req) -> Res:
        for method, pattern, fn in self.routes:
            if method not in ("*", req.method):
                continue
            hit = pattern.match(req.path)
            if hit:
                return fn(req, *hit.groups())
        if self.fallback:
            return self.fallback(req)
        return js({"error": "not found", "path": req.path}, 404)


def _handler_for(app: App):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        server_version = "miniweb"
        sys_version = ""

        def log_message(self, *args):
            if os.environ.get("LAB_VERBOSE"):
                BaseHTTPRequestHandler.log_message(self, *args)

        def _serve(self):
            try:
                res = app.dispatch(Req(self))
            except Exception as err:  # a lab that crashes should say so, not hang
                res = js({"error": type(err).__name__, "detail": str(err)}, 500)
            self.send_response(res.status)
            for name, value in res.headers:
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(res.body)))
            self.end_headers()
            self.wfile.write(res.body)

        do_GET = do_POST = do_PUT = do_HEAD = do_PATCH = do_DELETE = do_OPTIONS = _serve

    return Handler


def serve(app: App, port: int, background: bool = False) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), _handler_for(app))
    httpd.daemon_threads = True
    if background:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd
    banner(app, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return httpd


def banner(app: App, port: int, extra: str = ""):
    print(f"  {app.name} listening on http://127.0.0.1:{port}{'  ' + extra if extra else ''}", flush=True)
