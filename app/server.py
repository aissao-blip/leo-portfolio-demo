"""Leo Portfolio Demo — the web application.

Flask, Jinja2 and the standard library. No database, no build step, no paid
API. `python run.py` and it is up.

Nothing in here sends an email, posts a message, or reaches any external
service. The only optional network call is to Anthropic, and only when you
put your own key in .env and switch the mode on.
"""
from __future__ import annotations

import os
from datetime import date, datetime

from flask import Flask, jsonify, redirect, render_template, request, url_for

from . import agent, store

app = Flask(__name__)
app.config["DEMO"] = True

STAGES = ["New", "Contacted", "In Conversation", "Negotiating",
          "Active Partner", "Renewal Due", "Paused", "Declined"]


@app.context_processor
def shared():
    inbox = store.load("inbox")
    waiting = sum(1 for m in inbox if m["status"] != "handled")
    return {"nav_waiting": waiting,
            "ai_mode": "live" if (agent.live_available() and
                                  os.environ.get("LEO_DEMO_AI_MODE") == "live")
                       else "simulated",
            "today": date.today().isoformat()}


def _ago(hours: int) -> str:
    if hours < 1:
        return "just now"
    if hours < 24:
        return f"{hours}h ago"
    days = round(hours / 24)
    return f"{days}d ago"


app.jinja_env.filters["ago"] = _ago


# ── 1. Dashboard ────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    creators = store.load("creators")
    campaigns = store.load("campaigns")
    inbox = store.load("inbox")
    activity = store.load("activity")

    waiting = [m for m in inbox if m["status"] != "handled"]
    deciding = []
    for m in waiting:
        m["verdict"] = agent.classify(m["subject"], m["body"])
        if m["verdict"]["needs_decision"]:
            deciding.append(m)
    active = [c for c in creators if c["stage"] == "Active Partner"]
    in_seq = [c for c in creators
              if (c.get("sequence") or {}).get("status") == "running"]
    renewals = [c for c in creators if c["stage"] == "Renewal Due"]
    live = [c for c in campaigns if c["status"] == "active"]

    by_stage = [{"stage": s, "count": sum(1 for c in creators if c["stage"] == s)}
                for s in STAGES]

    return render_template(
        "dashboard.html",
        total=len(creators), active=len(active), in_sequence=len(in_seq),
        waiting=len(waiting), deciding=deciding[:5], deciding_total=len(deciding),
        renewals=renewals, campaigns=live, by_stage=by_stage,
        activity=activity[:6],
        progress=round(sum(c["progress"] for c in live) / len(live)) if live else 0,
    )


# ── 2. Creator CRM ──────────────────────────────────────────────────────────

@app.route("/creators")
def creators_page():
    rows = store.load("creators")
    stage = request.args.get("stage", "")
    query = request.args.get("q", "").strip().lower()
    if stage:
        rows = [c for c in rows if c["stage"] == stage]
    if query:
        rows = [c for c in rows if query in " ".join(
            str(c.get(k, "")) for k in
            ("name", "handle", "company", "trade", "city", "platform")).lower()]
    counts = {s: sum(1 for c in store.load("creators") if c["stage"] == s)
              for s in STAGES}
    return render_template("creators.html", creators=rows, stages=STAGES,
                           counts=counts, stage=stage, q=request.args.get("q", ""))


@app.route("/creators/<cid>")
def creator_detail(cid):
    person = store.creator(cid)
    if not person:
        return redirect(url_for("creators_page"))
    messages = [m for m in store.load("inbox") if m["creator_id"] == cid]
    campaigns = [c for c in store.load("campaigns")
                 if any(p["creator_id"] == cid for p in c["participants"])]
    return render_template("creator_detail.html", c=person, stages=STAGES,
                           messages=messages, campaigns=campaigns)


@app.route("/creators/<cid>/stage", methods=["POST"])
def move_stage(cid):
    stage = (request.form.get("stage") or "").strip()
    if stage not in STAGES:
        return redirect(url_for("creator_detail", cid=cid))
    person = store.creator(cid)
    was = person["stage"] if person else "?"
    store.update_creator(cid, stage=stage,
                         last_activity=date.today().isoformat())
    store.log(f"Moved {person['name']} from {was} to {stage}",
              kind="real", actor="you")
    return redirect(url_for("creator_detail", cid=cid))


