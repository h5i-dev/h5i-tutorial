#!/usr/bin/env python3
"""Lab 34 — Fleet. Commands travel over a socket, and a socket is still input.

The WebSocket server is hand-rolled: handshake, one frame reader, one frame
writer. Roughly seventy lines, so that nothing about the protocol is hidden.
"""
import base64
import hashlib
import os
import pathlib
import socketserver
import struct
import subprocess
import sys
import tempfile
import threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from lib.miniweb import App, html, serve

FLAG = os.environ.get("FLAG", "FLAG{websocket_injection}")
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

ROOT = pathlib.Path(tempfile.mkdtemp(prefix="lab34-"))
(ROOT / "fleet.key").write_text(f"{FLAG}\n")

app = App("fleet")


@app.get("/")
def index(req):
    return html("<h1>Fleet console</h1>"
                "<p>The console speaks to <code>ws://127.0.0.1:9341/control</code>.</p>"
                '<p>Frames look like <code>{"action":"ping","host":"10.0.0.1"}</code> '
                'and <code>{"action":"status"}</code>.</p>')


def ws_read(sock) -> str | None:
    head = sock.recv(2)
    if len(head) < 2:
        return None
    length = head[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", sock.recv(2))[0]
    elif length == 127:
        length = struct.unpack(">Q", sock.recv(8))[0]
    mask = sock.recv(4) if head[1] & 0x80 else b"\0\0\0\0"
    data = b""
    while len(data) < length:
        data += sock.recv(length - len(data))
    return bytes(b ^ mask[i % 4] for i, b in enumerate(data)).decode("utf-8", "replace")


def ws_write(sock, text: str) -> None:
    raw = text.encode()
    if len(raw) < 126:
        header = struct.pack("!BB", 0x81, len(raw))
    else:
        header = struct.pack("!BBH", 0x81, 126, len(raw))
    sock.sendall(header + raw)


class Control(socketserver.StreamRequestHandler):
    def handle(self):
        head = b""
        while b"\r\n\r\n" not in head:
            byte = self.connection.recv(1)
            if not byte:
                return
            head += byte
        key = ""
        for line in head.split(b"\r\n"):
            if line.lower().startswith(b"sec-websocket-key:"):
                key = line.split(b":", 1)[1].decode().strip()
        accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        self.connection.sendall(
            f"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode())

        while True:
            frame = ws_read(self.connection)
            if frame is None:
                return
            import json
            try:
                msg = json.loads(frame)
            except Exception:
                ws_write(self.connection, '{"error":"bad frame"}')
                continue
            action = msg.get("action")
            if action == "status":
                ws_write(self.connection, '{"fleet":"12 nodes","state":"green"}')
            elif action == "ping":
                # The bug: the command is built by interpolation. That the input
                # arrived over a WebSocket rather than in a query string changes
                # nothing about whether it is trusted — but it does change how
                # many people ever look at it.
                host = str(msg.get("host", ""))
                out = subprocess.run(["/bin/sh", "-c", f"echo probing {host}"],
                                     capture_output=True, cwd=ROOT, timeout=5)
                ws_write(self.connection, (out.stdout + out.stderr).decode("utf-8", "replace"))
            else:
                ws_write(self.connection, '{"error":"unknown action"}')


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    threading.Thread(target=Server(("127.0.0.1", 9341), Control).serve_forever,
                     daemon=True).start()
    serve(app, 9340)
