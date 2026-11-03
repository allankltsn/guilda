"""Shim: delega para guilda.engine (mantém `python scripts/template.py ...`)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from guilda.engine import *  # noqa: E402,F401,F403
from guilda.engine import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
