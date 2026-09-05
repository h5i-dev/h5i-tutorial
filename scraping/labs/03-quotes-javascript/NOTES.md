# Lab 03 — writeup

## An empty column is a result

```json
{"quote": []}
```

That is not a failure. It is the page telling you that no element matching
`span.text` exists in what the server sent — which, given a selector you know
is right from Lab 02, is a fact about how the page is built. The same answer
would come from a wrong selector, and telling those two apart is the reading
skill this lab is really about:

```bash
h5i browser markdown --session lab03      # is the content there at all?
h5i browser extract '{"js": ["script"]}'  # is it in a script instead?
```

The second one finds `var data = [{"tags": ["change", …], "author": {…}` in
plain sight. The quotes were in the response the whole time — in a JavaScript
literal rather than in markup.

Note that `extract` distinguishes these two cases for you at the top level: a
schema where **nothing at all** matched is an error with a sentence in it,
while a schema where one key matched nothing is a normal answer with an empty
column. An object full of nulls would look like an answer, so it refuses to
produce one.

## What `--script` costs

Three things, and they are worth naming before turning it on out of habit.

**Attack surface.** Page script is the delivery channel for prompt injection,
and it is the only one h5i's default closes completely. On a site you do not
control, with an agent reading the result, that is not a small default to
change.

**Determinism.** A script-rendered page is a page that can render differently
on the same input — a timer, a race between two fetches, a feature flag. The
scraper that worked yesterday and returns nineteen rows today has not
necessarily changed.

**Coverage.** This engine's JavaScript is real but partial (see
[`../../docs/05-limits.md`](../../docs/05-limits.md)). `--script` is not a
promise that the page will work; it is permission for it to try. Lab 06 is the
one where permission is not enough.

## When to turn it on

When you have read the served HTML and confirmed the data is not in it —
not in the markup, not in a `<script>` literal, not in a `data-` attribute,
not in `#__NEXT_DATA__` or a JSON-LD block. In this lab the data *is* in a
script literal, so there is a third route:

```bash
h5i browser extract '{"js": ["script"]}' --session lab03 \
  | python3 -c 'import json,re,sys; …'   # parse the array out of the source
```

Ugly, brittle against a reformat, and it needs no `--script` at all. Labs 08
and 10 are the cases where that route is not ugly but obviously right, because
the page ships its data as JSON on purpose.

The order to try, on any page that looks empty:

| | |
| --- | --- |
| 1 | `structured` — JSON-LD, OpenGraph, `<meta>` |
| 2 | a `data-*` attribute holding JSON (Lab 08) |
| 3 | `#__NEXT_DATA__` or another framework's state blob (Lab 10) |
| 4 | a JSON endpoint the page calls (Lab 06) |
| 5 | `--script`, and render it |
