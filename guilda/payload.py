"""Allowlist of the files that make up the installed template payload."""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

FORBIDDEN: tuple[str, ...] = ("graphify-out", "docs/superpowers", "plans/", "specs/", ".worktrees", ".dev", "__pycache__")
TRACKED = ("core", "profiles", "adapters", "integrations", "template.json")
LIST_NAME = "payload.txt"
DATA_PREFIX = "guilda/_data/"


def _parts(value: str) -> tuple[str, ...]:
    return tuple(p for p in value.split("/") if p)


def is_forbidden(path: str) -> bool:
    """True when a forbidden segment (or segment prefix path) appears anywhere in path."""
    parts = _parts(path.replace("\\", "/"))
    for item in FORBIDDEN:
        needle = _parts(item)
        for i in range(len(parts) - len(needle) + 1):
            if parts[i:i + len(needle)] == needle:
                return True
    return False


def _check_entry(path: str) -> None:
    p = Path(path)
    if not path or p.is_absolute() or ".." in p.parts or "\\" in path or ":" in path:
        raise ValueError(f"unsafe payload path: {path}")
    if is_forbidden(path):
        raise ValueError(f"forbidden payload path: {path}")


def list_file(root: Path) -> Path:
    """Checkout layout keeps the list in <root>/guilda; the wheel keeps it next to _data."""
    root = Path(root)
    primary = root / "guilda" / LIST_NAME
    if primary.is_file() or root.name != "_data":
        return primary
    return root.parent / LIST_NAME


def read(root: Path) -> list[str]:
    text = list_file(root).read_text(encoding="utf-8")
    entries = sorted({line.strip() for line in text.splitlines() if line.strip()})
    for entry in entries:
        _check_entry(entry)
    return entries


def generate(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", *TRACKED], cwd=root, capture_output=True, check=True,
    )
    entries = sorted({item.decode("utf-8") for item in result.stdout.split(b"\0") if item})
    for entry in entries:
        _check_entry(entry)
    return entries


def wheel_force_include(root: Path) -> dict[str, str]:
    """Absolute source path -> destination inside the wheel, for every payload file."""
    root = Path(root)
    entries = set(read(root)) | {"template.json"}
    return {str(root / e): DATA_PREFIX + e for e in sorted(entries)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m guilda.payload")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    wanted = generate(root)
    target = root / "guilda" / LIST_NAME
    if args.write:
        target.write_text("".join(f"{e}\n" for e in wanted), encoding="utf-8", newline="\n")
        return 0
    current = set(read(root)) if target.is_file() else set()
    missing, extra = sorted(set(wanted) - current), sorted(current - set(wanted))
    if missing or extra:
        for e in missing:
            print(f"missing from payload.txt: {e}", file=sys.stderr)
        for e in extra:
            print(f"stale in payload.txt: {e}", file=sys.stderr)
        print("run: python -m guilda.payload --write", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
