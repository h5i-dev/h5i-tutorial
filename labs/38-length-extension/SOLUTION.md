# Lab 38 — Signer

## The bug

```python
def sign(message): return hashlib.sha256(SECRET + message).hexdigest()
```

`sha256(secret || message)` looks like a message authentication code and is not
one. SHA-256 is a **Merkle–Damgård** construction: it processes the message in
64-byte blocks, and the digest it returns **is** its internal state after the
last block.

So anyone holding a digest holds the hash function's state, and can carry on
hashing from there — without knowing a single byte of the secret.

## What you can and cannot do

You *cannot* recover the secret, and you *cannot* forge a signature for an
arbitrary message. You can do exactly one thing, and it is enough:

> Given `sign(m)` and `len(secret)`, compute `sign(m ‖ padding(m) ‖ anything)`
> for any `anything` you choose.

The `padding` is the bytes SHA-256 would have appended to `secret ‖ m`: a `0x80`
byte, zeros, and the 64-bit bit-length. They become part of your forged message,
which is why the attack needs the message format to tolerate junk in the middle.
Query strings tolerate it beautifully.

## The exploit

```
original: user=guest&role=viewer
forged:   user=guest&role=viewer \x80\x00…\x01\x30 &role=admin
```

The parser reads the junk as a garbage field name and then reads `role=admin` —
and **the last value wins** in almost every query-string parser, so the appended
field overrides the original.

```bash
python3 extend.py --digest <sig> --data 'user=guest&role=viewer' \
                  --append '&role=admin' --key-len 16
```

`extend.py` in this lab is an ordinary SHA-256 whose state can be set from
outside — that is the whole tool. Read it; the attack is much less mysterious
once you see that `compress()` is unchanged.

## The two practical obstacles

**1. You must know the secret's length.** You do not, usually. Sweep it — it is
one request per candidate:

```bash
for n in $(seq 4 64); do
  read -r DATA SIG <<<"$(python3 extend.py --digest $SIG0 --data "$ORIG" --append '&role=admin' --key-len $n)"
  h5i websec replay req_0 --session lab38 --reset-budget --raw-target "/api/act?data=$DATA&sig=$SIG"
done
```

Watch for the one that stops returning 403.

**2. The forged message contains raw bytes.** `0x80` and NULs. Their
percent-encoding *is* the payload, so a URL parser that re-encodes `%` destroys
it — exactly Lab 27. Use `--raw-target`:

```bash
h5i websec replay req_0 --session lab38 --raw-target "/api/act?data=$DATA&sig=$SIG"
```

## Where this appears

* API signing schemes rolled by hand: `sig=sha1(secret+params)`
* signed cookies and download links built the same way
* Flickr's original API, and a long tail of imitations
* anything where the phrase "we hash the secret with the data" appears in a
  design document

The suffix form `hash(message ‖ secret)` is not length-extendable, but has its
own collision problems. SHA-3 and BLAKE2 are sponge/keyed constructions and are
not extendable at all — but do not rely on knowing which one is in use.

## The fix

```python
hmac.new(SECRET, message, hashlib.sha256).hexdigest()
```

HMAC exists precisely because of this attack — its nested construction makes the
output not the internal state. Compare with `hmac.compare_digest`, never `==`.

Two further notes on this app: the MAC is truncated to 16 hex characters (64
bits), which is weak for a value an attacker may grind against offline; and the
signed blob is a query string, whose last-value-wins parsing turns any appended
field into an override. Sign a canonical, unambiguous encoding — and prefer
signing a token whose fields cannot be duplicated at all.

## h5i technique

`--raw-target` for a payload whose percent-encoding must survive, plus a
one-request-per-candidate sweep for the unknown key length.
