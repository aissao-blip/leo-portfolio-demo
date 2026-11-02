"""The agent: classify an email, draft a reply, write the briefing.

TWO MODES, AND THE DIFFERENCE IS VISIBLE

Simulated is the default and needs no API key, no account and no network. It
is deterministic: the same email always produces the same classification, the
same confidence and the same draft, which is what makes it demonstrable — you
can show it twice and it behaves the same way both times.

Live mode calls Anthropic with the key in your own .env. It is optional and
the application is fully usable without it. Which mode produced a given
answer is recorded on the answer itself and shown in the interface, because
"the AI wrote this" and "a rule wrote this" are different claims and a
portfolio piece should not blur them.

WHY THE SIMULATION IS RULE-BASED RATHER THAN RANDOM

It mirrors how the original system worked. Classification there was keyword
and signal matching on the hot path — fast, free, and good enough to route a
message — with a language model reserved for drafting the reply, where the
wording actually matters. The same split is reproduced here.
"""
from __future__ import annotations

import os
import re

# ── intents ─────────────────────────────────────────────────────────────────
# Each is (intent, label, what it means for the pipeline, the signals that
# point at it). Ordered: the first match wins, so the more consequential
# intents are tested before the softer ones.
INTENTS = [
    ("decline", "Declining", None, [
        "not right now", "not a fit", "fully booked", "pass on this",
        "no thanks", "unable to", "won't be able"]),
    ("negotiating", "Negotiating terms", "Negotiating", [
        "room to move", "closer to", "higher", "rate", "more than",
        "budget", "counter", "hoping for"]),
    ("scheduling", "Rescheduling", None, [
        "move our call", "reschedule", "push", "another time",
        "can we meet", "availability", "next week"]),
    ("deliverable", "Delivered content", "Active Partner", [
        "posted", "went live", "published", "here's the link",
        "uploaded", "link below"]),
    ("invoice", "Sending an invoice", None, [
        "invoice", "payment", "paid", "finance", "remittance"]),
    ("question", "Asking a question", "In Conversation", [
        "can you confirm", "before i sign", "question", "would i still",
        "what does", "how does", "clarify"]),
    ("interested", "Interested", "In Conversation", [
        "love to hear", "tell me more", "interested", "sounds good",
        "what kind of", "i'd love"]),
]

FYI = ("no action needed", "just wanted to say", "loved the", "fyi", "nice work")


def classify(subject: str, body: str) -> dict:
    """{intent, label, reason, confidence, needs_decision, suggest_stage, mode}

    The `reason` is the point. A label on its own cannot be argued with; a
    sentence naming the words that produced it can be, and a reviewer who can
    see why a thing was sorted can correct it in one read.
    """
    text = f"{subject} {body}".lower()

    for intent, label, stage, signals in INTENTS:
        hits = [s for s in signals if s in text]
        if hits:
            quoted = ", ".join(f'"{h}"' for h in hits[:2])
            return {
                "intent": intent,
                "label": label,
                "reason": f"Reads as {label.lower()} — matched {quoted}.",
                "confidence": min(0.95, 0.62 + 0.11 * len(hits)),
                "needs_decision": intent not in ("deliverable", "invoice"),
                "suggest_stage": stage,
                "mode": "simulated",
            }

    if any(s in text for s in FYI):
        return {"intent": "fyi", "label": "No action needed",
                "reason": "Nothing is being asked of you — it reads as an update.",
                "confidence": 0.74, "needs_decision": False,
                "suggest_stage": None, "mode": "simulated"}

    return {"intent": "unclear", "label": "Unclear",
            "reason": "No signal strong enough to classify this. Read it yourself.",
            "confidence": 0.3, "needs_decision": True,
            "suggest_stage": None, "mode": "simulated"}


# ── drafting ────────────────────────────────────────────────────────────────

