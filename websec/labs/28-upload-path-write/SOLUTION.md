# Lab 28 — Avatars

## The bug

```python
if not data.startswith(b"\xff\xd8\xff"):        # what
    return js({"error": "not a JPEG"}, 400)
target = ROOT / "uploads" / (part["filename"] or "avatar.jpg")   # where
target.write_bytes(data)
```

The team upgraded from extension checking to content sniffing and felt safer.
Content sniffing answers **what** was uploaded. Nothing here answers **where it
goes** — and the destination comes from the client, in the `filename` field of
the multipart part.

## Two independent attacker inputs

An upload has *at least* three separately-controlled fields, and developers
usually think about one:

| Field | Controlled by | Usual mistake |
| --- | --- | --- |
| body bytes | attacker | checked (magic numbers, image parse) |
| `filename` | attacker | joined onto a path, echoed into HTML, put on a command line |
| `Content-Type` | attacker | trusted as the file's type |

Test all three, always, and independently.

## The polyglot

The file must be a JPEG to the sniffer and a key list to the reader:

```python
open("poly.jpg", "wb").write(b"\xff\xd8\xff\xe0" + b"\nk-pwn-1\n")
```

Real magic bytes, then your text. The consumer here splits on whitespace and
looks for a match, so a mangled first token costs nothing. Most consumers are
this forgiving: config parsers skip lines they cannot read, `.htaccess` ignores
junk, PHP ignores everything outside `<?php`, and a `.py` file can begin with a
`#`-comment holding whatever bytes you like.

`--set` cannot carry `\xff\xd8\xff` — a command line is text and that is not
text in any encoding — so the file comes from disk:

```bash
h5i websec replay req_0 --session lab28 --create \
    --set method=POST --set path=/api/avatar \
    --set-file multipart.file=./poly.jpg \
    --set 'multipart.file.filename=../config/trusted_keys.txt' \
    --set multipart.file.content_type=image/jpeg
```

## Choosing where to write

An arbitrary file write is worth exactly as much as the best file you can reach.
Rank targets by how soon something *reads* them:

1. A file consulted on every request — an allowlist, a key list, a config
   reloaded on change. Instant effect, no restart needed. (This lab.)
2. A web-served directory with a handler for the extension — `.php`, `.jsp`,
   `.aspx`, a `.py` under an autoloading path.
3. `.htaccess` / `web.config` — turn a directory into one that executes.
4. A template the app renders (which is Lab 17, arriving from the file system).
5. `~/.ssh/authorized_keys`, a cron file, a systemd unit, a `.bashrc`,
   `/proc/self/cwd/...` — where the process user permits it.
6. Overwrite the application's own source and wait for a reload.

The same list applies to **zip-slip** (an archive entry named `../../x`), tar
extraction, and any "restore from backup" feature.

## The fix

Never let the client name the file:

```python
import secrets, pathlib
name = secrets.token_hex(16) + ".jpg"          # you choose the name
target = (UPLOADS / name).resolve()
if not target.is_relative_to(UPLOADS.resolve()):
    reject()
```

Generate the name server-side, keep the original only as a display string in
the database, store uploads outside the web root, serve them through a handler
that sets `Content-Type` and `Content-Disposition: attachment`, and re-encode
images rather than trusting a header check. Serve user content from a separate
origin so that a file which does slip through is not same-origin with your app.

## h5i technique

`--set-file multipart.<part>=PATH` alongside `--set multipart.<part>.filename=`
— the two halves of an upload, controlled separately, which is the whole point
of this lab.
