#!/usr/bin/env python3
"""Lab 14 — Coupons. No output at all, so the channel is the clock."""
import pathlib
import sqlite3
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("coupons")
LOCAL = threading.local()
PIN = "471902"


def db() -> sqlite3.Connection:
    if not hasattr(LOCAL, "conn"):
        conn = sqlite3.connect(":memory:")
        # Every engine ships one of these. MySQL calls it SLEEP, PostgreSQL
        # pg_sleep, MSSQL WAITFOR DELAY. SQLite has none, so this lab
        # registers one, which is exactly the capability those engines expose.
        conn.create_function("sleep", 1, lambda s: (time.sleep(min(float(s), 2.0)), 0)[1])
        conn.executescript(
            "CREATE TABLE coupons (code TEXT);"
            "CREATE TABLE staff (name TEXT, pin TEXT);"
            "INSERT INTO coupons VALUES ('SPRING10'),('WELCOME');"
        )
        conn.execute("INSERT INTO staff VALUES ('admin', ?)", (PIN,))
        LOCAL.conn = conn
    return LOCAL.conn


@app.get("/")
def index(req):
    return html('<h1>Coupons</h1><p><a href="/api/coupon?code=SPRING10">check a code</a> · '
                'staff: <a href="/api/vault?pin=000000">/api/vault?pin=</a></p>')


@app.get("/api/coupon")
def coupon(req):
    code = req.query.get("code", "")
    try:
        db().execute(f"SELECT 1 FROM coupons WHERE code = '{code}'").fetchone()
    except sqlite3.Error:
        pass
    # The bug is the concatenation. What makes it *fully* blind is this: one
    # constant answer, whatever the query did.
    return js({"checked": True})


@app.get("/api/vault")
def vault(req):
    if req.query.get("pin", "") != PIN:
        return js({"error": "wrong pin"}, 403)
    return js({"vault": "open", "petty_cash_code": FLAG})


if __name__ == "__main__":
    serve(app, 9140)
