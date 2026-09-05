#!/usr/bin/env python3
"""Lab 01 — Statuspage. A parameter the UI never varies is still a parameter."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("statuspage")

PUBLIC = [{"service": "api", "state": "operational"}, {"service": "web", "state": "operational"}]
INTERNAL = [
    {"service": "api", "state": "operational", "note": "rate limiter disabled for the demo tenant"},
    {"service": "vault", "state": "degraded", "note": f"root token rotated to {FLAG}"},
]


@app.get("/")
def index(req):
    return html(
        "<h1>Acme Status</h1>"
        '<p>Live data: <a href="/api/status?level=public">/api/status?level=public</a></p>'
    )


@app.get("/api/status")
def status(req):
    level = req.query.get("level", "public")
    # The bug: `level` decides how much to disclose and nothing decides who may
    # ask for which level. The UI only ever sends `public`, which the developer
    # mistook for a constraint.
    rows = INTERNAL if level == "internal" else PUBLIC
    return js({"level": level, "levels": ["public", "internal"], "services": rows})


if __name__ == "__main__":
    serve(app, 9010)