# ── 3. AI email agent ───────────────────────────────────────────────────────

@app.route("/inbox")
def inbox_page():
    rows = store.load("inbox")
    for m in rows:
        m["verdict"] = agent.classify(m["subject"], m["body"])
    waiting = [m for m in rows if m["status"] != "handled"]
    handled = [m for m in rows if m["status"] == "handled"]
    return render_template("inbox.html",
                           deciding=[m for m in waiting if m["verdict"]["needs_decision"]],
                           fyi=[m for m in waiting if not m["verdict"]["needs_decision"]],
                           handled=handled)


@app.route("/inbox/<mid>/draft", methods=["POST"])
def make_draft(mid):
    rows = store.load("inbox")
    msg = next((m for m in rows if m["id"] == mid), None)
    if not msg:
        return jsonify({"ok": False, "error": "No such message"}), 404
    person = store.creator(msg["creator_id"]) or {}
    verdict = agent.classify(msg["subject"], msg["body"])
    drafted = agent.draft_reply(msg, person, verdict)
    msg["draft"] = drafted["body"]
    msg["draft_mode"] = drafted["mode"]
    msg["status"] = "drafted"
    store.save("inbox", rows)
    store.log(f"Drafted a reply to {msg['from_name']} ({drafted['mode']} mode) "
              f"— not sent", kind="simulated")
    return jsonify({"ok": True, "draft": drafted["body"], "mode": drafted["mode"],
                    "verdict": verdict})


@app.route("/inbox/<mid>/approve", methods=["POST"])
def approve(mid):
    """Approve the draft. In a real deployment this is where a send would be
    queued; here it marks the thread handled and moves the creator on."""
    rows = store.load("inbox")
    msg = next((m for m in rows if m["id"] == mid), None)
    if not msg or not msg.get("draft"):
        return jsonify({"ok": False, "error": "Nothing drafted yet"}), 400
    msg["status"] = "handled"
    msg["approved"] = True
    store.save("inbox", rows)

    verdict = agent.classify(msg["subject"], msg["body"])
    moved = None
    if verdict.get("suggest_stage"):
        person = store.creator(msg["creator_id"])
        if person and person["stage"] != verdict["suggest_stage"]:
            store.update_creator(person["id"], stage=verdict["suggest_stage"],
                                 last_activity=date.today().isoformat())
            moved = f"{person['name']} → {verdict['suggest_stage']}"
    store.log(f"Approved the reply to {msg['from_name']}. No email was sent — "
              f"this demonstration has no mail transport.", kind="simulated")
    if moved:
        store.log(f"Pipeline updated: {moved}", kind="real", actor="agent")
    return jsonify({"ok": True, "moved": moved})


# ── 4. Outreach sequences ───────────────────────────────────────────────────

SEQUENCE = [
    (1, "Intro", "Why I think this is a fit, and what a partnership looks like."),
    (2, "Following up", "A short nudge with one piece of proof attached."),
    (3, "Last note", "A final note that closes the loop and leaves the door open."),
]


@app.route("/outreach")
def outreach_page():
    creators = store.load("creators")
    running = [c for c in creators
               if (c.get("sequence") or {}).get("status") == "running"]
    replied = [c for c in creators
               if (c.get("sequence") or {}).get("status") == "replied"]
    not_started = [c for c in creators
                   if (c.get("sequence") or {}).get("status") == "not started"
                   and c["stage"] in ("New", "Contacted")]
    return render_template("outreach.html", sequence=SEQUENCE, running=running,
                           replied=replied, not_started=not_started)


