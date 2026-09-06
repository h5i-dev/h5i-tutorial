#!/usr/bin/env python3
"""Lab 36 — Checkout. Every field validated, and the rule never written down."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("checkout")

PRICES = {"sticker": 3, "tshirt": 25, "enterprise-license": 4900}
COUPONS = {"WELCOME10": 10, "SPRING15": 15, "FRIEND25": 25}
CREDIT = 20


@app.get("/")
def index(req):
    return html("<h1>Checkout</h1>"
                f"<p>Items: {', '.join(f'{k} ({v})' for k, v in PRICES.items())}</p>"
                f"<p>Coupons: {', '.join(f'{k} −{v}%' for k, v in COUPONS.items())}. "
                "The basket page lets you apply one.</p>"
                f"<p>You have {CREDIT} in store credit.</p>"
                '<p><code>POST /api/checkout {"item","coupons":[…]}</code></p>')


@app.post("/api/checkout")
def checkout(req):
    body = req.json() or {}
    item = str(body.get("item", ""))
    coupons = body.get("coupons", [])
    if item not in PRICES:
        return js({"error": "no such item"}, 404)
    if not isinstance(coupons, list):
        return js({"error": "coupons must be a list"}, 400)
    for code in coupons:
        if code not in COUPONS:
            # Each coupon is validated. Every individual field is fine.
            return js({"error": "unknown coupon", "code": code}, 400)

    # The bug: the discounts are summed. Nothing says a coupon may be used once,
    # nothing caps the total, and nothing stops the result going below zero.
    percent = sum(COUPONS[c] for c in coupons)
    total = PRICES[item] * (100 - percent) // 100
    if total > CREDIT:
        return js({"error": "insufficient credit", "total": total}, 402)
    receipt = {"item": item, "discount_percent": percent, "paid": total}
    if item == "enterprise-license":
        receipt["license_key"] = FLAG
    return js(receipt)


if __name__ == "__main__":
    serve(app, 9360)
