#!/usr/bin/env python3
"""Leo Portfolio Demo — launcher.

    python run.py

Then open http://127.0.0.1:5055
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load .env if present. No dependency on python-dotenv: it is six lines.
env = Path(__file__).resolve().parent / ".env"
if env.exists():
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

from app.server import main

if __name__ == "__main__":
    main()
