# Lab 35 — Wallet

## The bug

```python
have = BALANCES[who]        # read
time.sleep(0.05)            # think
if have < amount: reject    # decide
BALANCES[who] = have - amount   # write
```

Between the read and the write the stored balance is still the old number. Every
request that arrives inside that window reads 100, decides 100 is enough, and
pays out. Twenty-five concurrent requests spend the same 100 credits many times over.

The generic name is **TOCTOU** — time of check to time of use — and it is the
same shape whether the state is a balance, a stock count, a "has this coupon
been used", a one-time token, or a rate-limit counter.

## `--repeat N --race`

```bash
h5i websec replay req_0 --session lab35 --create --repeat 25 --race \
    --set method=POST --set path=/api/transfer \
    --set header.Content-Type=application/json \
    --set "header.Authorization=Bearer $TOKEN" \
    --set json.to=vault --set json.amount=100
```

The sends leave from twenty-five threads that **meet at a barrier first**, so
they arrive inside one window instead of twenty-five consecutive ones. Around
ten of them land there; the rest get a correct 402, and that split is itself the
signature. A shell loop cannot
do this: it pays process startup between each request — tens of milliseconds
against a window measured in ones.

Every send is still a receipt and a stored message, so a race that reproduces is
a race somebody else can read afterwards. That matters: "I think it double-spent"
is not a finding; twenty numbered requests and a balance that went from 100 to
−1900 is.

Do not skip `--race` and hope. `--repeat 25` alone sends twenty-five requests in
sequence, which is a load test, not a race.

## Reading the result

The interesting output is the *victim's* state, not the responses. Some will succeed and some will 402, and the split varies run to run. Check the invariant afterwards:

```bash
h5i websec replay req_0 --session lab35 --create --set path=/api/rewards
```

If the vault holds more than alice ever had — 100 — the window is real, whether
that is 500 or 1200.

## When a plain burst is not enough

`--race` is a burst and h5i names it as one. It is **not** the single-packet
attack, which splits each request across two writes and holds back the final
byte so that twenty requests are completed by one TCP packet — the technique for
windows of tens of microseconds. Ordinary check-then-act windows, which is most
of them, do not need it.

Between the two, try:

* a larger `--repeat` — 50 or 100 costs nothing, and a wider net is the first
  thing to try when a race reproduces only sometimes
* removing whatever makes the requests unequal (keep-alive warm-up: send one
  request first, then race)
* races between *different* endpoints that touch the same row (transfer while
  refunding, redeem while cancelling) — often wider than a single-endpoint race

## Where to hunt for races

Anything that must happen once: coupon redemption, gift-card spend, vote,
"claim your free trial", withdrawal, invite acceptance, MFA enrolment, file
upload quota, follow/unfollow counters, and *any* two-step flow whose first step
reserves something.

Also the negative direction: races that make a counter go **down** past zero, or
that create two objects with the same unique key.

## The fix

Do not read-decide-write in application code. Make the database do it in one
statement, and let it enforce the invariant:

```sql
UPDATE balances SET amount = amount - :n WHERE user = :u AND amount >= :n;
-- then: if rowcount == 0, reject
```

Plus a `CHECK (amount >= 0)` constraint, so a future code path cannot bypass the
rule. Where a single statement is impossible, take a row lock (`SELECT … FOR
UPDATE`) inside a transaction, or use an idempotency key so a repeated request
returns the first result instead of doing the work again.

Rate limiting is not a fix — the whole attack fits inside 50 milliseconds.

## h5i technique

`--repeat N --race`, and the habit of verifying the invariant afterwards rather
than reading the responses.
