# Portfolio description

## Short — for a portfolio tile (40 words)

**Leo — AI agent for creator partnership operations.** Sorts an inbox by what
each message asks of you, explains every decision in a sentence, drafts the
reply, and refuses to chase a creator who already replied. The agent prepares;
the person decides.

## Medium — for a portfolio page (120 words)

**Leo — AI agent for creator partnership operations**

Running a creator programme is mostly coordination, and its failure modes are
quiet: a reply missed for three days, a follow-up sent to someone who already
answered, a renewal that passes unnoticed.

Leo is an agent built around one constraint — it prepares, and a person
decides. It sorts the inbox by what each message asks of you rather than who
sent it, and every classification carries the sentence that produced it, so a
wrong call can be spotted in one read. It drafts replies, runs a three-stage
outreach sequence that stops the moment someone replies, and tracks campaign
deliverables and renewals.

Built with Python and Flask. Rules for routing, language models for wording.

## LinkedIn post

I built an AI agent for creator partnership operations, and the most useful
decision I made was about what it isn't allowed to do.

Leo reads the partnership inbox, works out what each message is asking for,
drafts the reply, tracks the outreach sequence, and watches campaign
deadlines and renewals. Then it stops and waits for me.

Three things I'd take to any agent project:

**Sort by what the work asks of you.** Most inboxes sort by sender or folder.
The only question that matters first thing in the morning is which of these
needs a decision — so that's the question the screen answers.

**Make the reasoning readable.** Every classification comes with the sentence
that produced it: "Reads as negotiating terms — matched 'room to move'." A
label you can't argue with is one you have to re-check by hand, which removes
the point of having it.

**Put the limits in the code, not the documentation.** The sequence doesn't
*remind* you not to chase someone who replied — it refuses. The agent can't
send mail because there's no mail transport to reach.

Most of the work wasn't the AI. It was the guards, the idempotency, and
keeping one definition of each fact so two parts of the system couldn't
disagree about what was true.

I've built a standalone demonstration with fictional data that runs locally —
independent code, no employer systems involved. Happy to walk anyone through
it.

#AI #Automation #CreatorMarketing #ProductOperations #Python

## Positioning

This sits at the intersection of creator marketing, applied AI, business
operations and automation. It demonstrates:

- Identifying an operational problem from doing the work, not from a brief
- Designing an agent with deliberate limits on its authority
- Choosing rules over models where decisions must be inspectable
- Shipping guards in code rather than warnings in documentation
- Being honest about what a system cannot do
