#!/usr/bin/env python3
"""Lab 07 — Docstore. Unguessable is not unauthorized, and ids leak sideways."""
import hashlib
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve


def det_uuid(seed: str) -> str:
    return str(uuid.UUID(hashlib.sha256(seed.encode()).hexdigest()[:32]))


app = App("docstore")

DOCS = {
    det_uuid("acme-1"): {"tenant": "acme", "title": "Onboarding", "body": "Welcome."},
    det_uuid("acme-2"): {"tenant": "acme", "title": "Expenses", "body": "Receipts within 30 days."},
    det_uuid("initech-1"): {"tenant": "initech", "title": "TPS Report", "body": "Cover sheet required."},
    det_uuid("initech-2"): {"tenant": "initech", "title": "Break-glass",
                            "body": f"Emergency admin password: {FLAG}"},
}


@app.get("/")
def index(req):
    return html('<h1>Docstore</h1><p>tenant <b>acme</b> · '
                '<a href="/api/documents">your documents</a> · '
                '<a href="/api/search?q=report">search</a></p>')


@app.get("/api/documents")
def mine(req):
    tenant = req.cookies.get("tenant", "acme")
    return js({"tenant": tenant,
               "documents": [{"id": k, "title": v["title"]}
                             for k, v in DOCS.items() if v["tenant"] == tenant]})


@app.get("/api/search")
def search(req):
    # Leak #1: search is global. It filters on the query and not on the tenant,
    # so it hands out the ids the /api/document check relies on being secret.
    q = req.query.get("q", "").lower()
    hits = [{"id": k, "title": v["title"], "tenant": v["tenant"]}
            for k, v in DOCS.items() if q and q in v["title"].lower()]
    return js({"q": q, "hits": hits})


@app.get("/api/document/([0-9a-f-]{36})")
def one(req, doc_id):
    row = DOCS.get(doc_id)
    if not row:
        return js({"error": "not found"}, 404)
    # Leak #2: the id was the only thing standing between a caller and a
    # document. Possession of an identifier is not a permission.
    return js({"id": doc_id, **row})


if __name__ == "__main__":
    serve(app, 9070)
