# 1. The workbench

> Burp Suite is an HTTP workbench for humans. `h5i websec` is an HTTP workbench
> for scripts and agents.

This chapter is the tool. Read it once before Lab 01, and come back to the
tables.

---

## 1.1 The idea

h5i's engine **is** the browser's HTTP client. So there is no proxy to
configure, no CA certificate to install, and no gap between "what the browser
did" and "what was recorded". A session opened with `--capture` stores every
message it sent and received, each with a stable id, and any of them can be sent
again with one part changed.

That gives you the loop the whole book runs on:

```
    open --capture  →  read the record  →  replay one thing changed  →  compare
         ↑                                                                │
         └────────────────────────  and again  ─────────────────────────┘
```

Two properties of that loop matter more than any individual flag.

**One thing changed.** A replay sends the stored request with exactly the edits
you named and nothing else — same headers, same cookies, same identity. That is
what makes a difference in the answer *evidence* rather than a coincidence.

**Everything is written down.** A replay is a request like any other: it gets
its own sequence number and its own stored message, so a replay is itself
replayable and the whole chain is in the audit. When you finish, the
reproduction already exists.

---

## 1.2 Opening a session

```bash
h5i browser open http://target.example/ --session work --new --capture
```

| Flag | Why |
| --- | --- |
| `--session NAME` | name it, so you can hold several identities at once |
| `--new` | a fresh session rather than reusing one under that name |
| `--capture` | **required** — without it there is nothing to replay |
| `--allow HOST` | grant an origin the page does not grant itself (a second service, your collector) |
| `--script` | run page JavaScript (off by default; needed when you *are* the victim) |
| `--identity NAME` | present a coherent browser identity |
| `--in BOX` | place the session inside a sandbox |

Other verbs on the browser side that pay for themselves during recon:

```bash
h5i browser snapshot   --session work    # the page as elements, with @ref handles
h5i browser markdown   --session work    # the page as readable prose
h5i browser navigate   URL --session work
h5i browser click  @e3 --session work
h5i browser type   @e5 "serde" --session work
h5i browser requests   --session work    # allowed *and denied* fetches
h5i browser close      --session work
```

`h5i browser requests` differs from `h5i websec requests` in one useful way: it
shows what the **policy refused**, which is how you notice that your payload
never left.

---

## 1.3 Reading the record

```bash
h5i websec requests --session work                 # JSON, for a loop
h5i websec requests --session work --human         # a table, for you
h5i websec requests --session work --method POST
h5i websec requests --session work --status 500
h5i websec requests --session work --url-contains /api/
h5i websec requests --session work --initiator navigation   # or subresource, frame, redirect, replay
h5i websec requests --session work --denied-only
h5i websec requests --session work --limit 20
h5i websec sitemap  --session work --human         # origins and endpoints reached
```

Message ids: **`req_42`** is the request half, **`res_42`** the response half,
and **`42`** means "that exchange". Anything else is refused rather than parsed
as far as it goes — `42x` silently becoming 42 is how a loop tests the wrong
request.

```bash
h5i websec show req_42 --session work --raw            # the bytes, as sent
h5i websec show res_42 --session work --raw            # the bytes, as received
h5i websec show res_42 --session work --body-to out.bin  # the body, exactly
```

`--raw` is the one output here that is not JSON, because a wire message is bytes
and bytes inside a JSON string are no longer the message. Use `--body-to`
whenever the bytes must be exact: PEM keys (Lab 11), images (Lab 28), anything
you will re-upload or HMAC.

**Every verb here emits JSON by default**, because the caller is usually a loop.
`--human` gives the reading version.

---

## 1.4 Replay: the verb you will type most

```bash
h5i websec replay req_42 --session work --set query.id=456
```

### The `--set` targets, in full

