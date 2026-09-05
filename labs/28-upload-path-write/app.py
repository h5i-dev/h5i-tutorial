#!/usr/bin/env python3
"""Lab 28 — Avatars. The magic bytes are checked; the name is obeyed."""
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("avatars")

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab28-"))
(ROOT / "uploads").mkdir()
(ROOT / "config").mkdir()
# Read fresh on every admin request, which is what makes it a target.
(ROOT / "config" / "trusted_keys.txt").write_text("k-ops-1\nk-ops-2\n")


@app.get("/")
def index(req):
    return html("<h1>Avatars</h1>"
                "<p><code>POST /api/avatar</code> (multipart, part name <code>file</code>). "
                "JPEG only — the first bytes are checked.</p>"
                "<p><code>GET /api/admin/flag</code> with header "
                "<code>X-Api-Key</code>; keys are read from "
                "<code>config/trusted_keys.txt</code> on every request.</p>")


@app.post("/api/avatar")
def upload(req):
    part = req.multipart().get("file")
    if not part:
        return js({"error": "part `file` required"}, 400)
    data = part["data"]
    # The check the team is proud of: content sniffing, not extension checking.
    if not data.startswith(b"\xff\xd8\xff"):
        return js({"error": "not a JPEG", "first_bytes": data[:4].hex()}, 400)
    # The bug: the *name* is taken from the client and joined onto a directory.
    # A content check says nothing about where the content is written.
    target = ROOT / "uploads" / (part["filename"] or "avatar.jpg")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return js({"stored": str(target), "bytes": len(data)})


@app.get("/api/admin/flag")
def admin(req):
    keys = (ROOT / "config" / "trusted_keys.txt").read_text(errors="replace").split()
    if req.header("X-Api-Key") not in keys:
        return js({"error": "unknown api key"}, 403)
    return js({"flag": FLAG})


if __name__ == "__main__":
    serve(app, 9280)
