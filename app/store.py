"""The demo's data layer: JSON files, copied from seed on first run.

Deliberately not a database. A recruiter should be able to clone this, run one
command, and have it work — and should be able to open data/creators.json in a
text editor and see exactly what the application is reasoning over. Nothing is
hidden behind an ORM or a migration step.

`reset()` copies the seed files back over the working ones, so the demo can be
driven hard, broken, and restored in a second. Every write goes through
`save()`, which writes to a temp file and renames, so an interrupted write
cannot leave a half-file behind.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = Path(__file__).resolve().parent / "seed"
DATA = ROOT / "data"

FILES = ("creators", "campaigns", "inbox", "activity")


def ensure() -> None:
    """Create the working copy on first run. Never overwrites existing data."""
    DATA.mkdir(exist_ok=True)
    for name in FILES:
        target = DATA / f"{name}.json"
        if not target.exists():
            shutil.copy(SEED / f"{name}.json", target)


def reset() -> None:
    """Put the fictional dataset back exactly as shipped."""
    DATA.mkdir(exist_ok=True)
    for name in FILES:
        shutil.copy(SEED / f"{name}.json", DATA / f"{name}.json")


def load(name: str):
    ensure()
    with open(DATA / f"{name}.json") as handle:
        return json.load(handle)


def save(name: str, rows) -> None:
    DATA.mkdir(exist_ok=True)
    tmp = DATA / f"{name}.json.tmp"
    with open(tmp, "w") as handle:
        json.dump(rows, handle, indent=2)
    os.replace(tmp, DATA / f"{name}.json")


def creator(cid: str):
    return next((c for c in load("creators") if c["id"] == cid), None)


def update_creator(cid: str, **fields):
    rows = load("creators")
    for row in rows:
        if row["id"] == cid:
            row.update(fields)
            save("creators", rows)
            return row
    return None


def log(text: str, kind: str = "simulated", actor: str = "agent") -> dict:
    """Record something that happened.

    `kind` is the whole point of this log. "simulated" means the demo decided
    something; "real" means a file on this machine actually changed. A demo
    that blurs those two is a demo that lies about what it does.
    """
    from datetime import datetime

    rows = load("activity")
    entry = {"id": f"act-{len(rows) + 1:03d}", "kind": kind, "text": text,
             "actor": actor, "at": datetime.now().isoformat(timespec="seconds")}
    rows.insert(0, entry)
    save("activity", rows[:200])
    return entry
