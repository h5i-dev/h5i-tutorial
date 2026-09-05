"""An "admin who clicks the link", built out of h5i itself.

Several labs need a victim: a privileged user whose browser visits a URL, runs
whatever script is on the page, and carries a session cookie while doing it.
Rather than mock one, these labs drive a real h5i browser — the same engine you
are attacking the lab with, on the other side of the exploit.

    bot = Bot(login_url="http://127.0.0.1:9200/internal/login?t=SECRET")
    bot.visit("http://127.0.0.1:9200/search?q=<payload>")

Each visit is a fresh session: open the login URL (which sets the victim's
cookie), navigate to the target with scripts enabled, close.
"""

from __future__ import annotations

import os
import queue
import secrets
import subprocess
import threading
import time

H5I = os.environ.get("H5I", "h5i")


class Bot:
    def __init__(self, login_url: str, allow: str = "127.0.0.1", quiet: bool = True):
        self.login_url = login_url
        self.allow = allow
        self.quiet = quiet
        self.queue: queue.Queue[str] = queue.Queue()
        self.visited: list[str] = []
        threading.Thread(target=self._loop, daemon=True).start()

    def visit(self, url: str) -> None:
        """Queue a URL. Returns immediately, like a real "report to admin"."""
        self.queue.put(url)

    def _run(self, *args: str) -> None:
        subprocess.run(
            [H5I, "browser", *args],
            stdout=subprocess.DEVNULL if self.quiet else None,
            stderr=subprocess.DEVNULL if self.quiet else None,
            timeout=45,
        )

    def _loop(self) -> None:
        while True:
            url = self.queue.get()
            session = f"victim-{secrets.token_hex(4)}"
            try:
                self._run("open", self.login_url, "--session", session,
                          "--new", "--script", "--allow", self.allow)
                self._run("navigate", url, "--session", session)
                time.sleep(0.5)          # let the page's own fetches finish
                self.visited.append(url)
            except Exception:
                pass
            finally:
                try:
                    self._run("close", "--session", session)
                except Exception:
                    pass


class Collector:
    """Somewhere for an exfiltrated value to land.

    On a real engagement this is a host you own. Here it is two endpoints on the
    lab itself, keyed by a token you choose, so the lab needs no second machine.
    """

    def __init__(self):
        self.rows: dict[str, list[str]] = {}
        self.lock = threading.Lock()

    def put(self, key: str, value: str) -> None:
        with self.lock:
            self.rows.setdefault(key, []).append(value)

    def get(self, key: str) -> list[str]:
        with self.lock:
            return list(self.rows.get(key, []))
