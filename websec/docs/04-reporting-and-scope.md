# 4. Reporting, and the rules of engagement

The exploit is half the job. A finding that nobody acts on has the same effect
on the world as a finding nobody made.

---

## 4.1 Before you test

Write these down in your own notes, before the first request:

* **Targets.** Which hosts, which ports, which subdomains, which environments.
  "*.acme.test" and "acme.test" are different scopes, and staging is not
  production unless somebody said so.
* **Accounts.** Which ones you were given, and what role each holds. Ask for two
  accounts at the same privilege level — half of this book's Part II is
  untestable with one.
* **Prohibited actions.** Denial of service, data destruction, spam, social
  engineering, physical access, testing third-party services the target merely
  uses.
* **Techniques that touch other people.** Request smuggling (Lab 30) steals
  *other users'* requests. Cache poisoning (Lab 33) serves your payload to
  everyone. Both need explicit written permission, a quiet window, and a plan to
  restore state. Ask specifically; a generic "you may test the web application"
  does not cover them.
* **The stop signal.** Who to contact, on what channel, and what happens if you
  break something at 2am.
* **Data handling.** If you retrieve real customer data, how much do you keep,
  where, for how long, and how do you destroy it? The answer is usually "one
  redacted record as evidence, and nothing else".

If any line is unclear, ask before you test. "I assumed it was in scope" is not
a defence, professionally or legally.

---

## 4.2 While you test

**Minimise blast radius.** Prove a vulnerability with the smallest action that
proves it. You do not need to dump the table; you need one row, redacted, and
the query that produced it. You do not need to delete the record; you need the
403 that did not happen.

**Do not pivot into other people's data** further than the proof requires. Read
one other tenant's document, note its id, stop.

**Keep the record.** Every probe as a replay inside one session means
`h5i websec requests` is your evidence log, written by the engine as it went
rather than reconstructed afterwards. Note the ids of the requests that matter
as you go.

**Report critical findings immediately.** Remote code execution, authentication
bypass, and mass data exposure do not wait for the end of the engagement.

**Stop when something breaks.** If a payload takes a service down, tell someone
now, and say exactly what you sent.

---

## 4.3 The report

A finding is five things. In this order.

**1. What an attacker can do.** One sentence, in the client's vocabulary, with
no jargon and no payload.

> An unauthenticated internet user can read any customer's invoices, including
> billing addresses and payment references.

Not "IDOR in /api/invoice". Not "the id parameter is not validated". The
sentence a director has to be able to repeat in a meeting.

**2. Why it happens.** Two or three sentences and, where you have it, the line.

> `/api/invoice` looks up the invoice by id and returns it. It reads the
> caller's account number and never compares it to the invoice's owner.

**3. How to reproduce it.** Exact, runnable, from a clean state. Say which
account, which URL, which value. A reader who cannot reproduce it will
downgrade it.

```bash
h5i browser open 'https://target/api/invoice?id=1041' --session repro --new --capture
h5i websec replay req_0 --session repro --set query.id=1004
# → 200, an invoice belonging to account 1
```

Curl, HTTP messages, or a `websec sequence` file all work; pick whatever the
reader's team can run. A sequence file is the strongest artefact for a
multi-step finding, because it *is* the reproduction rather than a description
of one.

**4. What it costs.** Impact in the client's terms: how many records, whose,
what regulatory category, what an attacker gains. Say what you did **not** do —
"we confirmed access to one non-production record and stopped" — so the reader
knows the boundary of the evidence.

**5. How to fix it.** Specific, and at the right level.

> Scope the lookup: `WHERE id = ? AND account_id = ?`, returning 404 when the
> row is not the caller's. Enforce tenancy at the data-access layer so a new
> endpoint cannot omit it.

Then, separately, the systemic note: "this pattern appears in 6 of the 19
endpoints we reviewed" is worth more than six individual findings.

---

## 4.4 Severity, honestly

Rate by what an attacker achieves, and be explicit about the preconditions.

| | |
| --- | --- |
| **Critical** | unauthenticated RCE, full authentication bypass, mass data exposure |
| **High** | privilege escalation, another user's data, account takeover with a realistic precondition |
| **Medium** | needs a user interaction or an unusual precondition; limited data |
| **Low** | information disclosure with no clear path forward |
| **Informational** | hardening, defence in depth, no attacker benefit today |

Two rules that keep you credible:

**Chain before you rate.** Lab 42 is five findings that are individually
low-to-medium and jointly critical. Rate the chain, and list its links.

**Do not inflate.** A missing security header on a page with no functionality is
informational. Calling it high burns the credibility you will need on the
finding that matters. Equally, do not deflate to seem measured: an
authentication bypass is critical even when the fix is one line.

---

## 4.5 Writing up a negative

"We tested X and found nothing" is a real deliverable and is often the most
useful page in the report. Say what you tested, how, and what would have shown
a problem. A negative you cannot describe is a negative nobody can trust — and
the section is what stops the next tester repeating your afternoon.

Distinguish "not vulnerable" from "not tested" and from "could not be tested".
The last one is where scope and tooling limits go (see
[`05-limits.md`](05-limits.md)).

---

## 4.6 A note on this book

The labs here bind to `127.0.0.1` and exist to be attacked. The techniques
transfer to any web application, which is the point, and also the reason to be
careful: everything in this book applies to systems you own or have written
authorisation to test, and to nothing else.

Unauthorised testing is a crime in most jurisdictions regardless of intent, of
whether you caused harm, or of whether you reported what you found. If you want
targets, there are many legitimate ones: your own applications, deliberately
vulnerable ones like these, the public benchmark corpora in the README, and bug
bounty programmes — whose scope pages you should read completely before you send
the first request.

Next: [`05-limits.md`](05-limits.md).
