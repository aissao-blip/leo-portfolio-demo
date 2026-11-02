# Technical overview

## Stack

| Layer | Choice | Why |
|---|---|---|
| Runtime | Python 3.9+ | Already present on macOS; no version juggling |
| Web | Flask 3 | One dependency, no build step, renders on the server |
| Templating | Jinja2 | Ships with Flask |
| Storage | JSON files | Inspectable in a text editor; no database to install |
| Styling | One hand-written stylesheet | No framework, no compile step |
| AI | Deterministic rules, optional Anthropic | Works with no key, no network, no cost |

The whole dependency manifest is one line: `Flask`. `anthropic` is listed and
commented out, needed only for the optional live mode.

## Layout

```
run.py                  launcher; loads .env, starts the server
app/
  server.py             routes and request handling
  agent.py              classification, drafting, briefing
  store.py              JSON persistence, seeding, reset
  seed/                 the fictional dataset as shipped
  templates/            eight server-rendered pages
  static/app.css        the stylesheet
data/                   working copy, created on first run, gitignored
portfolio/              case study, this document, walkthrough, screenshots
```

`app/seed/` is read-only in practice. On first run `store.ensure()` copies it
to `data/`, and everything afterwards reads and writes `data/`. `Reset demo
data` copies the seed back over it. That separation is what makes the demo
safe to explore: there is no way to break it that a single click does not fix.

## How the agent decides

### Classification

`agent.classify(subject, body)` walks an ordered list of intents, each with
its own signal phrases, and returns the first that matches:

```python
{
  "intent": "negotiating",
  "label": "Negotiating terms",
  "reason": 'Reads as negotiating terms — matched "room to move", "closer to".',
  "confidence": 0.84,
  "needs_decision": True,
  "suggest_stage": "Negotiating",
  "mode": "simulated",
}
```

Four things are worth noting about that shape.

**Order is meaningful.** A declined email that happens to mention a rate
should sort as a decline, so `decline` is tested before `negotiating`.

**The reason is generated alongside the verdict**, from the same signals, so
it cannot drift out of step with it. A reason assembled separately is a
comment, not an explanation.

**Confidence is a transparent function** of how many signals matched, not a
model score. It is labelled as such rather than dressed up.

**`needs_decision` is the field the interface sorts on.** It is the whole
organising idea: not who sent it, but whether it is asking something of you.

### Drafting

Classification chooses which of nine reply shapes applies, then fills it with
the creator's own details — name, tier, fee. In live mode the same verdict and
creator context become a prompt to Anthropic, and the result is labelled
`live` on screen. If the call fails for any reason the simulated draft is used
instead, so the demo cannot break because a key expired.

Which mode produced a draft is shown next to it, every time.

### Briefing

`agent.briefing()` takes the three datasets and computes what is waiting:
messages needing a decision, follow-ups whose date has arrived, renewals, and
deliverables past their date. It stores nothing. Change the data and the
briefing changes, which is the difference between a briefing and a screenshot
of one.

## Safety properties, and how they are enforced

**Nothing can send.** Not "sending is disabled" — there is no mail transport
in the application at all. No SMTP, no API client, no queue. The approval
endpoint marks a thread handled and updates a pipeline stage; that is its
entire effect.

**The sequence refuses to chase someone who replied.** `/outreach/<id>/advance`
returns HTTP 400 with an explanation when the sequence status is `replied`. It
is a guard in the handler, not a filter on a list, so no path reaches a chase.

**Simulated and real are distinguished in the log.** `store.log()` takes a
`kind`. A classification is `simulated`; a stage change that wrote to disk is
`real`. The activity page counts both separately.

**No credential is required or stored.** `.env.example` contains no key. The
demo runs with no `.env` at all.

## Performance

Every page is a single request with no client-side data fetching. The dataset
is small enough to load per request, which keeps the code honest: nothing is
cached, so nothing can be stale.

## Testing performed

See the README for the full verification list. Summary: all eight pages
return HTTP 200; all eight fictional emails classify with a reason; drafting,
approval, pipeline movement, sequence advancement, the reply guard, campaign
ticking and reset were each exercised and their results checked.
