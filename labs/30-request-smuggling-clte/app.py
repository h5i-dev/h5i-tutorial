#!/usr/bin/env python3
"""Lab 30 — Frontdoor. Two servers, one connection, two opinions about where a
request ends.

Written with raw sockets rather than the lab framework because the whole point
is the framing, and a framework is a thing that hides framing.
"""
import os
import socket
import socketserver
import sys
import threading

FLAG = os.environ.get("FLAG", "FLAG{request_smuggling_clte}")
BACKEND = ("127.0.0.1", 9301)


def read_head(sock) -> bytes:
    """Bytes up to and including the blank line."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        chunk = sock.recv(1)
        if not chunk:
            return buf
        buf += chunk
    return buf


def headers_of(head: bytes) -> dict[str, str]:
    out = {}
    for line in head.split(b"\r\n")[1:]:
        if b":" in line:
            k, _, v = line.partition(b":")
            out[k.decode().strip().lower()] = v.decode().strip()
    return out


def read_chunked(sock) -> bytes:
    body = b""
    while True:
        size_line = b""
        while not size_line.endswith(b"\r\n"):
            byte = sock.recv(1)
            if not byte:
                return body
            size_line += byte
        size = int(size_line.strip().split(b";")[0] or b"0", 16)
        body += size_line
        if size == 0:
            body += sock.recv(2)          # the final CRLF
            return body
        body += sock.recv(size) + sock.recv(2)


class Backend(socketserver.StreamRequestHandler):
    """Prefers Transfer-Encoding when both framing headers are present."""

    def handle(self):
        self.connection.settimeout(10)
        while True:
            head = read_head(self.connection)
            if not head:
                return
            hdrs = headers_of(head)
            line = head.split(b"\r\n")[0].decode(errors="replace")
            try:
                method, target, _ = line.split(" ", 2)
            except ValueError:
                return
            # The disagreement: this server reads `Transfer-Encoding` and
            # ignores `Content-Length` when both are present. RFC 9112 says to
            # do exactly this — and to reject the message instead, which is the
            # part that gets skipped.
            if "chunked" in hdrs.get("transfer-encoding", "").lower():
                read_chunked(self.connection)
            elif hdrs.get("content-length"):
                self.connection.recv(int(hdrs["content-length"]))

            if target.startswith("/admin/"):
                body = f'{{"flag": "{FLAG}"}}'.encode()
            elif target == "/health":
                body = b'{"ok": true}'
            else:
                body = f'{{"seen": "{method} {target}"}}'.encode()
            self.connection.sendall(
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
                + f"Content-Length: {len(body)}\r\n\r\n".encode() + body
            )


class Proxy(socketserver.StreamRequestHandler):
    """Blocks /admin/*. Decides where a request ends by Content-Length."""

    def handle(self):
        self.connection.settimeout(10)
        upstream = socket.create_connection(BACKEND, timeout=10)
        try:
            while True:
                head = read_head(self.connection)
                if not head:
                    return
                hdrs = headers_of(head)
                target = head.split(b"\r\n")[0].split(b" ")[1].decode(errors="replace")
                # The bug is not this line. This line is the *control*: it is
                # correct about the request it can see.
                if target.startswith("/admin"):
                    body = b'{"error": "blocked by the edge"}'
                    self.connection.sendall(
                        b"HTTP/1.1 403 Forbidden\r\nContent-Type: application/json\r\n"
                        + f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
                    continue
                # The bug: `Content-Length` decides where this request ends, and
                # the server downstream will decide differently.
                length = int(hdrs.get("content-length") or 0)
                payload = self.connection.recv(length) if length else b""
                upstream.sendall(head + payload)

                # Relay everything the backend says, not just the first message.
                upstream.settimeout(0.6)
                out = b""
                try:
                    while True:
                        chunk = upstream.recv(65536)
                        if not chunk:
                            break
                        out += chunk
                except socket.timeout:
                    pass
                if not out:
                    return
                self.connection.sendall(out)
        finally:
            upstream.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    threading.Thread(target=Server(BACKEND, Backend).serve_forever, daemon=True).start()
    print("  frontdoor listening on http://127.0.0.1:9300", flush=True)
    Server(("127.0.0.1", 9300), Proxy).serve_forever()
