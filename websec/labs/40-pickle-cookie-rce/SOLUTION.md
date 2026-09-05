# Lab 40 — Prefs jar

## The bug

```python
return pickle.loads(raw)
```

A pickle is not data. It is a **program for a stack machine**, and one of its
opcodes calls a callable of the pickle's choosing. `pickle.loads` on untrusted
bytes is `exec` on untrusted bytes, and Python's own documentation says so.

The signature is real, and it is beside the point. A MAC decides *who* may
supply the bytes. It does not make the bytes safe — and here the key is the
framework's sample value, printed on the homepage, so "who" is everybody.

## Finding the format before the exploit

Read the cookie, do not assume:

```bash
h5i browser open http://127.0.0.1:9400/ --session lab40 --new --capture
h5i websec show res_0 --session lab40 --raw
```

Then decode a segment and look at the first bytes. The magic numbers worth
recognising on sight:

| First bytes | Format | What it means |
| --- | --- | --- |
| `\x80\x04\x95` / `\x80\x05` | Python pickle | `__reduce__` → RCE |
| `rO0AB` (base64) / `\xac\xed\x00\x05` | Java serialization | ysoserial gadget chains |
| `O:8:"stdClass"` / `a:2:{` | PHP `serialize` | POP chain via magic methods |
| `AAEAAAD/////` | .NET BinaryFormatter | RCE |
| `!!python/object/apply:` | PyYAML `yaml.load` | RCE |
| `{"$type":` | Json.NET `TypeNameHandling` | RCE |
| `eyJ` | base64 JSON | Labs 03 and 10 |

Two dots and three segments means JWT; one dot and a short tail usually means
"blob plus MAC", as here.

## The payload

```python
class Payload:
    def __reduce__(self):
        return (subprocess.check_output, (["printenv", "FLAG"],))
```

`__reduce__` tells `pickle` how to rebuild the object: call this callable with
these arguments. Any callable will do — `os.system`, `subprocess.check_output`,
`builtins.eval`. Then sign it with the key you were given and send it:

```bash
h5i websec replay req_0 --session lab40 --create \
    --set path=/api/prefs --set "cookie.prefs=$COOKIE"
```

For a real target, prefer a payload whose **output you can see** (`check_output`
returns bytes that get stringified into the response) or that reaches out to a
collector, over a blind `os.system`.

## The two bugs, ranked

People report the weak key. The key is the *lesser* bug:

* **Rotate the key** and the application is still one leaked key, one debug
  endpoint, one source-code disclosure, one `.git` directory away from remote
  code execution.
* **Replace pickle with JSON** and a leaked key costs you a forged preference.

Report both, and say which one is structural. A finding that recommends only
key rotation leaves the application in the same shape it was.

## The fix

```python
value = json.loads(raw)          # data in, data out
```

Serialise data, not objects. JSON, msgpack, protobuf — formats with no opcode
for "call this". Keep the MAC (with a random key from a secret manager, compared
with `compare_digest`, untruncated), because you still do not want users editing
their own preferences. Better still, keep server-side state and put an opaque id
in the cookie.

Where a language's native serialisation is unavoidable, restrict it:
`pickle.Unpickler` with an overridden `find_class` allowlist,
`yaml.safe_load`, Java's `ObjectInputFilter`, and never `BinaryFormatter`.

## h5i technique

`--set cookie.<name>=` with a value built in a heredoc — and the habit of
identifying a blob's *format* from its first bytes before deciding what it is.
