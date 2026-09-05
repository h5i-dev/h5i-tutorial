#!/usr/bin/env python3
"""Lab 17 — Postcard. Rendering user input as a template hands over the runtime."""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("postcard")

VAULT_KEY = FLAG  # a module global, like every real app's config


class User:
    def __init__(self, name: str):
        self.name = name
        self.plan = "free"


def render(template: str, env: dict) -> str:
    """A template engine in three lines. Every real one is this plus a sandbox,
    and the interesting part of the exploit is what the sandbox forgot."""
    def one(m):
        try:
            return str(eval(m.group(1).strip(), {"__builtins__": {}}, env))
        except Exception as err:
            return f"[{type(err).__name__}: {err}]"

    return re.sub(r"\{\{(.*?)\}\}", one, template)


@app.get("/")
def index(req):
    return html('<h1>Postcard</h1><p>Preview a greeting: '
                '<a href="/api/preview?tpl=Hello%20{{user.name}}!">'
                "/api/preview?tpl=Hello {{user.name}}!</a></p>")


@app.get("/api/preview")
def preview(req):
    tpl = req.query.get("tpl", "Hello {{user.name}}!")
    # The bug: the *template* comes from the request. Escaping the value would
    # have been fine; the value is the program.
    return js({"preview": render(tpl, {"user": User("guest")})})


if __name__ == "__main__":
    serve(app, 9170)
