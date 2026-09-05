#!/usr/bin/env python3
"""Lab 11 — Keyring. The token names the key that verifies it."""
import base64
import hashlib
import hmac
import json
import os
import pathlib
import secrets
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("keyring")

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab11-"))
(ROOT / "keys").mkdir()
(ROOT / "static").mkdir()
(ROOT / "keys" / "main.key").write_bytes(secrets.token_bytes(32))
# A public asset with stable, fetchable bytes. Ordinary, and served on purpose.
(ROOT / "static" / "brand.txt").write_bytes(b"Keyring Inc. // brand assets v3\n")


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unb64(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def key_for(kid: str) -> bytes | None:
    # The bug: `kid` is a filename taken from the token's own header, joined
    # onto a directory with no normalisation and no containment check.
    try:
        return (ROOT / "keys" / kid).read_bytes()
    except Exception:
        return None


def issue(claims: dict) -> str:
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": "main.key"}).encode())
    body = b64(json.dumps(claims).encode())
    sig = hmac.new(key_for("main.key"), f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{b64(sig)}"


def verify(token: str):
    try:
        head_s, body_s, sig_s = token.split(".")
        head = json.loads(unb64(head_s))
    except Exception:
        return None
    key = key_for(head.get("kid", "main.key"))
    if key is None or head.get("alg") != "HS256":
        return None
    want = b64(hmac.new(key, f"{head_s}.{body_s}".encode(), hashlib.sha256).digest())
    return json.loads(unb64(body_s)) if hmac.compare_digest(want, sig_s) else None


@app.get("/")
def index(req):
    return html('<h1>Keyring</h1><p><a href="/api/token">token</a> · '
                '<a href="/static/brand.txt">brand asset</a> · '
                '<a href="/api/hsm">/api/hsm</a></p>')


@app.get("/api/token")
def token(req):
    return js({"token": issue({"sub": "guest", "role": "guest"})})


@app.get("/static/([A-Za-z0-9._-]+)")
def static(req, name):
    path = ROOT / "static" / name
    if not path.is_file():
        return js({"error": "not found"}, 404)
    from lib.miniweb import Res
    return Res(path.read_bytes(), content_type="text/plain")


@app.get("/api/hsm")
def hsm(req):
    claims = verify(req.header("Authorization", "").removeprefix("Bearer ")) or {}
    if claims.get("role") != "admin":
        return js({"error": "admin role required"}, 403)
    return js({"hsm": "unsealed", "master": FLAG})


if __name__ == "__main__":
    serve(app, 9110)
