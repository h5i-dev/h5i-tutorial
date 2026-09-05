#!/usr/bin/env python3
"""Lab 02 — Curio Shop. The price arrives in the request that pays it."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("curio-shop")
CATALOGUE = {"mug": 9, "poster": 15, "vault-key": 999999}


@app.get("/")
def index(req):
    rows = "".join(
        f"""<form method="POST" action="/buy">
              <input type="hidden" name="item" value="{item}">
              <input type="hidden" name="price" value="{price}">
              <input type="hidden" name="qty" value="1">
              <button>{item} — {price} credits</button>
            </form>"""
        for item, price in CATALOGUE.items()
        if item != "vault-key"
    )
    return html(f"<h1>Curio Shop</h1><p>Balance: 20 credits</p>{rows}")


@app.post("/buy")
def buy(req):
    form = req.form
    item = form.get("item", "")
    # The bug: `price` and `qty` are read from the request. The catalogue is
    # right there in the same process and is never consulted.
    try:
        total = int(form.get("price", "0")) * int(form.get("qty", "1"))
    except ValueError:
        return js({"error": "bad number"}, 400)
    if item not in CATALOGUE:
        return js({"error": "no such item"}, 404)
    if total > 20:
        return js({"error": "insufficient balance", "total": total}, 402)
    receipt = {"item": item, "paid": total, "status": "shipped"}
    if item == "vault-key":
        receipt["engraving"] = FLAG
    return js(receipt)


if __name__ == "__main__":
    serve(app, 9020)
