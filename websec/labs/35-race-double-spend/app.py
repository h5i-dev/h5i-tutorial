#!/usr/bin/env python3
"""Lab 35 — Wallet. Read, decide, write — and a gap between the first and last."""
import pathlib
import secrets
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("wallet")

BALANCES = {"alice": 100, "vault": 0}
TOKENS = {"alice": "tok_" + secrets.token_hex(8)}


@app.get("/")
def index(req):
    return html("<h1>Wallet</h1>"
                f"<p>alice's token: <code>{TOKENS['alice']}</code>, balance 100.</p>"
                '<p><code>POST /api/transfer {"to","amount"}</code> with '
                "<code>Authorization: Bearer</code></p>"
                "<p><code>GET /api/rewards</code> — anyone holding 500 gets the prize.</p>")


@app.post("/api/transfer")
def transfer(req):
    who = "alice" if req.header("Authorization", "").removeprefix("Bearer ") == TOKENS["alice"] else None
    if not who:
        return js({"error": "bad token"}, 401)
    body = req.json() or {}
    to, amount = str(body.get("to", "")), int(body.get("amount", 0))
    if to not in BALANCES or amount <= 0:
        return js({"error": "bad transfer"}, 400)

    # The bug: read, think, compare, then write. Between the read and the write
    # the row still holds the old number, so every request that arrives inside
    # that window reads 100, decides 100 is enough, and pays out.
    have = BALANCES[who]
    # Deliberately generous: a real window is often single-digit milliseconds,
    # and a lab that reproduces half the time teaches nothing about the bug.
    time.sleep(0.25)                      # a lookup, a fraud check, an audit write
    if have < amount:
        return js({"error": "insufficient funds", "balance": have}, 402)
    BALANCES[who] = have - amount
    BALANCES[to] += amount
    return js({"ok": True, "from": who, "to": to, "amount": amount})


@app.get("/api/rewards")
def rewards(req):
    # 500 out of an account that only ever held 100 is unambiguous evidence;
    # it does not need every send in the burst to land in the window.
    if BALANCES["vault"] < 500:
        return js({"vault": BALANCES["vault"], "need": 500}, 402)
    return js({"vault": BALANCES["vault"], "prize": FLAG})


if __name__ == "__main__":
    serve(app, 9350)
