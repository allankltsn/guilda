"""All-or-nothing upgrade of an installed project to the current template."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from guilda import engine

MANIFEST = ".engineering/manifest.json"
_VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)(?:[-+][a-zA-Z0-9.-]+)?\Z")


@dataclass(frozen=True)
class Plan:
    write: list[str]
    remove: list[str]
    keep: list[str]
    conflicts: list[str]
    migrate_name: bool


class UpgradeRefused(Exception):
    """Conflicts exist and were not approved; nothing was changed."""

    def __init__(self, plan: Plan):
        super().__init__("upgrade refused: conflicts need approval: " + ", ".join(plan.conflicts))
        self.plan = plan


def same_text(a: bytes, b: bytes) -> bool:
    return a.replace(b"\r\n", b"\n") == b.replace(b"\r\n", b"\n")


def parse_version(version: str) -> tuple[int, int, int]:
    match = _VERSION.match(version) if isinstance(version, str) else None
    if not match:
        raise ValueError(f"malformed version: {version!r}")
    return int(match[1]), int(match[2]), int(match[3])


def _analyze(source, target):
    """Pure: classify every managed path. Returns (plan, desired render, new manifest hashes, config)."""
    source = engine.safe_path(source)
    target = engine.safe_path(target)
    if target == source or source in target.parents:
        raise ValueError("source and target must be separate, non-nested trees")
    manifest = engine.read_manifest(target)
    engine.validate_manifest(source, manifest, allow_legacy=True)
    if manifest.get("package", False):
        raise ValueError("package manifest is not a project install; nothing to upgrade")
    config, desired = engine.render(source, manifest["providers"], manifest["profiles"], False, manifest.get("tiers"))
    if parse_version(manifest["version"]) > parse_version(config["version"]):
        raise ValueError(f"installed version {manifest['version']} is newer than template {config['version']}; refusing to downgrade")
    if target in source.parents:
        for name in desired:
            if source in (target / name).parents or (target / name) == source:
                raise ValueError(f"managed file would overwrite the template source: {name}")
    old = manifest["files"]
    new = {p: engine.digest(v) for p, v in desired.items()}
    write, remove, keep, conflicts = [], [], [], []
    for name in sorted(set(old) | set(new)):
        dest = engine.safe_path(target / engine.relative(name))
        for parent in dest.parents:
            if parent == target.parent:
                break
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"parent is not directory: {parent}")
        if dest.exists() and not dest.is_file():
            raise ValueError(f"not a file: {dest}")
        if not dest.exists():
            if name in new:
                write.append(name)  # new in the template, or a managed file the user deleted
            continue
        local = dest.read_bytes()
        if name not in new:  # retired by the template
            unmodified = _unmodified(local, old[name])
            (remove if unmodified else conflicts).append(name)
        elif name not in old:  # foreign file at a path the template now ships
            if not same_text(local, desired[name]):
                conflicts.append(name)
        else:
            if _unmodified(local, old[name]):
                if new[name] != old[name]:
                    write.append(name)
            elif same_text(local, desired[name]):
                pass  # the user already has the new content
            elif new[name] != old[name]:
                conflicts.append(name)
            else:
                keep.append(name)
    plan = Plan(write, remove, keep, conflicts, manifest["name"] in engine.LEGACY_NAMES)
    hashes = {p: (old[p] if p in keep else h) for p, h in new.items()}
    return plan, desired, hashes, config, manifest


def _unmodified(local: bytes, recorded: str) -> bool:
    # Only the hash of the installed version is known, so tolerate a CRLF conversion by git/editors.
    return engine.digest(local) == recorded or engine.digest(local.replace(b"\r\n", b"\n")) == recorded


def plan_upgrade(source, target) -> Plan:
    return _analyze(source, target)[0]


def _write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _restore(target: Path, originals: dict, created_dirs: list):
    # Deliberately independent of _write/Path.write_bytes: rollback must not share the failing path.
    for name, data in originals.items():
        dest = target / name
        try:
            if data is None:
                if dest.exists():
                    dest.unlink()
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as handle:
                    handle.write(data)
        except OSError:
            pass
    for directory in sorted(created_dirs, key=lambda d: len(d.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass


def apply_upgrade(source, target, plan: Plan, approved: bool) -> dict:
    current, desired, hashes, config, manifest = _analyze(source, target)
    if current != plan:
        raise ValueError("stale upgrade plan; run the plan again")
    if current.conflicts and not approved:
        raise UpgradeRefused(current)
    target = engine.safe_path(target)
    writes = sorted(set(current.write) | {c for c in current.conflicts if c in desired})
    removals = sorted(set(current.remove) | {c for c in current.conflicts if c not in desired})
    new_manifest = engine.json_bytes({"name": config["name"], "version": config["version"], "providers": manifest["providers"], "profiles": manifest["profiles"], "package": False, "tiers": dict(sorted((manifest.get("tiers") or {}).items())), "files": hashes})
    # Originals live in memory only, for rollback; never persisted.
    originals = {}
    for name in (*writes, *removals, MANIFEST):
        p = target / name
        originals[name] = p.read_bytes() if p.exists() else None
    created_dirs = []
    for name in (*writes, MANIFEST):
        for parent in (target / name).parents:
            if parent == target.parent:
                break
            if not parent.exists() and parent not in created_dirs:
                created_dirs.append(parent)
    try:
        for name in removals:
            (target / name).unlink()
        for name in writes:
            _write(target / name, desired[name])
        if originals[MANIFEST] != new_manifest:
            _write(target / MANIFEST, new_manifest)  # last
    except BaseException:
        _restore(target, originals, created_dirs)
        raise
    finally:
        originals.clear()
    return {"write": writes, "remove": removals, "kept": list(current.keep), "migrated": current.migrate_name}
