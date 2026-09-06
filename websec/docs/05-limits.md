# 5. Where the tool ends

Every instrument has a shape, and knowing yours is part of testing honestly.
**A payload that fails in h5i has not necessarily failed in the world**, and a
report that does not distinguish the two is wrong.

This chapter is what this book found while building 42 labs against h5i 0.4.

---

## 5.1 h5i is not a complete browser

The engine is Rust, without Chromium or V8's ecosystem. It reads content-heavy
pages and runs ordinary page JavaScript, and it does not implement everything.

**Confirmed working**, on h5i 0.4.1, by probing each one:

* page `<script>` execution with `--script`, and `setTimeout`
* `fetch()`, including cross-origin, with `credentials: 'include'`
* the same-origin policy and CORS, enforced faithfully — including a readable
  explanation on the blocked request (Lab 23)
* `addEventListener` and synthetic dispatch (`el.click()`)
* `<body onload>`
* cookie jars per session, `HttpOnly`, `Set-Cookie` attributes
* WebSocket client, both from a page and from `websec socket` (Lab 34)
* redirects, and `--no-follow` to stop at one

**Confirmed missing.** Each was reduced to a minimal page and filed upstream:

| What | Effect | Issue |
| --- | --- | --- |
| inline `on*` attributes are never registered as handlers (`onclick`, `onerror`, `onload`, except `<body onload>`) | `<img src=x onerror=…>` and `<svg onload=…>` — the two commonest XSS payload shapes — do nothing | [h5i#609](https://github.com/h5i-dev/h5i/issues/609) |
| subresource `load`/`error` events are never dispatched, although the fetch does go out | nothing can observe whether an image or script loaded, via attribute *or* `addEventListener` | [h5i#610](https://github.com/h5i-dev/h5i/issues/610) |
| forms never submit — `form.submit()` is a silent no-op, and clicking a `type=submit` button sends nothing | any flow that depends on a form POST cannot be driven | [h5i#611](https://github.com/h5i-dev/h5i/issues/611) |

Also absent: Canvas, Web Workers, IndexedDB, and the wider set of
single-page-application APIs — a page needing one gets it *named* in the
snapshot rather than silently blank.

**The habit that follows from all of this:** when a payload does not land,
**prove the sink first** with `<script>fetch('/collect?c=alive')</script>`
before concluding the injection failed. The difference between "no XSS" and "no
`onerror` handler" is an hour, and only one of them is a fact about the
target.

---

## 5.2 h5i is deliberately stricter in one place

```
DENIED POST http://other/… — `mode: "no-cors"` with `credentials: "include"`
would send a credential to another origin and never be able to check that the
server agreed, because an opaque response cannot be read.
```

Real browsers send that request. h5i refuses it. It is a defensible choice for a
browser whose job is to contain an agent, and it means the classic **POST-based
CSRF** vector cannot be demonstrated end to end here (Lab 22 uses the GET-based
one instead).

What to do about it: prove the CSRF *conditions* with two replays — no token
required, and `Origin`/`Referer` from another site accepted — read the
`Set-Cookie` attributes for a missing `SameSite`, and reproduce the final step in
a real browser before writing it up.

An opt-in that makes one session behave like a browser here is requested in
[h5i#612](https://github.com/h5i-dev/h5i/issues/612).

---

## 5.3 URL parsing happens before the request exists

A parsed URL percent-decodes and resolves `.` and `..` before there is a request
to send. That is true of every HTTP client, not just this one, and it destroys
any payload whose *encoding* is the exploit:

```bash
--set query.file=%252e%252e%252f…     # arrives as %2e%2e%2f — not the payload
--raw-target '/download?file=%252e%252e%252f…'   # arrives as written
```

`--raw-target` for the request-target, `--raw-request` for the whole message
(Labs 27, 30, 38). When a payload behaves oddly, `websec show req_N --raw` says
what actually left.

---

## 5.4 Timing has a floor

The h5i repository documents a known artefact: roughly one send in fifteen that
takes about two seconds costs around three seconds more than the request did.
That corrupts a timing oracle in exactly one direction — it can make a fast
answer look slow, never a slow answer look fast.

So the rule in Lab 14: **trust every "fast", confirm every "slow"**. The
confirmation is nearly free because the answer it confirms is the fast one. Use
`--repeat N` and read the **median and MAD** rather than one sample, and read
`samples[].total_ms` rather than wrapping the CLI in `time` — process startup is
tens of milliseconds of noise on a signal you are reading at hundreds.

---

## 5.5 The budget is a real constraint

Each page has a bounded network allowance. It exists to contain page code; a
deliberate sweep is the opposite of what it was built for. Without
`--reset-budget`, a long loop stops partway and every later probe reads as a
negative result — which in a blind extraction does not look like an error, it
looks like the secret ending.

**Any loop of more than a handful of replays takes `--reset-budget`.**

---

## 5.6 What h5i does not do at all

By design, and stated in its own documentation:

* **It does not find vulnerabilities.** No scanner, no payload generation, no
  wordlists, no verdicts. It owns the deterministic half — exact capture, stable
  ids, structured edit, resend, diff, timing, scope, audit — and you own the
  judgement half: which request matters, which parameter to bend, what a
  difference means, what to try next. This book is training for that half.
* **It is not a content filter.** It bounds what a persuaded agent can reach; it
  does not classify what a page says.
* **It is not sandboxed by default.** A session with no `--in` is not contained,
  and `h5i browser status` says so on every line.

---

## 5.7 When to reach for something else

| Situation | Tool |
| --- | --- |
| a heavy SPA that will not render | Chromium inside an h5i sandbox, or Playwright |
| interactive, exploratory manual work on one request | Burp Suite Repeater |
| large-scale automated scanning | a scanner; that is not what this is |
| protocol work below HTTP/1.1 semantics | raw sockets, `openssl s_client` |
| HTTP/2-specific desync | a client that speaks h2 frames directly |
| single-packet race attacks (microsecond windows) | Turbo Intruder or an equivalent |
| fuzzing binary protocols | a fuzzer |

None of that is a criticism. It is the same judgement as choosing a wrench: the
useful skill is knowing which one is in your hand.

---

## 5.8 If you find a limit this chapter does not list

That is a contribution. The h5i benchmark repository has a section titled "what
the corpus found in h5i" — seven items, six fixed, one of them a capability
rather than a defect (`websec socket` exists because a benchmark needed it).

A good report of a tool limit looks like a good report of a vulnerability: what
you expected, what happened, the smallest reproduction, and what it cost you.
[h5i#609–#612](https://github.com/h5i-dev/h5i/issues/609) are this chapter's own
four, filed in that shape.
