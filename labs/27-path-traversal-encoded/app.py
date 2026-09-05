#!/usr/bin/env python3
"""Lab 27 — Docs. The filter runs before the last decode."""
import pathlib
import sys
import tempfile
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, App as _, html, js, serve, text

app = App("docs")

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab27-"))
(ROOT / "pages").mkdir()
(ROOT / "secret").mkdir()
(ROOT / "pages" / "welcome.md").write_text("# Welcome\nNothing to see.\n")
(ROOT / "pages" / "changelog.md").write_text("# Changelog\n- 3.1 hardened /download\n")
(ROOT / "secret" / "flag.txt").write_text(f"{FLAG}\n")


@app.get("/")
def index(req):
    return html('<h1>Docs</h1><p><a href="/download?file=welcome.md">welcome.md</a> · '
                '<a href="/download?file=changelog.md">changelog.md</a></p>'
                "<p><code>../</code> is stripped from the filename.</p>")


@app.get("/download")
def download(req):
    name = req.query.get("file", "")
    # The bug is the order. The filter looks for `../` in a string that has been
    # decoded once, and then the code decodes it a second time — so a payload
    # that is not yet `../` when the filter reads it becomes `../` afterwards.
    name = name.replace("../", "")
    name = urllib.parse.unquote(name)
    target = ROOT / "pages" / name
    try:
        return text(target.read_text())
    except Exception as err:
        return js({"error": type(err).__name__, "asked_for": str(target)}, 404)


if __name__ == "__main__":
    serve(app, 9270)
