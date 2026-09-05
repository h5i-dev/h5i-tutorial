#!/usr/bin/env python3
"""Lab 16 — Logdesk. A shell string is a program the user finishes writing."""
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("logdesk")

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab16-"))
(ROOT / "app.log").write_text(
    "2026-04-01 INFO  boot ok\n2026-04-01 WARN  disk 81%\n2026-04-02 ERROR upstream timeout\n"
)
# Out of the web root, readable by the service account, which is the usual
# arrangement and the usual mistake.
(ROOT / "deploy.key").write_text(f"passphrase={FLAG}\n")

BANNED = ["&&", "||", "|", ">", "<", "`", "$("]


@app.get("/")
def index(req):
    return html('<h1>Logdesk</h1><form action="/api/logs/search">'
                '<input name="q" value="ERROR"><button>grep</button></form>'
                "<p>Searches <code>app.log</code> in the service working directory. Shell metacharacters are filtered.</p>")


@app.get("/api/logs/search")
def search(req):
    q = req.query.get("q", "")
    for bad in BANNED:
        # A blocklist: it stops the operators the author thought of.
        if bad in q:
            return js({"error": "blocked", "token": bad}, 400)
    # The bug: the pattern is pasted into a shell command. The single quotes
    # look like containment and are themselves just characters in the string.
    cmd = f"grep -n '{q}' app.log"
    out = subprocess.run(["/bin/sh", "-c", cmd], capture_output=True, timeout=5, cwd=ROOT)
    return text((out.stdout + out.stderr).decode("utf-8", "replace") or "(no matches)")


if __name__ == "__main__":
    serve(app, 9160)
