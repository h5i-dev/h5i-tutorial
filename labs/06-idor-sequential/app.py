#!/usr/bin/env python3
"""Lab 06 — Invoices. Authentication answers "who"; nothing answers "whose"."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("invoices")

INVOICES = {i: {"id": i, "account": 77, "total": 40 + i % 13} for i in range(1030, 1051)}
INVOICES[1004] = {"id": 1004, "account": 1, "total": 0, "memo": f"escrow release code {FLAG}"}
for i in range(1000, 1030):
    INVOICES.setdefault(i, {"id": i, "account": 3 + i % 5, "total": 100 + i % 7})


@app.get("/")
def index(req):
    return html('<h1>Billing</h1><p>You are account 77. '
                '<a href="/api/invoice?id=1041">latest invoice</a></p>')


@app.get("/api/invoice")
def invoice(req):
    who = req.cookies.get("account", "77")
    try:
        wanted = int(req.query.get("id", "0"))
    except ValueError:
        return js({"error": "bad id"}, 400)
    row = INVOICES.get(wanted)
    if not row:
        return js({"error": "no such invoice"}, 404)
    # The bug: `who` is read and never compared to `row["account"]`.
    return js({"viewer_account": int(who), **row})


if __name__ == "__main__":
    serve(app, 9060)
