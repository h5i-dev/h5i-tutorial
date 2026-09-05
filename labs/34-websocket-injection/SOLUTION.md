# Lab 34 — Fleet console

## The bug

```python
host = str(msg.get("host", ""))
subprocess.run(["/bin/sh", "-c", f"echo probing {host}"], cwd=ROOT)
```

Identical to Lab 16. What is different is where the input arrived from — and
that difference is entirely social. A query parameter gets reviewed, fuzzed, and
put behind a WAF. A WebSocket frame is "the app talking to itself", so it gets
none of those, which is why command injection over a socket outlives the same
bug over HTTP.

**Everything that is input over HTTP is input over WebSocket**: injection,
authorization (is each frame authorised, or only the handshake?), IDOR, rate
limits, CSRF on the handshake — see below.

## Speaking to the socket

Until you can send a frame, an application whose commands travel over a
WebSocket is one you can watch connect and never talk to.

```bash
h5i browser open http://127.0.0.1:9340/ --session lab34 --new --capture --allow 127.0.0.1

# learn the protocol from a frame that is meant to work
h5i websec socket ws://127.0.0.1:9341/control --session lab34 --send '{"action":"status"}'

# then the same frame with a semicolon in it
h5i websec socket ws://127.0.0.1:9341/control --session lab34 \
    --send '{"action":"ping","host":"10.0.0.1; cat fleet.key"}' --wait-ms 3000
```

`websec socket` is `replay` for the other protocol: the *agent's* own frame,
through the same policy, budget and receipts, on a session running no page
script at all. It opens, sends what it was given in order, listens for
`--wait-ms`, and closes.

`--wait-ms` matters more than it looks. A server that answers by *doing*
something first — running a command, waiting on a device — answers late, and a
socket that says nothing at all is a result rather than an error. Raise it
before concluding a payload failed.

## Reconnaissance on a socket protocol

There is no OpenAPI document. Build the message vocabulary from:

1. The page's own JavaScript — it contains every message the client can send.
   `h5i websec show res_N --raw` on the script bundle, then grep for `send(`.
2. Watching a real session's frames.
3. Error replies: `{"error":"unknown action"}` invites enumeration.
4. Guessing the REST equivalents — `list`, `get`, `create`, `delete`, `admin`.

Then, for each message, ask the ordinary questions: which fields reach a shell,
a query, a path, a template; which actions check authorization per frame and
which trusted the handshake.

## The authorization trap

Most WebSocket applications authenticate **once**, at the handshake, and then
treat the connection as a session. Two consequences:

* **Per-message authorization is often missing entirely.** If `{"action":"ping"}`
  is allowed, try `{"action":"delete_node","id":1}` on the same socket.
* **Cross-site WebSocket hijacking.** The handshake is a plain HTTP request that
  carries cookies and is *not* subject to the same-origin policy. If the server
  does not check `Origin`, an attacker's page can open an authenticated socket
  as the victim and read everything on it. Test it with
  `--set header.Origin=http://evil.example` on the handshake.

## The fix

* Never build a shell string. `subprocess.run(["ping", "-c", "1", host])`, and
  validate `host` as an address or hostname (Lab 16).
* Authorise every message, not the connection.
* Check `Origin` on the handshake against an allowlist, and use a token in the
  first frame rather than relying on the cookie.
* Rate-limit and size-limit frames.

## h5i technique

`h5i websec socket URL --send FRAME --send FRAME --wait-ms MS`. Repeatable
`--send`, sent in order, so a protocol needing a hello frame before a command
frame is one exchange rather than a script.
