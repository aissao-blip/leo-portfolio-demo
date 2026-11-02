# Feature audit — the original Leo, and what this demonstration recreates

Written by inspecting the original source directly: reading the modules,
counting the routes, and running its test suite. Nothing here is taken from a
README. Where a feature exists in code but cannot run in its environment, that
is stated rather than counted as working.

## Scale of the original

Measured 2 November 2026.

| | |
|---|---|
| Python | 134 files, 63,107 lines |
| HTML templates | 42 |
| HTTP routes | 379 |
| Scheduled jobs | 41 |
| Automated tests | 4,024, in 142 files |
| Pages that render a template | 19 |

## What was actually built

### Fully functional

**Gmail integration** — 1,036 lines. Reads threads, writes drafts, sends only
through a typed send-token guard. This is the one external API that genuinely
works end to end.

**Rule-based email classification** — `classify_email()` produces category,
sentiment, intent and priority from keyword and signal matching. Verified: the
module makes zero LLM calls. The comment in the source is explicit that this
is the hot path and must stay fast and free.

**Three-stage outreach sequence** — stage gaps of 4 and 5 days, with a cold
cut-off 5 days after stage 3. Sequence state is stored per prospect and a
reply stops the sequence.

**Task and commitment tracking** — a Google Sheet reached through an Apps
Script bridge, because the Sheets API is disabled on the Cloud project behind
the OAuth client. The bridge authenticates as the user with a Google bearer
token.

**Scheduled automation** — 41 jobs, including a morning briefing, an inbox
coverage sweep, posted-content detection and follow-up reminders.

**Test coverage** — 4,024 tests, which is unusual for a tool of this kind and
was the single most useful thing about working in it.

### Partially implemented or deliberately gated

**LLM reply drafting** — real, via Anthropic, but confined to drafting. The
model writes wording; it does not classify, route or decide.

**Automatic outreach sending** — the code exists and is inert. It requires two
separate settings to both be true, and neither is set. It runs as a dry run
and logs what it would have done.

**Slack** — a client with a real `chat.postMessage` call exists, but the
product position is that Leo writes the message and a human sends it.

### Present in code but blocked by the environment

**Google Sheets, Drive and Calendar clients** — 360, 185 and 302 lines
respectively. All three APIs are disabled on the Cloud project behind the OAuth
client and cannot be enabled by the signed-in account. Sheets is worked around
with the Apps Script bridge. Calendar has no equivalent workaround, so the
calendar in the product is a local JSON file rather than a real one.

This distinction matters and is easy to miss: the code reads as a working
Calendar integration. It is not one.

## What this demonstration recreates, and how

**No source code was copied.** The original was built in an employment
context, so this is an independent implementation. The original was used to
understand *what problems were worth solving and how a sensible system
behaves* — not as a source of code, templates, prompts, credentials or data.
Every file in this demo was written for it.

| Capability | In the original | In this demo |
|---|---|---|
| Creator CRM with pipeline stages | Yes | Rewritten, 22 fictional profiles |
| Email intent classification | Rule-based | Rewritten rule-based, with a visible reason per verdict |
| AI reply drafting | Anthropic | Simulated by default; optional live Anthropic |
| Human approval before anything goes out | Yes, typed send tokens | Yes, and nothing can send — there is no mail transport |
| Three-stage outreach sequence | Yes | Rewritten, with the reply-stops-chase rule |
| Campaign and deliverable tracking | Yes | Rewritten, 4 fictional campaigns |
| Daily briefing | Yes | Rewritten, computed live from demo data |
| Activity log | Yes | Rewritten, and labels simulated vs real |
| Gmail / Slack / Sheets / Calendar | Live or bridged | **Not reproduced.** No external service is contacted |

## What is deliberately absent here

- Any connection to a real mailbox, calendar, sheet or chat workspace
- Any credential, token or API key
- Any real creator, partner, campaign or message
- Any employer-owned template, prompt or copy

The demonstration is complete without them. Every number on every screen is
computed from the fictional dataset in `app/seed/`.
