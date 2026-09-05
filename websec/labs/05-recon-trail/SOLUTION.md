# Lab 05 — Intranet

## The point of this lab

The previous four handed you the request. Real targets do not. This one is
about the twenty minutes before the first `--set`.

## Four sources, in the order you should read them

**1. The rendered page and its source.** `markdown` gives you the text a model
should read; the HTML comment is not in it, so read both.

```bash
h5i browser open http://127.0.0.1:9050/ --session lab05 --new --capture
h5i browser markdown --session lab05
h5i websec show res_0 --session lab05 --raw | grep -i 'todo\|<!--'
```

    <!-- TODO(dana): kill the v0 API before the audit -->

**2. `robots.txt`.** A file whose entire purpose is to list the paths the owner
does not want indexed.

```bash
h5i websec replay req_0 --session lab05 --set path=/robots.txt
h5i websec show res_1 --session lab05 --raw
```

    Disallow: /internal/
    Disallow: /api/v0/

**3. Whatever the disallowed directories hold.** `/internal/notes.md` names the
shape of the endpoint *and* the interesting id.

**4. The version skew itself.** `v3` demands a bearer token. `v0` was written
before the app had any concept of one.

```bash
h5i websec replay req_0 --session lab05 --set path=/api/v0/employee/1
```

## Keeping the map

Every message is in the session, so the map builds itself:

```bash
h5i websec sitemap --session lab05 --human      # origins and endpoints reached
h5i websec requests --session lab05 --human     # every message, with status
h5i websec requests --session lab05 --status 404 --human   # what you guessed wrong
h5i browser requests --session lab05            # including what policy refused
```

`sitemap` is the artefact to keep. On a real engagement it is the thing you
paste into notes at the end of a session, and it is generated rather than
remembered.

## The bug

Deprecation is a documentation event, not a routing event. `/api/v0/` was
announced as gone and left mounted. The auth requirement was added in v3, so
every control the team believes in lives on a version nobody has to use.

## What to sweep on a real target

```
/robots.txt  /sitemap.xml  /.well-known/security.txt  /.git/HEAD
/.env  /.env.bak  /backup.zip  /server-status  /actuator/health  /debug
/api  /api/v1  /api/v2  /swagger.json  /openapi.json  /graphql
```

Sweep them as replays of one captured request so every probe is in the same
record with the same identity:

```bash
for p in /.git/HEAD /.env /swagger.json /actuator/env; do
  printf '%-16s ' "$p"
  h5i websec replay req_0 --session lab05 --set path=$p |
    python3 -c 'import json,sys;r=json.load(sys.stdin)["response"];print(r["status"],r["bytes"])'
done
```

Watch the **size** column, not only the status. An application that returns 200
with a soft-404 body is common; a 200 whose length differs from the other 200s
is the hit.

## The fix

Delete dead routes rather than documenting them as dead. Put the authorization
check in one place that every version passes through, so a new version cannot
be written without it. And treat `robots.txt` as public documentation of your
attack surface, because that is what it is.

## h5i technique

| Verb | Use |
| --- | --- |
| `browser markdown` | the page as prose |
| `browser snapshot` | the page as elements with `@ref` handles |
| `websec sitemap` | everything this session reached |
| `websec requests --status N` | slice the record by outcome |
| `websec replay --set path=` | a content sweep that stays inside the audit |
