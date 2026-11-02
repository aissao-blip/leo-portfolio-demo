# Leo — an AI agent for creator partnership operations

## The problem

Running a creator partnership programme is mostly coordination, and the
coordination does not scale with headcount.

A single manager holds a roster of creators at different stages — some being
prospected, some mid-negotiation, some actively posting, some coming up for
renewal. Each one generates email. Each campaign has deliverables with dates.
Outreach needs following up on a schedule, except when it doesn't, because the
person already replied.

None of this is hard. All of it is relentless, and the failure modes are
quiet ones:

- A creator replies and the reply is missed for three days.
- A follow-up goes out to someone who already answered.
- A renewal passes without anyone noticing it was due.
- A deliverable slips and nobody finds out until the campaign report.

None of these show up as an error. They show up as a slightly worse
relationship, months later.

## Why I built Leo

I wanted to find out how much of that coordination could be handled by
software without handing it any authority it hadn't earned.

The organising principle: **the agent prepares, the human decides.** Leo reads
the inbox, works out what each message is asking for, drafts the reply, tracks
the sequence, watches the deadlines — and then stops, and waits. Nothing is
sent, committed, or agreed without a person seeing it first.

That constraint was not a compromise. It turned out to be the thing that made
the system usable: an agent you have to double-check is slower than doing it
yourself, and an agent that acts unilaterally in a relationship business is a
liability.

## Who it is for

A partnerships or creator marketing manager carrying a roster of 20 to 100
creators. The person who is the bottleneck not because the work is difficult
but because it all routes through one inbox.

## What it does

**Sorts the inbox by what each message asks of you.** Not by sender, not by
folder. The only question that matters at 9am is which of these needs a
decision — so that is the question the screen answers.

**Explains itself on every row.** Every classification comes with a sentence
naming the signals that produced it: *"Reads as negotiating terms — matched
'room to move', 'closer to'."* A label alone cannot be argued with. A sentence
can be checked in one read and corrected if it is wrong.

**Drafts the reply, and makes clear it has not sent it.** The draft appears
under the message for review. Approving it marks the thread handled and moves
the creator along the pipeline.

**Runs a three-stage outreach sequence that stops when it should.** Five days
between stages, and a hard stop the moment someone replies. That guard is a
rule, not a reminder, because chasing a person who already answered is the
most embarrassing thing this category of software does.

**Tracks campaigns, deliverables and renewals**, and assembles a daily
briefing from the current state of the data rather than from a stored summary.

## The architecture

Three layers, deliberately plain.

**Data** — JSON files. No database, no ORM, no migration step. The entire
state of the system can be opened in a text editor, which matters more than it
sounds: when an automated system does something surprising, being able to see
exactly what it was reasoning over is the difference between a five-minute fix
and an afternoon.

**Agent** — classification is rule-based and deterministic; language models
are used only for drafting wording. This split was a deliberate design
decision rather than a cost saving. Routing a message is a decision that
should be inspectable and reproducible. Writing a sentence is not.

**Interface** — server-rendered pages. Every number on screen is computed at
request time from the data, so the interface cannot drift away from the truth.

## My role

I designed and built it: the problem framing, the data model, the
classification rules, the agent behaviour, the interface, and the tests.

The work that took longest was not the AI. It was deciding what the system
was *not* allowed to do, and then enforcing those limits in code rather than
in documentation — typed tokens that make an unauthorised send impossible to
express, guards that refuse to chase someone who replied, an activity log that
distinguishes a decision the agent made from a change that actually happened.

## Key design decisions

**Rules for routing, models for wording.** Covered above. The practical effect
is that the same email always sorts the same way, and that behaviour can be
tested.

**Every verdict carries its reasoning.** Built because an unexplained
classification is one the user has to re-check by hand, which removes the
benefit entirely.

**Prepare, then stop.** No autonomous sending. The agent's output is always a
draft, a suggestion or a flag.

**Say which actions were real.** The activity log labels every entry as either
a simulated decision or a change that actually happened. Systems that blur the
two train people not to trust them.

**Write the reasoning into the code.** Comments in the original explain *why*
a rule exists, usually by naming the incident that caused it. Six months
later, that is the difference between a rule you can safely change and one
nobody dares touch.

## Challenges, and what they taught me

**Environment constraints shape architecture more than preferences do.** The
Google Cloud project behind the integration had Sheets, Drive and Calendar
APIs disabled and no route to enabling them. Sheets was solved with an Apps
Script bridge; Calendar had no equivalent, so that feature is honestly
diminished rather than faked. Shipping the limitation visibly was better than
shipping something that looked complete and wasn't.

**A display bug is worse than a sync failure.** At one point a record synced
correctly while the interface showed a stale cached status for five minutes.
Nothing was broken, and the user had no reason to doubt what they were
looking at — which is worse than an error, because an error tells you to
check.

**Date-dependent tests fail on calendar boundaries, not on code changes.**
Several tests broke on 1 November because their fixtures encoded October
dates. They now assert the rule rather than the date.

**Most of the value was in the boring parts.** Not the model. The guards, the
idempotency, the read-back-after-write, the one-definition-per-fact
discipline.

## Potential business value

Stated as mechanisms rather than numbers, because I have not measured
outcomes and will not invent them.

- **Fewer missed replies**, because the inbox is sorted by what needs a
  decision rather than by arrival.
- **Fewer wrong follow-ups**, because the sequence stops on reply as a rule.
- **Earlier visibility of renewals and deliverables**, because they are
  surfaced on a schedule rather than remembered.
- **Lower cost per decision**, because the drafting is done before the person
  arrives rather than during their day.

Any figure attached to these would be a guess. The mechanisms are real; the
magnitude would need measuring in a live programme.

---

*This case study describes a system built in a work context. The demonstration
accompanying it is an independent implementation with fictional data, written
separately. Nothing in the demonstration contains employer code, content or
records.*