DRAFTS = {
    "interested": (
        "Hi {first},\n\nGreat to hear from you. Here is the shape of it: a "
        "three-month partnership at ${fee}/month, with the deliverables agreed "
        "up front so you know exactly what you are committing to.\n\nFor "
        "someone in the {tier} tier we usually land on one in-feed piece a "
        "month plus a story set, but that is a conversation rather than a "
        "template — tell me what performs for your audience and we will build "
        "it round that.\n\nWould a 20-minute call this week suit?\n\nBest,\n"
        "Aissa"),
    "question": (
        "Hi {first},\n\nGood question, and a fair one to ask before signing.\n\n"
        "The agreement is non-exclusive. You are free to work with other brands, "
        "including in the same category — the only ask is that a competing "
        "product does not appear in the same piece of content as ours.\n\n"
        "Anything else you want settled before we go ahead?\n\nBest,\nAissa"),
    "negotiating": (
        "Hi {first},\n\nThanks for being straight about it. Audience growth of "
        "that order is a reasonable basis to revisit the number.\n\nBefore I "
        "take it further internally, could you send me your last three months "
        "of reach and engagement? With that in hand I can make the case "
        "properly rather than argue it in the abstract.\n\nBest,\nAissa"),
    "scheduling": (
        "Hi {first},\n\nNo problem at all — job sites win.\n\nI have Tuesday "
        "and Wednesday mornings open next week. Send whichever suits and I will "
        "put it in.\n\nBest,\nAissa"),
    "deliverable": (
        "Hi {first},\n\nSeen it — thank you, that is exactly the angle we were "
        "after.\n\nI have logged it against the campaign. Nothing else needed "
        "from you this cycle.\n\nBest,\nAissa"),
    "invoice": (
        "Hi {first},\n\nReceived, thank you. I have passed it to finance; the "
        "usual turnaround is about two weeks from approval.\n\nI will chase it "
        "if it slips past that.\n\nBest,\nAissa"),
    "decline": (
        "Hi {first},\n\nCompletely understood, and thank you for being direct "
        "about the timing.\n\nI will make a note to come back to you in Q1. If "
        "anything frees up before then you know where I am.\n\nBest,\nAissa"),
    "fyi": (
        "Hi {first},\n\nThat is good to hear — I have passed it on to the team "
        "that built it.\n\nBest,\nAissa"),
    "unclear": (
        "Hi {first},\n\nThanks for getting in touch. So I answer the right "
        "question — could you tell me a little more about what you need from "
        "me here?\n\nBest,\nAissa"),
}


def draft_reply(message: dict, creator: dict, verdict: dict) -> dict:
    """A reply for review. Never sent — this demo has no mail transport."""
    if live_available() and os.environ.get("LEO_DEMO_AI_MODE") == "live":
        drafted = _draft_live(message, creator, verdict)
        if drafted:
            return {"body": drafted, "mode": "live"}
    first = (creator.get("name") or "there").split()[0]
    body = DRAFTS.get(verdict["intent"], DRAFTS["unclear"]).format(
        first=first, fee=creator.get("monthly_fee", 500),
        tier=(creator.get("tier") or "micro").lower())
    return {"body": body, "mode": "simulated"}


def live_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _draft_live(message: dict, creator: dict, verdict: dict):
    """Optional. Returns None on any failure so the demo never breaks."""
    try:
        import anthropic
    except ImportError:
        return None
    try:
        client = anthropic.Anthropic()
        prompt = (
            "You manage creator partnerships for a home-services software "
            "company. Write a short, warm, direct reply. No em dashes. Sign "
            "off as Aissa.\n\n"
            f"Creator: {creator.get('name')} ({creator.get('tier')} tier, "
            f"{creator.get('platform')}, ${creator.get('monthly_fee')}/month)\n"
            f"They are: {verdict['label']}\n"
            f"Subject: {message['subject']}\n"
            f"Their message:\n{message['body']}\n")
        reply = client.messages.create(
            model=os.environ.get("LEO_DEMO_MODEL", "claude-opus-4-7"),
            max_tokens=600, messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in reply.content if b.type == "text").strip()
    except Exception:
        return None


# ── the daily briefing ──────────────────────────────────────────────────────

def briefing(creators, campaigns, inbox) -> dict:
    """What a person would want to know first, assembled from the data.

    Counts are computed, never written down. If the dataset changes the
    briefing changes with it, which is the difference between a briefing and
    a screenshot of one.
    """
    from datetime import date

    today = date.today()
    waiting = [m for m in inbox if m["status"] != "handled"]
    deciding = []
    for m in waiting:
        if classify(m["subject"], m["body"])["needs_decision"]:
            deciding.append(m)

    due = []
    for c in creators:
        nd = (c.get("sequence") or {}).get("next_due")
        if nd and nd <= today.isoformat():
            due.append(c)

    renewals = [c for c in creators if c["stage"] == "Renewal Due"]

    deadlines = []
    for cmp in campaigns:
        if cmp["status"] != "active":
            continue
        for p in cmp["participants"]:
            if p["completed"] < p["total"] and p["due"] <= (today.replace(
                    day=min(28, today.day)) ).isoformat():
                deadlines.append({"campaign": cmp["name"], **p})

    actions = []
    if deciding:
        actions.append(f"Answer {len(deciding)} email"
                       f"{'' if len(deciding)==1 else 's'} waiting on a decision.")
    if renewals:
        actions.append(f"{len(renewals)} partnership"
                       f"{'' if len(renewals)==1 else 's'} up for renewal.")
    if due:
        actions.append(f"{len(due)} outreach follow-up"
                       f"{'' if len(due)==1 else 's'} are due.")
    if deadlines:
        actions.append(f"{len(deadlines)} campaign deliverable"
                       f"{'' if len(deadlines)==1 else 's'} past their date.")
    if not actions:
        actions.append("Nothing is waiting on you.")

    return {"needs_decision": deciding, "follow_ups": due,
            "renewals": renewals, "deadlines": deadlines,
            "actions": actions, "generated_for": today.isoformat()}
