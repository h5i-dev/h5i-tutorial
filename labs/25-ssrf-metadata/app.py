#!/usr/bin/env python3
"""Lab 25 — Linkpreview. The server is a browser sitting inside the perimeter."""
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve, text

app = App("linkpreview")
metadata = App("metadata-service")


@app.get("/")
def index(req):
    return html('<h1>Link preview</h1><p>'
                '<a href="/api/preview?url=http://example.com/">/api/preview?url=</a> '
                "fetches a page and reports what it found.</p>")


@app.get("/api/preview")
def preview(req):
    url = req.query.get("url", "")
    # The bug: a URL from a stranger, fetched by a process that sits inside the
    # network and holds credentials the stranger does not.
    try:
        with urllib.request.urlopen(url, timeout=4) as answer:
            body = answer.read(4096).decode("utf-8", "replace")
            return js({"url": url, "status": answer.status, "body": body})
    except urllib.error.HTTPError as err:
        return js({"url": url, "status": err.code, "body": err.read(2048).decode("utf-8", "replace")})
    except Exception as err:
        return js({"url": url, "error": type(err).__name__, "detail": str(err)}, 502)


@metadata.get("/")
def meta_root(req):
    return text("latest/\n")


@metadata.get("/latest/meta-data/")
def meta_index(req):
    return text("instance-id\niam/\n")


@metadata.get("/latest/meta-data/iam/security-credentials/")
def role_list(req):
    return text("linkpreview-role\n")


@metadata.get("/latest/meta-data/iam/security-credentials/linkpreview-role")
def role(req):
    return js({"AccessKeyId": "AKIAEXAMPLE", "SecretAccessKey": FLAG, "Type": "AWS-HMAC"})


if __name__ == "__main__":
    from lib.miniweb import serve as run
    serve(metadata, 9251, background=True)
    run(app, 9250)
