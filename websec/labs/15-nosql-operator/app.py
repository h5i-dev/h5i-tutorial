#!/usr/bin/env python3
"""Lab 15 — Vaultdoor. A document store reads objects as operators."""
import hashlib
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("vaultdoor")


def h(word: str) -> str:
    return hashlib.sha256(word.encode()).hexdigest()


USERS = [
    {"username": "admin", "password": h("Tr0ub4dor&3"), "role": "admin", "note": FLAG},
    {"username": "kim", "password": h("kittens"), "role": "user", "note": "nothing here"},
]


def matches(doc: dict, query: dict) -> bool:
    """A miniature Mongo-style matcher: exactly the semantics that make this
    class of bug possible. A scalar means equality; an object means operators."""
    for field, want in query.items():
        have = doc.get(field)
        if isinstance(want, dict):
            for op, arg in want.items():
                if op == "$ne" and have == arg:
                    return False
                if op == "$gt" and not (have is not None and have > arg):
                    return False
                if op == "$in" and have not in arg:
                    return False
                if op == "$regex" and not (isinstance(have, str) and re.search(arg, have)):
                    return False
                if op not in ("$ne", "$gt", "$in", "$regex"):
                    return False
        elif have != want:
            return False
    return True


@app.get("/")
def index(req):
    return html('<h1>Vaultdoor</h1><p>POST /api/login {"username","password"}</p>'
                "<p>Passwords are stored as SHA-256; nothing you type can equal a hash.</p>")


@app.post("/api/login")
def login(req):
    payload = req.json()
    if not isinstance(payload, dict):
        return js({"error": "json body required"}, 400)
    # The bug: the request's JSON becomes the query document. A field the client
    # sent as an object is read by the store as an operator, not as a value.
    query = {"username": payload.get("username"), "password": payload.get("password")}
    for row in USERS:
        if matches(row, query):
            return js({"ok": True, "role": row["role"], "note": row["note"]})
    return js({"error": "bad credentials"}, 401)


if __name__ == "__main__":
    serve(app, 9150)
