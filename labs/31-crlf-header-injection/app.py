#!/usr/bin/env python3
"""Lab 31 — Reports. A header value that can contain a newline is not a value."""
import pathlib
import socket
import socketserver
import sys
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import FLAG, App, html, js, serve

app = App("reports")
INTERNAL = ("127.0.0.1", 9311)


@app.get("/")
def index(req):
    return html("<h1>Reports</h1>"
                '<p><code>POST /api/report {"name"}</code> — asks the internal '
                "report service to render a report for you.</p>"
                "<p>The internal service decides your role; this front end always "
                "asks as <code>guest</code>.</p>")


@app.post("/api/report")
def report(req):
    name = str((req.json() or {}).get("name", "quarterly"))
    # The bug: `name` is interpolated into a header of a request this server
    # composes. A newline in the value ends the header and starts another one.
    raw = (
        f"GET /render HTTP/1.1\r\n"
        f"Host: reports.internal\r\n"
        f"X-Report-Name: {name}\r\n"
        f"X-Role: guest\r\n"
        f"Connection: close\r\n\r\n"
    )
    try:
        sock = socket.create_connection(INTERNAL, timeout=4)
        sock.sendall(raw.encode("utf-8", "replace"))
        answer = b""
        while chunk := sock.recv(65536):
            answer += chunk
        sock.close()
    except Exception as err:
        return js({"error": type(err).__name__, "detail": str(err)}, 502)
    return js({"sent": raw, "internal_response": answer.decode("utf-8", "replace")})


class Internal(socketserver.StreamRequestHandler):
    def handle(self):
        head = b""
        while b"\r\n\r\n" not in head:
            byte = self.connection.recv(1)
            if not byte:
                return
            head += byte
        headers = {}
        for line in head.split(b"\r\n")[1:]:
            if b":" in line:
                key, _, value = line.partition(b":")
                # Last occurrence wins, which is what a dict-building parser does
                # and what a great many real ones do.
                headers[key.decode(errors="replace").strip().lower()] = \
                    value.decode(errors="replace").strip()
        if headers.get("x-role") == "admin":
            body = f'{{"report": "all tenants", "signing_key": "{FLAG}"}}'.encode()
        else:
            body = b'{"report": "your tenant only"}'
        self.connection.sendall(
            b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
            + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    threading.Thread(target=Server(INTERNAL, Internal).serve_forever, daemon=True).start()
    serve(app, 9310)
