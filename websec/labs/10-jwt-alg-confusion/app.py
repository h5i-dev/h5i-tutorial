#!/usr/bin/env python3
"""Lab 10 — Passport. A JWT is a claim about who checks it."""
import base64
import hashlib
import hmac
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("passport")
SECRET = b"letmein"  # from the sample config, never rotated


def b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def unb64(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def issue(claims: dict) -> str:
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = b64(json.dumps(claims).encode())
    sig = hmac.new(SECRET, f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{b64(sig)}"


def verify(token: str):
    try:
        head_s, body_s, sig_s = token.split(".")
        head = json.loads(unb64(head_s))
        claims = json.loads(unb64(body_s))
    except Exception:
        return None
    alg = head.get("alg", "HS256")
    # Bug #1: the algorithm is read out of the token the caller supplied, and
    # `none` short-circuits the check it was supposed to survive.
    if alg.lower() == "none":
        return claims
    if alg != "HS256":
        return None
    want = b64(hmac.new(SECRET, f"{head_s}.{body_s}".encode(), hashlib.sha256).digest())
    # Bug #2: even on the honest path, the secret is a dictionary word.
    return claims if hmac.compare_digest(want, sig_s) else None


@app.get("/")
def index(req):
    return html('<h1>Passport</h1><p><a href="/api/token">get a guest token</a> · '
                'admin area: <a href="/api/vault">/api/vault</a></p>')


@app.get("/api/token")
def token(req):
    return js({"token": issue({"sub": "guest", "role": "guest", "iss": "passport"})})


@app.get("/api/vault")
def vault(req):
    claims = verify(req.header("Authorization", "").removeprefix("Bearer ")) or {}
    if claims.get("role") != "admin":
        return js({"error": "admin role required", "saw": claims.get("role")}, 403)
    return js({"vault": "open", "recovery_phrase": FLAG})


if __name__ == "__main__":
    serve(app, 9100)
