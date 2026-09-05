#!/usr/bin/env python3
"""Lab 29 — Wiki. A file read plus a renderer is code execution."""
import pathlib
import re
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("wiki")

RELEASE_KEY = FLAG          # a module global, like any app's config
ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab29-"))
(ROOT / "pages").mkdir()
(ROOT / "pages" / "home.md").write_text("# Home\nWelcome to the wiki. Hello {{page}}.\n")
LOG = ROOT / "access.log"
LOG.write_text("")


class Page:
    def __init__(self, name: str):
        self.name = name


def render(template: str, env: dict) -> str:
    """The same three-line engine as Lab 17: `{{ … }}` is evaluated."""
    def one(m):
        try:
            return str(eval(m.group(1).strip(), {"__builtins__": {}}, env))
        except Exception as err:
            return f"[{type(err).__name__}]"

    return re.sub(r"\{\{(.*?)\}\}", one, template)


@app.any("(?!/favicon).*")
def catch_all(req):
    # Every request is logged, User-Agent and all. Ordinary, and the reason
    # this lab has a second half.
    LOG.open("a").write(f'{req.client} "{req.method} {req.raw_path}" "{req.header("User-Agent")}"\n')

    if req.path == "/":
        return html('<h1>Wiki</h1><p><a href="/view?page=home.md">home.md</a></p>'
                    "<p>Pages live in <code>pages/</code> and are rendered as templates.</p>")
    if req.path != "/view":
        return js({"error": "not found"}, 404)

    name = req.query.get("page", "home.md")
    # The bug: the path is joined without containment, so any file on the host
    # can be read — and it is read *as a template*, so any file whose contents
    # an attacker influences is a file whose contents get evaluated.
    try:
        raw = (ROOT / "pages" / name).read_text(errors="replace")
    except Exception as err:
        return js({"error": type(err).__name__, "asked_for": str(ROOT / "pages" / name)}, 404)
    return text(render(raw, {"page": Page(name)}))


if __name__ == "__main__":
    serve(app, 9290)