| Target | Edits | Example |
| --- | --- | --- |
| `method=` | the method | `--set method=PUT` |
| `url=` | the whole URL | `--set url=http://other.example/x` |
| `path=` | the path, keeping the query | `--set path=/admin/flag` |
| `query.<name>=` | one query parameter | `--set query.level=internal` |
| `header.<name>=` | one header (replaces every copy) | `--set header.X-Real-IP=1.2.3.4` |
| `cookie.<name>=` | one cookie inside `Cookie` | `--set cookie.session=forged` |
| `json.<dotted.path>=` | one JSON field | `--set json.user.role=admin`, `--set json.items.0.id=7` |
| `form.<name>=` | one urlencoded field | `--set form.price=0` |
| `multipart.<part>=` | a part's bytes | `--set multipart.file=hello` |
| `multipart.<part>.filename=` | the declared filename | `--set multipart.file.filename=../x` |
| `multipart.<part>.content-type=` | the declared type | `--set multipart.file.content-type=image/jpeg` |
| `body.raw=` | the whole body | `--set body.raw='{"a":1}'` |

Two rules that save hours:

* **The value is everything after the first `=`.** A payload full of `=` needs no
  escaping.
* **A value that parses as JSON is sent as JSON.** `json.admin=true` is a
  boolean; `json.p={"$gt":""}` is an object (Lab 15); `json.tags=["a","b"]` is an
  array (Lab 36). To send the *string* `"true"`, write `json.admin="true"`.

`--set path=/x?y=1` is **refused**, naming `url=` and `query.y=` instead — a
query string inside `path` would be percent-encoded into a filename containing a
question mark, and a 404 that says nothing about what you asked for.

### The other replay flags

| Flag | What it is for |
| --- | --- |
| `--create` | add a target that is not in the stored request. Off by default: a parameter that does not exist is usually a typo. |
| `--unset TARGET` | remove one |
| `--set-file TARGET=PATH` | the value is the file's **bytes**, unaltered — for JPEGs, polyglots, anything not text. Applied after every `--set`. |
| `--as SESSION` | send this message from another session's cookie jar and identity — the authorization test in one flag (Lab 08) |
| `--keep-credentials` | with `--as`, carry the source session's `Cookie` and `Authorization` too |
| `--repeat N` | send it N times and report the clock: every sample, a median, and a median absolute deviation (Lab 14) |
| `--race` | release the repeats together, from threads that meet at a barrier (Lab 35) |
| `--no-follow` | stop at the first redirect and report it — where auth flows and open redirects live (Lab 24) |
| `--reset-budget` | restart the page's network allowance. **Any loop of more than a handful of replays needs this** (Lab 06). |
| `--raw-target TARGET` | write the request-target byte for byte, around the URL parser (Lab 27) |
| `--raw-request PATH` | send a whole message from a file, framing headers recomputed by nothing; `-` reads stdin (Lab 30) |

### What a replay answers with

```json
{"ok": true, "seq": 7,
 "applied": [{"target": "query.level", "value": "internal", "was": "public"}],
 "sent": {"method": "GET", "url": "…", "header_names": [...], "body_bytes": 0},
 "samples": [{"seq": 7, "status": 200, "ttfb_ms": 1, "total_ms": 2, "bytes": 26}],
 "response": {"status": 200, "headers": [...], "bytes": 26, "error": null}}
```

Note what is **not** there: the body. That is right for a verb that may have
just pulled down a database dump. When you want the body, name the message the
replay created:

```bash
SEQ=$(h5i websec replay req_0 --session work --set … | jq -r .seq)
h5i websec show "res_$SEQ" --session work --raw
```

That two-call pattern is the `send` helper in `labs/lib/h5i.sh`, and it is the
single most useful thing to keep in your own toolbox.

Read `applied` when a payload does not behave: it says what changed and what it
was before. Read `samples[].total_ms` for timing (Lab 14). Read
`response.status` and `response.bytes` in a sweep, so a hundred probes cost you
two numbers each instead of a hundred bodies (Labs 06, 13).

---

## 1.5 Comparing and asserting

```bash
h5i websec diff res_1 res_2 --session work --human
```

```
  status   : 200 → 200
  bytes    : 17 → 26 (+9)
  alike    : 0.000
  ~ header : content-length
  ~ flag : (absent) → FLAG{…}
  ~ user : guest → (absent)
```