@app.route("/outreach/<cid>/advance", methods=["POST"])
def advance(cid):
    """Move a creator to the next stage of the sequence.

    Refuses once they have replied. That refusal is the interesting part: the
    single most embarrassing failure in outreach software is chasing somebody
    who already answered you, so the stop is a rule rather than a reminder.
    """
    from datetime import timedelta

    rows = store.load("creators")
    person = next((c for c in rows if c["id"] == cid), None)
    if not person:
        return jsonify({"ok": False, "error": "No such creator"}), 404

    seq = person.setdefault("sequence", {"stage": 0, "status": "not started",
                                         "sent": [], "next_due": None,
                                         "stop_reason": ""})
    if seq.get("status") == "replied":
        return jsonify({"ok": False, "stopped": True,
                        "error": "They replied. The sequence stops here."}), 400
    if seq.get("stage", 0) >= 3:
        seq["status"] = "finished"
        seq["next_due"] = None
        seq["stop_reason"] = "All three stages sent."
        store.save("creators", rows)
        return jsonify({"ok": True, "finished": True})

    seq["stage"] = seq.get("stage", 0) + 1
    seq["status"] = "running"
    seq["sent"].append({"stage": seq["stage"], "on": date.today().isoformat(),
                        "subject": SEQUENCE[seq["stage"] - 1][1]})
    seq["next_due"] = ((date.today() + timedelta(days=5)).isoformat()
                       if seq["stage"] < 3 else None)
    if person["stage"] == "New":
        person["stage"] = "Contacted"
    person["last_activity"] = date.today().isoformat()
    store.save("creators", rows)
    store.log(f"Simulated stage {seq['stage']} of the sequence to "
              f"{person['name']} — nothing was sent", kind="simulated")
    return jsonify({"ok": True, "stage": seq["stage"],
                    "next_due": seq["next_due"]})


# ── 5. Campaigns ────────────────────────────────────────────────────────────

@app.route("/campaigns")
def campaigns_page():
    return render_template("campaigns.html", campaigns=store.load("campaigns"))


@app.route("/campaigns/<cid>/tick", methods=["POST"])
def tick_deliverable(cid):
    rows = store.load("campaigns")
    who = request.form.get("creator_id") or (request.json or {}).get("creator_id")
    for cmp in rows:
        if cmp["id"] != cid:
            continue
        for p in cmp["participants"]:
            if p["creator_id"] == who and p["completed"] < p["total"]:
                p["completed"] += 1
                done = sum(x["completed"] for x in cmp["participants"])
                total = sum(x["total"] for x in cmp["participants"]) or 1
                cmp["progress"] = round(100 * done / total)
                store.save("campaigns", rows)
                store.log(f"Marked a deliverable complete for {p['name']} "
                          f"on {cmp['name']}", kind="real", actor="you")
                return jsonify({"ok": True, "completed": p["completed"],
                                "progress": cmp["progress"]})
    return jsonify({"ok": False, "error": "Nothing left to tick"}), 400


# ── 6. Daily briefing ───────────────────────────────────────────────────────

@app.route("/briefing")
def briefing_page():
    brief = agent.briefing(store.load("creators"), store.load("campaigns"),
                           store.load("inbox"))
    for m in brief["needs_decision"]:
        m["verdict"] = agent.classify(m["subject"], m["body"])
    return render_template("briefing.html", b=brief)


# ── 7. Activity log ─────────────────────────────────────────────────────────

@app.route("/activity")
def activity_page():
    rows = store.load("activity")
    return render_template("activity.html", rows=rows,
                           simulated=sum(1 for r in rows if r["kind"] == "simulated"),
                           real=sum(1 for r in rows if r["kind"] == "real"))


# ── reset ───────────────────────────────────────────────────────────────────

@app.route("/reset", methods=["POST"])
def reset():
    store.reset()
    store.log("Restored the fictional demonstration dataset", kind="real",
              actor="you")
    return redirect(url_for("dashboard"))


def main():
    store.ensure()
    port = int(os.environ.get("PORT", "5055"))
    # Local runs stay on the loopback interface. A host that routes external
    # traffic (Render, Fly) sets HOST=0.0.0.0 so the container is reachable.
    host = os.environ.get("HOST", "127.0.0.1")
    print("\n  Leo Portfolio Demo")
    print(f"  http://{'127.0.0.1' if host == '127.0.0.1' else host}:{port}\n")
    print(f"  AI mode: {'live (Anthropic)' if agent.live_available() and os.environ.get('LEO_DEMO_AI_MODE') == 'live' else 'simulated — no API key needed'}")
    print("  No email is sent and no external service is contacted.\n")
    app.run(host=host, port=port, debug=False)
