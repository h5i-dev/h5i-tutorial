#!/usr/bin/env python3
"""Lab 19 — Rename. The payload is stored safely and used unsafely."""
import pathlib
import sqlite3
import sys
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("rename")
LOCAL = threading.local()
DB = sqlite3.connect(":memory:", check_same_thread=False)
LOCK = threading.Lock()
DB.executescript(
    "CREATE TABLE users (username TEXT, password TEXT, role TEXT);"
    "INSERT INTO users VALUES ('admin','7f3d9c1a55','admin');"
)


@app.get("/")
def index(req):
    return html('<h1>Rename</h1><p>POST /api/register {"username","password"} · '
                'POST /api/password {"username","password","new"} · '
                'POST /api/login {"username","password"}</p>')


@app.post("/api/register")
def register(req):
    body = req.json() or {}
    user, pw = str(body.get("username", "")), str(body.get("password", ""))
    if not user:
        return js({"error": "username required"}, 400)
    with LOCK:
        # Correct: parameterised. The quote is stored, not executed.
        if DB.execute("SELECT 1 FROM users WHERE username = ?", (user,)).fetchone():
            return js({"error": "taken"}, 409)
        DB.execute("INSERT INTO users VALUES (?, ?, 'user')", (user, pw))
    return js({"ok": True, "username": user})


@app.post("/api/password")
def change(req):
    body = req.json() or {}
    user, pw, new = str(body.get("username", "")), str(body.get("password", "")), str(body.get("new", ""))
    with LOCK:
        row = DB.execute(
            "SELECT username FROM users WHERE username = ? AND password = ?", (user, pw)
        ).fetchone()
        if not row:
            return js({"error": "bad credentials"}, 401)
        # The bug: `row[0]` came out of the database, so it is treated as
        # trusted — and pasted straight into SQL. Trust does not survive a
        # round trip through storage.
        sql = f"UPDATE users SET password = '{new}' WHERE username = '{row[0]}'"
        try:
            DB.executescript(sql)
        except sqlite3.Error as err:
            return js({"error": str(err)}, 500)
    return js({"ok": True, "changed": row[0]})


@app.post("/api/login")
def login(req):
    body = req.json() or {}
    with LOCK:
        row = DB.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (str(body.get("username", "")), str(body.get("password", ""))),
        ).fetchone()
    if not row:
        return js({"error": "bad credentials"}, 401)
    if row[0] != "admin":
        return js({"ok": True, "role": row[0]})
    return js({"ok": True, "role": "admin", "recovery": FLAG})


if __name__ == "__main__":
    serve(app, 9190)