`diff` states the difference — status, size, headers, changed JSON fields —
instead of asking you to spot it. It is the primary instrument for anything
where the finding *is* a difference: cache poisoning (Lab 33), unkeyed inputs,
authorization matrices, boolean oracles.

```bash
h5i websec match res_2 --session work --status 200 --contains FLAG{
```

`match` exits **0** when the condition holds, **1** when it does not, and **2**
when it could not be asked — three states, so a script can tell "no" from
"broken". Conditions: `--status`, `--contains`, `--regex`, `--json-path
PATH[=VALUE]`, `--header NAME[=VALUE]`, `--longer-than`, `--shorter-than`.

---

## 1.6 Sequences

A single replay cannot test an endpoint whose token is minted by the request
before it. Hand-carrying the token between two shell commands is where the
mistakes happen.

```json
{"steps": [
  {"name": "log in", "resend": 0, "create": true,
   "set": ["method=POST", "path=/api/login",
           "header.Content-Type=application/json",
           "json.user=${user}", "json.password=${password}"]},
  {"name": "take the token", "resend": 0, "create": true,
   "set": ["path=/account/settings"],
   "extract": {"csrf": "regex:name=\"csrf\" value=\"([^\"]+)\""}},
  {"name": "post with it", "resend": 0, "create": true,
   "set": ["method=POST", "path=/account/settings",
           "form.csrf=${csrf}", "form.role=admin"]}
]}
```

```bash
h5i websec sequence flow.json --session work --var user=guest --var password=guest
```

* Extractors: `regex:` (first capture group), `json:` (dotted path), `header:`,
  `status`.
* `${name}` substitutes what an earlier step bound. **An unbound name stops the
  sequence** rather than becoming an empty string — a request that goes out with
  `csrf=` gets a 403 that looks exactly like the finding you are hunting for.
* Steps stop at the first failure; `--keep-going` runs them all.
* The cookie jar is the session's, so `Set-Cookie` propagates for free.

Lab 41 is the worked example. A sequence file is also a good artefact to put in
a report: it is a reproduction somebody else can run.

---

## 1.7 Sockets

```bash
h5i websec socket ws://target.example/control --session work \
    --send '{"action":"status"}' \
    --send '{"action":"ping","host":"127.0.0.1; id"}' --wait-ms 3000
```

`socket` is `replay` for the other protocol: your own frame, through the same
policy, budget and receipts, on a session running no page script at all. It
opens, sends what it was given in order, listens for `--wait-ms`, and closes.

Raise `--wait-ms` before concluding a payload failed: a server that answers by
*doing* something first answers late, and a socket that says nothing is a result
rather than an error. Lab 34.

---

## 1.8 The two flags people forget

**`--reset-budget`.** Each page has a bounded network allowance, there to
contain page code — a script in a loop is the untrusted thing it stops. A
deliberate sweep is the opposite. Without this flag a long loop stops partway and
every later probe reads as a negative result, which is the worst way for a test
to fail: silently, as evidence of absence.

**`--create`.** Adding a field the captured request never had is a thing you
must say out loud, because the alternative — typos silently succeeding — costs a
whole turn reading a response that was never going to differ.

---

## 1.9 A worked minute

```bash
h5i browser open 'http://target.example/api/report?id=7' --session work --new --capture
h5i websec requests --session work --human
h5i websec show res_0 --session work --raw

h5i websec replay req_0 --session work --set query.id=8
h5i websec diff res_0 res_1 --session work --human
h5i websec match res_1 --session work --status 200 && echo "reachable"

for id in $(seq 1 50); do
  h5i websec replay req_0 --session work --reset-budget --set query.id=$id |
    python3 -c 'import json,sys;r=json.load(sys.stdin)["response"];print(r["status"], r["bytes"])'
done | sort | uniq -c
```

Six commands: capture, read, change one thing, compare, assert, sweep. Ninety
per cent of this book is those six with different values in them.

Next: [`02-methodology.md`](02-methodology.md).
