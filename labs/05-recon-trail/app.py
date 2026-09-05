#!/usr/bin/env python3
"""Lab 05 — Intranet. The map is written down in four places nobody removed."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("intranet")


@app.get("/")
def index(req):
    return html('<h1>Acme Intranet</h1><p><a href="/docs">docs</a> · '
                '<a href="/api/v3/whoami">whoami</a></p>'
                "<!-- TODO(dana): kill the v0 API before the audit -->")


@app.get("/robots.txt")
def robots(req):
    return text("User-agent: *\nDisallow: /internal/\nDisallow: /api/v0/\n")


@app.get("/docs")
def docs(req):
    return html('<h1>Docs</h1><p>Nothing here yet. See <a href="/internal/notes.md">notes</a>.</p>')


@app.get("/internal/notes.md")
def notes(req):
    return text(
        "# Migration notes\n"
        "- v3 requires a bearer token (see the SSO doc)\n"
        "- v0 predates auth entirely; /api/v0/employee/<id> still answers\n"
        "- id 1 is the service account\n"
    )


@app.get("/api/v3/whoami")
def whoami(req):
    return js({"error": "missing bearer token"}, 401)


@app.get("/api/v0/employee/(\\d+)")
def employee_v0(req, emp_id):
    # The bug: a deprecated version left routable, with the auth check that
    # was only ever added to v3.
    if emp_id == "1":
        return js({"id": 1, "name": "svc-deploy", "notes": f"ssh key passphrase: {FLAG}"})
    return js({"id": int(emp_id), "name": f"employee-{emp_id}"})


if __name__ == "__main__":
    serve(app, 9050)
