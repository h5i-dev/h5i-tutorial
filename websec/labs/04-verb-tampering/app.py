#!/usr/bin/env python3
"""Lab 04 — Payroll. The guard reads one verb; the router answers to all."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("payroll")

# A "middleware" written as a list of rules, the way frameworks really do it.
RULES = [
    # methods, path prefix, who may pass
    (("GET", "POST"), "/admin/", "admin"),
]


def allowed(req) -> bool:
    role = req.cookies.get("role", "staff")
    for methods, prefix, need in RULES:
        # The bug: the rule is keyed on method as well as path. Any verb the
        # rule does not list walks straight past it, and the router below
        # answers every verb it is given.
        if req.method in methods and req.path.startswith(prefix):
            return role == need
    return True


@app.get("/")
def index(req):
    return html('<h1>Payroll</h1><p>Restricted: <a href="/admin/payslips">/admin/payslips</a></p>')


@app.any("/admin/payslips")
def payslips(req):
    if not allowed(req):
        return js({"error": "admins only", "method_checked": req.method}, 403)
    return js({"payslips": 412, "signing_key": FLAG})


if __name__ == "__main__":
    serve(app, 9040)
