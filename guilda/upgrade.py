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
    strays = set(engine.validate_manifest(source, manifest, allow_legacy=True))
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
        if name in strays:
            # Never shipped on purpose (1.3.0 from a dirty checkout): remove the intact copy; a
            # changed one stays on disk, dropped from the manifest (no longer managed).
            (remove if _unmodified(local, old[name]) else keep).append(name)
        elif name not in new:  # retired by the template
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
    # Only the hash of the installed version is known, so tolerate CRLF<->LF conversion by git/editors.
    lf = local.replace(b"\r\n", b"\n")
    return recorded in (engine.digest(local), engine.digest(lf), engine.digest(lf.replace(b"\n", b"\r\n")))


def plan_upgrade(source, target) -> Plan:
    return _analyze(source, target)[0]


def verify(source, target) -> Plan:
    """After an upgrade nothing is left to write, remove or approve.

    Unlike `engine.check`, files the upgrade deliberately kept (user edits on files the template
    did not change; their manifest hash stays the installed one) are not drift.
    """
    plan = plan_upgrade(source, target)
    pending = [*plan.write, *plan.remove, *plan.conflicts]
    if pending or plan.migrate_name:
        raise ValueError("post-upgrade verification failed: " + (", ".join(pending) or "legacy manifest name"))
    return plan


def _write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _restore(target: Path, originals: dict, created_dirs: list) -> list:
    """Best-effort rollback; returns the paths that could not be restored."""
    # Deliberately independent of _write/Path.write_bytes: rollback must not share the failing path.
    failed = []
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
            failed.append(name)
    for directory in sorted(created_dirs, key=lambda d: len(d.parts), reverse=True):
        try:
            directory.rmdir()
        except OSError:
            pass
    return failed


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
    except BaseException as exc:
        failed = _restore(target, originals, created_dirs)
        if failed:
            exc.add_note("upgrade rollback incomplete; the project may be in a mixed state. Not restored: " + ", ".join(failed))
        raise
    finally:
        originals.clear()
    _prune_empty_dirs(target, removals)
    return {"write": writes, "remove": removals, "kept": list(current.keep), "migrated": current.migrate_name}


def _prune_empty_dirs(target: Path, removed) -> None:
    """Best effort, after success: drop directories the removals left empty (never the target)."""
    for name in removed:
        for parent in (target / name).parents:
            if parent == target or target not in parent.parents:
                break
            try:
                parent.rmdir()  # fails (and stops) on the first non-empty directory
            except OSError:
                break
