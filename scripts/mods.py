"""Shim: reexporta guilda.mods."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from guilda.mods import *  # noqa: E402,F401,F403
