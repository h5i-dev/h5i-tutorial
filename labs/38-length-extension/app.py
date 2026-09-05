#!/usr/bin/env python3
"""Lab 38 — Signer. sha256(secret || message) is not a MAC."""
import hashlib
import pathlib
import secrets
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("signer")
SECRET = secrets.token_bytes(16)     # 16 bytes; unknown to you, and it need not be


def sign(message: bytes) -> str:
    # The bug: a hash of the secret followed by the message. SHA-256 is a
    # Merkle-Damgard construction, so its output *is* its internal state — and
    # anyone holding a digest can carry on hashing from it.
    return hashlib.sha256(SECRET + message).hexdigest()


@app.get("/")
def index(req):
    demo = b"user=guest&role=viewer"
    return html("<h1>Signer</h1>"
                "<p>Signed requests look like "
                "<code>/api/act?data=&lt;urlencoded&gt;&amp;sig=&lt;hex&gt;</code>, where "
                "<code>sig = sha256(secret || data)</code> and the secret is 16 bytes.</p>"
                f"<p>A token you may use: <code>/api/act?data="
                f"{urllib.parse.quote(demo)}&amp;sig={sign(demo)}</code></p>"
                "<p><code>role=admin</code> unseals the archive.</p>")


@app.get("/api/act")
def act(req):
    # Read the signed blob as *bytes*: it is a signed value, not text, and a
    # decode that replaces what it cannot read would break the signature.
    fieldbytes = {}
    for pair in req.raw_query.split("&"):
        name, _, value = pair.partition("=")
        fieldbytes[name] = urllib.parse.unquote_to_bytes(value)
    data = fieldbytes.get("data", b"")
    if sign(data) != fieldbytes.get("sig", b"").decode():
        return js({"error": "bad signature"}, 403)
    fields = urllib.parse.parse_qs(data.decode("utf-8", "replace"), keep_blank_values=True)
    # Last value wins, which is what most query parsers do — and what makes an
    # appended field able to override an earlier one.
    role = fields.get("role", [""])[-1]
    if role != "admin":
        return js({"role": role, "archive": "locked"})
    return js({"role": role, "archive": "open", "contents": FLAG})


if __name__ == "__main__":
    serve(app, 9380)
