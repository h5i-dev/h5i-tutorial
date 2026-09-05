# Lab 07 — Docstore

## The argument this lab is against

> "The ids are UUIDs. Nobody can enumerate them, so we do not need a check."

Two things are wrong with it, and this lab contains both.

## Leak #1 — the id comes out of a different endpoint

```python
hits = [… for k, v in DOCS.items() if q and q in v["title"].lower()]
```

`/api/search` filters on the *query* and not on the *tenant*. It is a listing
endpoint, so nobody thought of it as an authorization surface; it hands out
exactly the identifiers the read endpoint treats as secret.

```bash
h5i browser open 'http://127.0.0.1:9070/api/search?q=report' --session lab07 --new --capture
h5i websec show res_0 --session lab07 --raw
```

```json
{"q":"report","hits":[{"id":"…","title":"TPS Report","tenant":"initech"}]}
```

The response even labels the tenant. Sweep single vowels to enumerate the whole
corpus:

```bash
for q in a e i o u; do
  h5i websec replay req_0 --session lab07 --reset-budget --set query.q=$q
done
```

## Leak #2 — possession is not permission

```python
row = DOCS.get(doc_id)
return js({"id": doc_id, **row})
```

Once you hold the id, nothing asks whether you should. Unguessability is a
*rate limiter*, not an access control: it makes the attack take a step, and the
step is usually available.

```bash
h5i websec replay req_0 --session lab07 --set path=/api/document/<uuid>
```

## Where identifiers leak in the real world

Keep this list; it is most of the work in a real engagement.

* search, autocomplete, and `?q=` endpoints that forget the tenant filter
* `Location` headers and 302s after a create (`--no-follow` to read them)
* error messages: "document X belongs to tenant Y"
* HTML: `data-*` attributes, `<script>window.__STATE__ = {...}</script>`
* export/report endpoints, webhooks, activity feeds, `@mention` pickers
* the *other* user's copy of a shared object
* referrer headers, email notifications, cache keys, log endpoints

## The fix

Scope the read, and scope the list:

```python
row = DOCS.get(doc_id)
if not row or row["tenant"] != session.tenant:
    return js({"error": "not found"}, 404)
```

and in search, `if q in v["title"].lower() and v["tenant"] == session.tenant`.

The general rule: **every query that reaches storage carries the tenant in its
`WHERE` clause.** Enforce it at the data-access layer, where it cannot be
forgotten one endpoint at a time. Random ids remain worthwhile — they stop the
first accidental enumeration — but they are defence in depth, not the defence.

## h5i technique

Chaining two endpoints inside one session: the ids from `res_N` become the
`--set path=` of the next replay, and both halves stay in one audit trail you
can hand to the client as the reproduction.
