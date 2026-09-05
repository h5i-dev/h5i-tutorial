#!/usr/bin/env python3
"""Lab 42 — Meridian. Four ordinary mistakes, one chain."""
import pathlib
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("meridian")
ops = App("meridian-ops")

OPS_TOKEN = "ops_" + secrets.token_hex(10)
ACCOUNTS: dict[str, dict] = {}
BANNED = ["localhost", "127.0.0.1", "0.0.0.0", "::1", "internal", "ops."]


# ------------------------------------------------------------ public surface
@app.get("/")
def index(req):
    return html("<h1>Meridian</h1><p>Customer portal.</p>"
                '<p><a href="/api/v1/signup">/api/v1/signup</a> · '
                '<a href="/api/support/fetch">/api/support/fetch</a></p>')


@app.get("/robots.txt")
def robots(req):
    return text("User-agent: *\nDisallow: /internal/\nDisallow: /api/v0/\n")


@app.get("/internal/handover.md")
def handover(req):
    return text(
        "# Handover — platform team\n"
        "\n"
        "- v1 signup allowlists its fields. v0 does not; it is kept for the\n"
        "  mobile client and is gated behind `X-Api-Version: 0`.\n"
        "- Accounts carry `role`; `support` unlocks /api/support/fetch.\n"
        "- The ops service runs on port 9421 of this host. It is not exposed.\n"
        "- TODO: remove /debug/env from ops before the audit.\n"
    )


@app.post("/api/v1/signup")
def signup_v1(req):
    body = req.json() or {}
    if req.header("X-Api-Version") == "0":
        # Mistake 2: a deprecated handler that merges the body whole, still
        # mounted, reachable by a header anybody can send.
        row = {"user": str(body.get("user", "")), "role": "customer", **body}
    else:
        row = {"user": str(body.get("user", "")), "role": "customer"}
    if not row["user"]:
        return js({"error": "user required"}, 400)
    token = secrets.token_hex(12)
    ACCOUNTS[token] = row
    return js({"token": token, "role": row["role"]})


@app.get("/api/support/fetch")
def support_fetch(req):
    who = ACCOUNTS.get(req.header("Authorization", "").removeprefix("Bearer "), {})
    if who.get("role") != "support":
        return js({"error": "support role required", "your_role": who.get("role")}, 403)
    url = req.query.get("url", "")
    # Mistake 3: a blocklist of spellings in front of a resolver.
    for bad in BANNED:
        if bad in url.lower():
            return js({"error": "blocked", "matched": bad}, 400)
    try:
        with urllib.request.urlopen(url, timeout=4) as answer:
            return js({"status": answer.status,
                       "body": answer.read(4096).decode("utf-8", "replace")})
    except urllib.error.HTTPError as err:
        return js({"status": err.code, "body": err.read(2048).decode("utf-8", "replace")})
    except Exception as err:
        return js({"error": type(err).__name__, "detail": str(err)}, 502)


# --------------------------------------------------------------- ops service
@ops.get("/")
def ops_root(req):
    return text("meridian ops\n/status\n/debug/env\n/vault?token=\n")


@ops.get("/status")
def ops_status(req):
    return js({"ok": True, "vault": "GET /vault?token=<OPS_TOKEN>"})


@ops.get("/debug/env")
def ops_env(req):
    # Mistake 4: a debug endpoint that outlived the debugging.
    return js({"NODE_ENV": "production", "OPS_TOKEN": OPS_TOKEN, "REGION": "eu-west-1"})


@ops.get("/vault")
def ops_vault(req):
    if req.query.get("token") != OPS_TOKEN:
        return js({"error": "bad ops token"}, 403)
    return js({"vault": "open", "root_credential": FLAG})


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(ops, 9421, background=True)
    run(app, 9420)
