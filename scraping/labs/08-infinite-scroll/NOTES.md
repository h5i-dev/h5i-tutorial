# Lab 08 — writeup

## The loop is correct and the answer is wrong

```
# rendered before scrolling: 3
# after a scroll: 3
```

The termination condition — *stop when a scroll adds no items* — is the right
condition. It is met immediately, because this engine dispatches no
scroll-driven loading, and the loop cannot tell that apart from having reached
the bottom.

That failure is not specific to h5i. Every scroll loop has it. A slow network,
a lazy-loader waiting on an intersection observer that never fires because the
viewport is 720px tall, a rate limiter that started returning empty pages: all
of them look, from inside the loop, exactly like the end of the data. **A stop
condition that cannot distinguish "done" from "broken" will eventually return a
short file and call it a success.**

Where a real one comes from: a total the page states, a `next` link whose
absence is meaningful, a `pageCount` in a JSON payload. Labs 09 and 10 are both
about having one.

## Where the data was

```bash
h5i browser extract '{"items": {"selector": "[data-items]", "attr": "data-items"}}' --session lab08
```

```json
[{"id": 60, "title": "Asus VivoBook X441NA-GA190", "price": 295.99, "description": "…"}, …]
```

117 products, as JSON, in an attribute on the wrapper element, in the **first
response**. The scroll is a rendering decision made in JavaScript over data
that had already arrived. No script needed, no scrolling needed, one request.

The sibling attributes say so out loud: `data-type="scroll"` here, and
`data-pages` on the paginated version of the same catalogue. The page is
configured by attributes, and reading the configuration is faster than
inferring it from behaviour.

## The habit

Before automating an interaction, **look at what the first response already
contains.** Search the served HTML for a string you can see on screen — a
product name, a price — and see what surrounds it. If it is inside a JSON
literal rather than inside markup, the interaction was never going to be
necessary.

The places worth searching, roughly in order of how often they pay:

| Where | Looks like |
| --- | --- |
| a `data-*` attribute | `data-items='[{…}]'`, `data-props`, `data-state` |
| a framework state blob | `#__NEXT_DATA__`, `window.__NUXT__`, `__INITIAL_STATE__` |
| a JSON-LD block | `<script type="application/ld+json">` |
| an inline literal | `var data = [{…}]` (Lab 03) |
| an endpoint the page calls | found in the script source (Lab 06) |

`h5i browser extract '{"js": ["script"]}'` reads the fourth. The `--json`
answer from `h5i browser read` carries the request log for the fifth.
