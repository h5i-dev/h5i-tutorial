#!/usr/bin/env python3
"""Lab 18 — Avatar. An XML parser is a file client you did not know you shipped."""
import io
import pathlib
import sys
import tempfile
import xml.sax
from xml.sax.handler import feature_external_ges

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("avatar")

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab18-"))
(ROOT / "service.env").write_text(f"S3_SECRET={FLAG}\n")


class Collect(xml.sax.ContentHandler):
    def __init__(self):
        self.chunks: list[str] = []

    def characters(self, data):
        self.chunks.append(data)


@app.get("/")
def index(req):
    return html('<h1>Avatar</h1><form method="POST" action="/api/avatar" '
                'enctype="multipart/form-data">'
                '<input type="file" name="file"><button>upload</button></form>'
                f"<p>SVG only. Config lives in <code>{ROOT}/service.env</code>.</p>")


@app.post("/api/avatar")
def upload(req):
    part = req.multipart().get("file")
    if not part:
        return js({"error": "file part required"}, 400)
    data = part["data"]
    if b"<svg" not in data:
        return js({"error": "SVG only"}, 400)
    handler = Collect()
    parser = xml.sax.make_parser()
    # The bug: external general entities are switched on. The parser will now
    # fetch whatever a document's DOCTYPE tells it to, and the document comes
    # from a stranger.
    parser.setFeature(feature_external_ges, True)
    parser.setContentHandler(handler)
    try:
        parser.parse(io.BytesIO(data))
    except Exception as err:
        return js({"error": type(err).__name__, "detail": str(err)}, 400)
    return js({"accepted": True, "bytes": len(data), "title": "".join(handler.chunks).strip()})


if __name__ == "__main__":
    serve(app, 9180)
