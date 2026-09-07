#!/usr/bin/env python3
"""rows.py COLUMN... — turn one `h5i browser extract` answer into aligned CSV.

Read the JSON that `h5i browser extract` writes to standard output, take the
named columns in the order given, and write CSV with a header row.

It exists for one reason, and the reason is worth the file.

`extract` has no notion of a row. Every key in the schema is matched against
the whole page independently, so what comes back is a set of *columns* — a
list of twenty titles, a list of twenty prices — and never a list of twenty
books. Zipping the columns is correct only while they are the same length, and
the first card that is missing a field breaks that: one column is nineteen
long, the rest are twenty, and from that card onward every price is attached to
the wrong title. Nothing downstream can detect it. The file looks fine.

So this refuses to zip columns of different lengths, and says which lengths.
The fix is never here; it is in the schema. Anchor each selector to the row
container, so a row that lacks the field still contributes an empty string:

    "price": ["p.price_color"]                       # 19 — silently wrong
    "price": ["article.product_pod p.price_color"]   # 20 — one per card

Values that came from `attr` arrive wrapped on h5i 0.4.1 and earlier, because a
list of attribute reads was a list of one-key objects: `[{"href": "..."}, ...]`.
Later engines answer `["...", ...]`. Both are accepted here, so a scraper in
this course produces the same CSV on either.

A schema that uses `fields` needs none of this: it already answers rows, and
`extract | python3 -c` is enough to write them out.
"""

import csv
import json
import sys


def unwrap(value):
    """`{"href": "/x"}` -> `/x`, for the engines that wrap an attribute read."""
    if isinstance(value, dict) and len(value) == 1:
        return next(iter(value.values()))
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def main(argv):
    columns = argv[1:]
    if not columns:
        sys.exit("usage: extract ... | rows.py COLUMN [COLUMN ...]")

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        # `extract` writes its errors as prose, not JSON, so an unparseable
        # stdin is nearly always the error text. Show it rather than the
        # decoder's complaint about where the prose stopped looking like JSON.
        sys.exit("rows.py: extract did not return JSON:\n%s" % exc.doc.strip()[:400])

    missing = [c for c in columns if c not in data]
    if missing:
        sys.exit("rows.py: no such column: %s (the answer has: %s)"
                 % (", ".join(missing), ", ".join(sorted(data)) or "nothing"))

    scalars = [c for c in columns if not isinstance(data[c], list)]
    if scalars:
        sys.exit("rows.py: %s is a single value, not a column. Write the "
                 "selector inside an array — \"%s\": [\"...\"] — to ask for "
                 "every match." % (", ".join(scalars), scalars[0]))

    lengths = {c: len(data[c]) for c in columns}
    if len(set(lengths.values())) > 1:
        sys.exit("rows.py: the columns are not the same length, so no zip of "
                 "them is a table: %s\nAnchor each selector to the row "
                 "container so every row contributes exactly one value."
                 % ", ".join("%s=%d" % (c, n) for c, n in lengths.items()))

    out = csv.writer(sys.stdout, lineterminator="\n")
    out.writerow(columns)
    for i in range(next(iter(lengths.values()), 0)):
        out.writerow([unwrap(data[c][i]) for c in columns])


if __name__ == "__main__":
    main(sys.argv)
