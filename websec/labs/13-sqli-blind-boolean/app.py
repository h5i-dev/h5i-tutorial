#!/usr/bin/env python3
"""Lab 13 — Waitlist. One bit of truth per request is still an oracle."""
import pathlib
import sqlite3
import sys
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("waitlist")
LOCAL = threading.local()


def db() -> sqlite3.Connection:
    if not hasattr(LOCAL, "conn"):
        conn = sqlite3.connect(":memory:")
        conn.executescript(
            "CREATE TABLE members (email TEXT);"
            "CREATE TABLE vouchers (code TEXT);"
            "INSERT INTO members VALUES ('ada@example.test'),('grace@example.test');"
        )
        conn.execute("INSERT INTO vouchers VALUES (?)", (FLAG,))
        LOCAL.conn = conn
    return LOCAL.conn


@app.get("/")
def index(req):
    return html('<h1>Waitlist</h1><p>Check whether an address is on the list: '
                '<a href="/api/check?email=ada@example.test">/api/check?email=</a></p>')


@app.get("/api/check")
def check(req):
    email = req.query.get("email", "")
    sql = f"SELECT 1 FROM members WHERE email = '{email}'"
    try:
        found = db().execute(sql).fetchone() is not None
    except sqlite3.Error:
        # The bug is the concatenation above. What makes it *blind* is here:
        # one boolean out, and the same 200 whether the query broke or missed.
        found = False
    return js({"on_list": found})


if __name__ == "__main__":
    serve(app, 9130)
