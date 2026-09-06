#!/usr/bin/env python3
"""Lab 40 — Prefs jar. Deserialisation is not parsing; it is running."""
import base64
import hashlib
import hmac
import pathlib
import pickle
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("prefs-jar")
# Sample-config secret, never rotated. Its weakness is a second bug; the first
# one is what the value is used to protect.
SECRET = b"prefs-signing-key"


def seal(obj) -> str:
    raw = pickle.dumps(obj)
    mac = hmac.new(SECRET, raw, hashlib.sha256).hexdigest()[:16]
    return base64.urlsafe_b64encode(raw).decode().rstrip("=") + "." + mac


def unseal(cookie: str):
    try:
        blob, _, mac = cookie.rpartition(".")
        raw = base64.urlsafe_b64decode(blob + "=" * (-len(blob) % 4))
        if not hmac.compare_digest(hmac.new(SECRET, raw, hashlib.sha256).hexdigest()[:16], mac):
            return None
        # The bug: `pickle.loads` on anything that got past the signature. A
        # pickle is a program for a stack machine, and `__reduce__` lets it call
        # whatever it likes. A signature only decides *who* may run code.
        return pickle.loads(raw)
    except Exception:
        return None


@app.get("/")
def index(req):
    return html("<h1>Prefs jar</h1>"
                "<p>Preferences ride in the <code>prefs</code> cookie: a pickled dict, "
                "base64, then a truncated HMAC. "
                f'The signing key is the sample one from the docs: <code>{SECRET.decode()}</code>.</p>'
                '<p><a href="/api/prefs">/api/prefs</a> reads it back. '
                "<code>?debug=1</code> reports the result of <code>run</code>, if the "
                "preferences carry one.</p>")


@app.get("/api/prefs")
def prefs(req):
    jar = req.cookies.get("prefs")
    value = unseal(jar) if jar else {"theme": "light"}
    if value is None:
        return js({"error": "bad or unsigned cookie"}, 400)
    return js({"prefs": str(value)[:400]})


if __name__ == "__main__":
    serve(app, 9400)
