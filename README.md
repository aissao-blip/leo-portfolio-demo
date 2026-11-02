# Leo Portfolio Demo

An interactive demonstration of **Leo**, an AI agent for creator partnership
operations. Runs entirely on your own machine with fictional data.

Nothing here sends email, posts to chat, or connects to any external service.
No API key is required.

---

## Run it

You need **Python 3.9 or newer**. Nothing else.

### macOS

```bash
cd Leo_Portfolio_Demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### Windows

```powershell
cd Leo_Portfolio_Demo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Then open **http://127.0.0.1:5055**

To stop it, press `Ctrl+C`. To run it again, repeat the last two lines
(`activate`, then `python run.py`).

### If port 5055 is busy

```bash
PORT=5099 python run.py        # macOS
set PORT=5099 && python run.py # Windows
```

---

## What to look at

| Page | What it demonstrates |
|---|---|
| **Today** | Live counts, decisions waiting, pipeline distribution |
| **Inbox** | Email sorted by what it asks of you, with a reason on every row |
| **Creators** | 22 fictional profiles, filterable, with full histories |
| **Outreach** | Three-stage sequence — and a guard that refuses to chase a creator who replied |
| **Campaigns** | Deliverables per creator, deadlines, progress, metrics |
| **Briefing** | A daily briefing computed from current data, not stored |
| **Activity** | Every action labelled *simulated* or *real* |

**Start here:** open **Inbox**, press **Draft a reply** on any message, then
**Approve**. Then go to **Outreach** and press *Try to advance* on someone in
the "Stopped because they replied" section — it will refuse, and tell you why.

**Reset demo data** in the top bar restores everything to how it shipped.

---

## AI modes

**Simulated** (default) — rule-based, deterministic, no network, no key, no
cost. The same email always classifies the same way, which is what makes it
demonstrable.

**Live** (optional) — uses Anthropic to write the reply drafts.

```bash
cp .env.example .env
# edit .env: set LEO_DEMO_AI_MODE=live and add ANTHROPIC_API_KEY
pip install anthropic
```

Which mode produced a draft is shown on screen next to it. If a live call
fails the demo falls back to the simulated draft, so it cannot break.

---

## What was verified

Tested on macOS with Python 3.9 and Flask 3.1.3, on 2 November 2026.

- All eight pages return HTTP 200 and render
- All 8 fictional emails classify, each with a reason and a confidence
- Drafting works in simulated mode and returns the expected intent
- Approving a draft marks the thread handled **and** moves the creator's
  pipeline stage (verified: *Kwame Castellanos → In Conversation*)
- Advancing an outreach sequence records the stage and sets the next due date
- The reply guard refuses with HTTP 400 and an explanation
- Ticking a campaign deliverable updates both the count and the percentage
- Reset restores the dataset — handled emails returned to 0
- The activity log separates simulated entries from real ones

**Not tested:** live AI mode, which needs an Anthropic key I do not have; and
Windows, where the instructions follow standard Python practice but were
written rather than run.

---

## Fictional data

Every creator, campaign, email and metric is invented. Names, companies and
email addresses are fabricated and use `.example` domains, which cannot
resolve. No real creator, partner, campaign or message appears anywhere.

The data lives in `app/seed/`. Reset copies it over `data/`.

---

## Portfolio materials

In `portfolio/`:

- `CASE_STUDY.md` — the problem, the design, the decisions, the lessons
- `TECHNICAL_OVERVIEW.md` — architecture and how the agent decides
- `FEATURE_AUDIT.md` — what the original system actually did, and what this recreates
- `DEMO_WALKTHROUGH.md` — a 60–90 second video script
- `PORTFOLIO_DESCRIPTION.md` — portfolio and LinkedIn copy
- `screenshots/` — seven captures of the running application

---

## About this demonstration

The original Leo was built in an employment context. This is an independent
implementation: no source code, templates, prompts, credentials or records
were carried over. The original informed *what problems were worth solving*;
every file here was written for this demonstration.

See `portfolio/FEATURE_AUDIT.md` for the full accounting.

---

## Deploying it

The demo is self-contained: fictional data, no database, no API key, no
outbound network calls. It runs on a free plan anywhere that serves a Python
web app.

**Render** — the repository carries a `render.yaml`, so the setup is read
automatically:

1. Sign in at [render.com](https://render.com) with GitHub.
2. **New** → **Blueprint**, and pick `leo-portfolio-demo`.
3. **Apply**. The first build takes two or three minutes.

The free plan sleeps after fifteen minutes idle, so the first visit after a
quiet spell takes a few seconds to wake.

Locally, `python run.py` serves on `127.0.0.1` and never binds a public
interface. A host sets `HOST=0.0.0.0` to accept external traffic; `wsgi.py` is
the entrypoint gunicorn uses, and it copies the seed dataset on boot.

