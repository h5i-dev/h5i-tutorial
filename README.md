# h5i websec — a web security course in 42 labs

A hands-on course in web application security, built around
[h5i](https://github.com/h5i-dev/h5i) and its `websec` plugin: an HTTP
workbench that captures every message a browser session sent, gives each one a
stable id, and lets you edit and resend it with one part changed.

Every lab is a small, deliberately vulnerable application you run on your own
machine, a brief with no spoilers, a proof of concept that really works, and a
writeup that explains the bug, the technique, the variants, and the fix.

```bash
./run.sh 06                 # start lab 06, print its URL
./run.sh stop               # stop every lab, and close leftover h5i sessions
./solve.sh 06               # start it, run the proof of concept, check the flag
./test-all.sh               # every lab, end to end
cat labs/06-*/README.md     # the brief
cat labs/06-*/SOLUTION.md   # the writeup, when you want it
```

Everything is Python's standard library and one binary. No Docker, no
databases, no network access, no accounts.

---

## 1. Setup

You need **Python 3.11+** and **h5i 0.4+ with the `websec` plugin**.

```bash
curl -fsSL https://h5i.dev/install.sh | sh          # h5i itself
h5i websec --help                                   # if this fails, read on
```

`websec` ships separately from the base binary:

```bash
curl -fsSL https://h5i.dev/install.sh --websec | sh
h5i plugin install websec --from ./h5i-websec
h5i plugin list
```

Building from source instead:

```bash
git clone https://github.com/h5i-dev/h5i && cd h5i
cargo build --release --workspace
./target/release/h5i plugin install websec --from target/release/h5i-websec
```

If h5i is not on your `PATH`, point every script at it:

```bash
export H5I=~/src/h5i/target/release/h5i
./test-all.sh
```

Check it works:

```bash
./solve.sh 01
FLAG{query_tampering}
```

Labs 20–24 and 33 also use `h5i` as a scripted **victim browser**, so those need
`h5i` reachable from the lab process (on `PATH`, or via `H5I`).

Every lab binds `127.0.0.1` only, on port `9000 + 10 × lab number` — lab 6 is
`9060`, lab 42 is `9420`. A few use the next port up as a second service.

---

## 2. How to use this book

**Read `docs/` first.** The five chapters are short and they are the part that
makes the labs mean something:

| | |
| --- | --- |
| [`docs/01-the-workbench.md`](docs/01-the-workbench.md) | the tool: capture, ids, replay, diff, match, sequence, socket — with every `--set` target |
| [`docs/02-methodology.md`](docs/02-methodology.md) | how to approach an application you have never seen |
| [`docs/03-cheatsheet.md`](docs/03-cheatsheet.md) | one page: every flag, every probe, every payload family |
| [`docs/04-reporting-and-scope.md`](docs/04-reporting-and-scope.md) | turning findings into a report, and the rules of engagement |
| [`docs/05-limits.md`](docs/05-limits.md) | where h5i is stricter or thinner than a browser, and what to do about it |

**Then work the labs in order.** They are ordered so that each one assumes the
last. Give each brief a real attempt before opening `SOLUTION.md` — the writeup
is worth much more after you have been stuck.

**Work inside one session.** Open the target with `--capture`, and make every
probe a replay of something you captured. At the end, `h5i websec requests` is
your notes and your reproduction, written by the engine rather than remembered
by you.

---

## 3. The curriculum

### Part I — The workbench (learn the tool)

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 01 | [Statuspage](labs/01-query-tampering) | parameter tampering | ① |
| 02 | [Curio Shop](labs/02-hidden-form-field) | form field tampering | ① |
| 03 | [Helpdesk](labs/03-cookie-role) | broken session integrity | ① |
| 04 | [Payroll](labs/04-verb-tampering) | verb tampering, fail-open rules | ① |
| 05 | [Intranet](labs/05-recon-trail) | recon and deprecated surface | ① |

### Part II — Access control

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 06 | [Invoices](labs/06-idor-sequential) | IDOR | ① |
| 07 | [Docstore](labs/07-idor-uuid) | IDOR behind unguessable ids | ② |
| 08 | [Ledger](labs/08-cross-session-authz) | authentication ≠ authorization (`--as`) | ② |
| 09 | [Signup](labs/09-mass-assignment) | mass assignment | ② |
| 10 | [Passport](labs/10-jwt-alg-confusion) | JWT `alg: none`, weak secret | ② |
| 11 | [Keyring](labs/11-jwt-kid-injection) | JWT `kid` key injection | ③ |

### Part III — Injection

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 12 | [Catalogue](labs/12-sqli-union) | SQL injection, union | ② |
| 13 | [Waitlist](labs/13-sqli-blind-boolean) | blind SQLi, boolean oracle | ③ |
| 14 | [Coupons](labs/14-sqli-blind-time) | blind SQLi, timing oracle | ③ |
| 15 | [Vaultdoor](labs/15-nosql-operator) | NoSQL operator injection | ② |
| 16 | [Logdesk](labs/16-command-injection) | OS command injection | ② |
| 17 | [Postcard](labs/17-ssti-template) | server-side template injection | ③ |
| 18 | [Avatar](labs/18-xxe-svg-upload) | XXE via upload | ③ |
| 19 | [Rename](labs/19-second-order-sqli) | second-order SQL injection | ④ |

### Part IV — The browser as a weapon

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 20 | [Findit](labs/20-reflected-xss-filter) | reflected XSS, filter bypass, session theft | ③ |
| 21 | [Board](labs/21-stored-xss-httponly) | stored XSS against `HttpOnly` | ③ |
| 22 | [Prefs](labs/22-csrf-no-token) | CSRF | ③ |
| 23 | [Partner API](labs/23-cors-origin-check) | CORS misconfiguration | ③ |
| 24 | [SSO](labs/24-oauth-redirect-uri) | OAuth `redirect_uri` validation | ④ |

### Part V — The server as a client

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 25 | [Link preview](labs/25-ssrf-metadata) | SSRF to instance metadata | ② |
| 26 | [Webhook tester](labs/26-ssrf-filter-bypass) | SSRF past a blocklist | ③ |
| 27 | [Docs](labs/27-path-traversal-encoded) | traversal past an encoding filter | ④ |
| 28 | [Avatars](labs/28-upload-path-write) | arbitrary file write via upload | ③ |
| 29 | [Wiki](labs/29-lfi-log-poisoning) | LFI → log poisoning → RCE | ④ |

### Part VI — Protocol

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 30 | [Frontdoor](labs/30-request-smuggling-clte) | request smuggling (CL.TE) | ⑤ |
| 31 | [Reports](labs/31-crlf-header-injection) | CRLF / header injection | ③ |
| 32 | [Passreset](labs/32-host-header-reset) | host header poisoning | ③ |
| 33 | [Newsroom](labs/33-cache-poisoning) | web cache poisoning | ④ |
| 34 | [Fleet console](labs/34-websocket-injection) | injection over a WebSocket | ③ |

### Part VII — Logic, time, and crypto

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 35 | [Wallet](labs/35-race-double-spend) | race condition (check-then-act) | ③ |
| 36 | [Checkout](labs/36-coupon-stacking) | business logic | ② |
| 37 | [Recover](labs/37-predictable-token) | predictable token / weak PRNG | ③ |
| 38 | [Signer](labs/38-length-extension) | hash length extension | ⑤ |
| 39 | [Twostep](labs/39-mfa-bypass) | MFA bypass | ② |
| 40 | [Prefs jar](labs/40-pickle-cookie-rce) | insecure deserialisation | ④ |

### Part VIII — Chains

| # | Lab | Class | ★ |
| --- | --- | --- | --- |
| 41 | [Settings](labs/41-sequence-csrf-chain) | mass assignment behind CSRF (`sequence`) | ③ |
| 42 | [Meridian](labs/42-the-gauntlet) | the final exam: a five-step chain | ⑤ |

---

## 4. What each lab contains

```
labs/06-idor-sequential/
  README.md      the brief — story, target, goal, one hint, no spoilers
  app.py         the vulnerable application; the bug is commented in place
  solve.sh       the proof of concept: real h5i commands that print the flag
  SOLUTION.md    the writeup — the bug, finding it, variants, the fix, the technique
```

Flags are `FLAG{lab_name_with_underscores}`, derived from the directory name, so
a solution that prints one really did retrieve it.

`labs/lib/` holds the shared pieces: a 200-line web toolkit so each `app.py`
fits on a screen, a handful of shell helpers, and an "admin bot" that is a real
h5i browser running your payloads.

---

## 5. Where to go after lab 42

Two public corpora, and worked h5i solutions for both:

* [XBOW validation benchmarks](https://github.com/xbow-engineering/validation-benchmarks)
* [Argus validation benchmarks](https://github.com/pensarai/argus-validation-benchmarks)
* [h5i-benchmark](https://github.com/h5i-dev/h5i-benchmark) — 154 solved
  instances, each a short shell script in the same idiom as this book's
  `solve.sh` files. Read them; they are the next hundred labs.

Then: PortSwigger's Web Security Academy for breadth, and a bug bounty
programme with a scope you have actually read.

---

## 6. Scope and intent

These labs bind to `127.0.0.1` and are meant to be attacked. Everything you
learn here applies to systems you own or have written authorisation to test,
and to nothing else. `docs/04-reporting-and-scope.md` covers the rest.

Apache-2.0, like h5i.
