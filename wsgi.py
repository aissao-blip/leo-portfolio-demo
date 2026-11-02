"""WSGI entrypoint for hosted deployments (Render, Fly, any gunicorn host).

`run.py` is the local launcher and calls `store.ensure()` itself inside
`main()`. A production server imports the app object instead and never calls
`main()`, so the seed copy has to happen here or the first request hits a
dataset that was never created.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import store
from app.server import app

store.ensure()

__all__ = ["app"]
