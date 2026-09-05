# h5i — tutorial

Two hands-on courses built on [h5i](https://github.com/h5i-dev/h5i), whose
engine **is** the browser's HTTP client. There is no proxy to configure and no
gap between what the browser did and what was recorded: every request is logged
before its bytes move, and a fetch that cannot be recorded is refused.

One course uses that to bend requests. The other uses it to read pages. They
share a tool and a habit — *know exactly what you sent and what came back* —
and nothing else. Start with either.

| | | |
| --- | --- | --- |
| **[`websec/`](websec/)** | 42 labs, 5 chapters | Web application security. Every target is a small, deliberately vulnerable app that runs on `127.0.0.1` and ships in this repository. IDOR, injection, SSRF, smuggling, races, and a five-step chain as the final exam. |
| **[`scraping/`](scraping/)** | 10 labs, 5 chapters | Web scraping. Every target is a public sandbox its operator published to be scraped. Pagination, forms, AJAX, infinite scroll, and the argument that you should find the data before writing a selector. |

```bash
cd websec   && ./solve.sh 01     # start a lab, run its proof of concept, check the flag
cd scraping && ./run.sh   01 -   # run a scraper, print the CSV
```

Both need **Python 3.11+** and the `h5i` binary; `websec` additionally needs its
`websec` plugin. Each course's README has its own setup section.

```bash
curl -fsSL https://h5i.dev/install.sh | sh
```

---

## Which one first

**`websec/`** if you want to learn to test applications. It is the longer
course, it is ordered so that each lab assumes the last, and it needs no
network — every target is in the repository.

**`scraping/`** if you want to get data out of pages. It is shorter, it stands
alone, and it runs against ten real sites, so it needs the network and it is
built around only touching hosts that asked for it.

---

## The line between them

`websec/` attacks; every one of its targets binds `127.0.0.1` and ships here, on
purpose. What you learn there applies to systems you own or have written
authorisation to test, and to nothing else.

`scraping/` touches real hosts, and therefore only hosts whose operators
published them for exactly this. Each lab quotes the site saying so, fetches two
or three pages, and paces itself.

Same rule underneath: **the target's consent is what makes the difference, and
knowing you have it is your job.** See
[`websec/docs/04-reporting-and-scope.md`](websec/docs/04-reporting-and-scope.md)
and [`scraping/docs/04-etiquette-and-scope.md`](scraping/docs/04-etiquette-and-scope.md).

---

Apache-2.0, like h5i.
