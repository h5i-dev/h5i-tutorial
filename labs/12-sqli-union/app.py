#!/usr/bin/env python3
"""Lab 12 — Catalogue. String concatenation is the vulnerability."""
import pathlib
import sqlite3
import sys
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("catalogue")
LOCAL = threading.local()

SCHEMA = """
CREATE TABLE products (id INTEGER, name TEXT, price INTEGER);
CREATE TABLE api_keys (id INTEGER, owner TEXT, secret TEXT);
INSERT INTO products VALUES (1,'Brass Compass',48),(2,'Field Notebook',12),
                            (3,'Compass Rose Poster',20),(4,'Ink Pot',7);
"""


def db() -> sqlite3.Connection:
    if not hasattr(LOCAL, "conn"):
        LOCAL.conn = sqlite3.connect(":memory:")
        LOCAL.conn.executescript(SCHEMA)
        LOCAL.conn.execute("INSERT INTO api_keys VALUES (1,'ops',?)", (FLAG,))
    return LOCAL.conn


@app.get("/")
def index(req):
    return html('<h1>Catalogue</h1><form action="/api/products">'
                '<input name="q" placeholder="search"><button>go</button></form>')


@app.get("/api/products")
def products(req):
    q = req.query.get("q", "")
    # The bug: the query is built by concatenation, so the quote in the
    # parameter ends the string literal and everything after it is SQL.
    sql = f"SELECT id, name, price FROM products WHERE name LIKE '%{q}%'"
    try:
        rows = db().execute(sql).fetchall()
    except sqlite3.Error as err:
        # A verbose error is a gift to the tester and the reason this lab is
        # the easy one.
        return js({"error": str(err), "sql": sql}, 500)
    return js({"q": q, "results": [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]})


if __name__ == "__main__":
    serve(app, 9120)
