"""Tests for the all-or-nothing upgrade engine.

"The template changed" is simulated by installing the project from the real
source (the OLD template) and upgrading from a modified COPY of the source
(the NEW template), which differs from the real one in core/roles/architect.md
(rendered into .engineering/roles, .claude/agents and .codex/agents).
"""
import json
import os
import shutil
import stat
import sys
import time
import unittest
import uuid
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from tests import guilda_test_isolation  # noqa: E402,F401  (isola o config do usuário)
import guilda.engine as engine  # noqa: E402
import guilda.payload as payload  # noqa: E402
import guilda.upgrade as upgrade  # noqa: E402

CHANGED = "core/roles/architect.md"
CHANGED_OUT = ".engineering/roles/architect.md"
OTHER_OUT = ".engineering/roles/backend.md"
MANIFEST = ".engineering/manifest.json"
RETIRED = ".engineering/old-file.md"


def extend(data):
    return data + b"\nExtra rule added by the new template.\n"


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.target = self.root / "consumer"
        self.new_src = self.copy_source("new-src", {CHANGED: extend})
        engine.install(ROOT, self.target, ["claude", "codex"], ["base"])

    def tearDown(self):
        resolved = self.root.resolve()
        self.assertEqual(resolved.parent, ROOT.parent.resolve())
        self.assertTrue(resolved.name.startswith("template-test-"))
        for attempt in range(6):
            try:
                shutil.rmtree(resolved, onerror=self._make_writable)
                break
            except PermissionError:
                if attempt == 5:
                    raise
                time.sleep(0.5 * (attempt + 1))

    @staticmethod
    def _make_writable(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def copy_source(self, name, edits, retired=()):
        dest = self.root / name
        for entry in payload.read(ROOT):
            out = dest / entry
            out.parent.mkdir(parents=True, exist_ok=True)
            data = (ROOT / entry).read_bytes()
            out.write_bytes(edits[entry](data) if entry in edits else data)
        (dest / "guilda").mkdir(exist_ok=True)
        shutil.copyfile(ROOT / "guilda" / "payload.txt", dest / "guilda" / "payload.txt")
        if retired:
            config = json.loads((dest / "template.json").read_text(encoding="utf-8"))
            config["retired_paths"] = list(retired)
            (dest / "template.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return dest

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes() for p in sorted(self.target.rglob("*")) if p.is_file()}

    def manifest(self):
        return json.loads((self.target / MANIFEST).read_text(encoding="utf-8"))

    def set_manifest(self, **changes):
        value = self.manifest()
        value.update(changes)
        (self.target / MANIFEST).write_bytes(engine.json_bytes(value))

    def own_retired(self, content=b"old shipped file\n"):
        """Make the project own a path the new template retires; returns the new source."""
        (self.target / RETIRED).write_bytes(content)
        files = self.manifest()["files"]
        files[RETIRED] = engine.digest(content)
        self.set_manifest(files=files)
        return self.copy_source("retired-src", {CHANGED: extend}, retired=[RETIRED])

    def test_untouched_project_has_empty_plan(self):
        plan = upgrade.plan_upgrade(ROOT, self.target)
        self.assertEqual(plan, upgrade.Plan([], [], [], [], False))

    def test_template_change_is_written(self):
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertIn(CHANGED_OUT, plan.write)
        self.assertEqual((plan.remove, plan.keep, plan.conflicts), ([], [], []))
        result = upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertIn(CHANGED_OUT, result["write"])
        self.assertIn(b"Extra rule", (self.target / CHANGED_OUT).read_bytes())
        engine.check(self.new_src, self.target)

    def test_user_edit_is_kept_when_template_unchanged(self):
        (self.target / OTHER_OUT).write_bytes(b"my own backend rules\n")
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertEqual(plan.keep, [OTHER_OUT])
        self.assertEqual(plan.conflicts, [])
        old_hash = self.manifest()["files"][OTHER_OUT]
        result = upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertEqual(result["kept"], [OTHER_OUT])
        self.assertEqual((self.target / OTHER_OUT).read_bytes(), b"my own backend rules\n")
        self.assertEqual(self.manifest()["files"][OTHER_OUT], old_hash)
        self.assertEqual(self.manifest()["files"][CHANGED_OUT], engine.digest((self.target / CHANGED_OUT).read_bytes()))
        # still classified as a local modification afterwards
        self.assertEqual(upgrade.plan_upgrade(self.new_src, self.target).keep, [OTHER_OUT])

    def test_user_edit_plus_template_change_is_conflict(self):
        (self.target / CHANGED_OUT).write_bytes(b"user edit\n")
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertEqual(plan.conflicts, [CHANGED_OUT])
        self.assertNotIn(CHANGED_OUT, plan.write)

    def test_foreign_file_at_shipped_path_is_conflict_unless_identical(self):
        files = self.manifest()["files"]
        del files[CHANGED_OUT]
        self.set_manifest(files=files)
        (self.target / CHANGED_OUT).write_bytes(b"foreign\n")
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertEqual(plan.conflicts, [CHANGED_OUT])
        _, desired = engine.render(self.new_src, ["claude", "codex"], ["base"])
        (self.target / CHANGED_OUT).write_bytes(desired[CHANGED_OUT])
        self.assertEqual(upgrade.plan_upgrade(self.new_src, self.target).conflicts, [])

    def test_path_new_in_template_and_absent_is_written(self):
        files = self.manifest()["files"]
        del files[CHANGED_OUT]
        self.set_manifest(files=files)
        (self.target / CHANGED_OUT).unlink()
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertIn(CHANGED_OUT, plan.write)

    def test_retired_path_is_removed(self):
        retired = self.own_retired()
        plan = upgrade.plan_upgrade(retired, self.target)
        self.assertEqual((plan.remove, plan.conflicts), ([RETIRED], []))
        result = upgrade.apply_upgrade(retired, self.target, plan, approved=False)
        self.assertEqual(result["remove"], [RETIRED])
        self.assertFalse((self.target / RETIRED).exists())
        self.assertNotIn(RETIRED, self.manifest()["files"])

    def test_retired_path_modified_by_user_is_conflict(self):
        retired = self.own_retired()
        (self.target / RETIRED).write_bytes(b"edited\n")
        plan = upgrade.plan_upgrade(retired, self.target)
        self.assertEqual((plan.remove, plan.conflicts), ([], [RETIRED]))
        before = self.snapshot()
        with self.assertRaises(upgrade.UpgradeRefused):
            upgrade.apply_upgrade(retired, self.target, plan, approved=False)
        self.assertEqual(self.snapshot(), before)
        upgrade.apply_upgrade(retired, self.target, plan, approved=True)
        self.assertFalse((self.target / RETIRED).exists())

    def test_user_added_file_never_touched(self):
        mine = self.target / ".claude/skills/mine/SKILL.md"
        mine.parent.mkdir(parents=True)
        mine.write_bytes(b"my skill\r\n")
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        for names in (plan.write, plan.remove, plan.keep, plan.conflicts):
            self.assertNotIn(".claude/skills/mine/SKILL.md", names)
        upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertEqual(mine.read_bytes(), b"my skill\r\n")

    def test_crlf_conversion_is_not_a_modification(self):
        # The recorded hash is that of the installed bytes; whatever line endings the checkout has,
        # an editor/git round trip to CRLF must not look like a user edit.
        for name in (OTHER_OUT, CHANGED_OUT):
            path = self.target / name
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        converted = (self.target / OTHER_OUT).read_bytes()
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertEqual((plan.keep, plan.conflicts), ([], []))
        self.assertIn(CHANGED_OUT, plan.write)
        self.assertNotIn(OTHER_OUT, plan.write)
        upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        _, desired = engine.render(self.new_src, ["claude", "codex"], ["base"])
        self.assertEqual((self.target / CHANGED_OUT).read_bytes(), desired[CHANGED_OUT])  # exact render bytes
        self.assertEqual((self.target / OTHER_OUT).read_bytes(), converted)  # identical content is not rewritten

    def test_conflicts_without_approval_write_nothing(self):
        (self.target / CHANGED_OUT).write_bytes(b"user edit\n")
        (self.target / OTHER_OUT).write_bytes(b"kept edit\n")
        before = self.snapshot()
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertTrue(plan.write)  # non-conflicting template changes exist and must stay unapplied
        with self.assertRaises(upgrade.UpgradeRefused) as ctx:
            upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertEqual(ctx.exception.plan, plan)
        self.assertEqual(self.snapshot(), before)

    def test_approved_overwrites_conflicts_without_backup(self):
        (self.target / CHANGED_OUT).write_bytes(b"user edit\n")
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        upgrade.apply_upgrade(self.new_src, self.target, plan, approved=True)
        self.assertIn(b"Extra rule", (self.target / CHANGED_OUT).read_bytes())
        names = [p.name.lower() for p in self.root.rglob("*")]
        self.assertFalse([n for n in names if n.endswith(".bak") or "backup" in n or n.endswith("~")])
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["consumer", "new-src"])

    def flaky_write(self, fail_on):
        real = Path.write_bytes
        calls = []

        def flaky(path, data):
            calls.append(path)
            if len(calls) == fail_on:
                raise OSError("disk full")
            return real(path, data)

        return flaky, calls

    def test_failure_mid_apply_restores_project(self):
        (self.target / OTHER_OUT).write_bytes(b"kept edit\n")
        before = self.snapshot()
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertGreaterEqual(len(plan.write), 3)
        flaky, calls = self.flaky_write(3)
        with mock.patch.object(Path, "write_bytes", flaky):
            with self.assertRaises(OSError):
                upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertEqual(len(calls), 3)
        self.assertEqual(self.snapshot(), before)

    def test_failure_restores_removed_and_created_files(self):
        retired = self.own_retired()
        missing = self.target / ".claude/commands/aws.md"
        files = self.manifest()["files"]
        missing.unlink()  # user deleted a managed file: it is re-created, and must vanish again on rollback
        before = self.snapshot()
        plan = upgrade.plan_upgrade(retired, self.target)
        self.assertEqual(plan.remove, [RETIRED])
        self.assertIn(".claude/commands/aws.md", plan.write)
        flaky, calls = self.flaky_write(len(plan.write))  # fail after the removal and most writes
        with mock.patch.object(Path, "write_bytes", flaky):
            with self.assertRaises(OSError):
                upgrade.apply_upgrade(retired, self.target, plan, approved=False)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(missing.exists())
        self.assertEqual(self.manifest()["files"], files)

    def test_manifest_written_last(self):
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        real = Path.write_bytes
        order = []

        def record(path, data):
            order.append(Path(path).relative_to(self.target).as_posix())
            return real(path, data)

        with mock.patch.object(Path, "write_bytes", record):
            upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertGreater(len(order), 1)
        self.assertEqual(order[-1], MANIFEST)
        self.assertEqual(order.count(MANIFEST), 1)

    def test_legacy_name_migrates_in_same_operation(self):
        self.set_manifest(name="engineering-template")
        with self.assertRaisesRegex(ValueError, "guilda upgrade"):
            engine.check(self.new_src, self.target)
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertTrue(plan.migrate_name)
        result = upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertTrue(result["migrated"])
        self.assertEqual(self.manifest()["name"], "guilda")
        _, desired = engine.render(self.new_src, ["claude", "codex"], ["base"])
        self.assertEqual(self.manifest()["files"], {p: engine.digest(v) for p, v in desired.items()})
        engine.check(self.new_src, self.target)

    def test_legacy_name_alone_migrates_with_empty_file_plan(self):
        self.set_manifest(name="engineering-template")
        plan = upgrade.plan_upgrade(ROOT, self.target)
        self.assertEqual((plan.write, plan.conflicts, plan.migrate_name), ([], [], True))
        upgrade.apply_upgrade(ROOT, self.target, plan, approved=False)
        self.assertEqual(self.manifest()["name"], "guilda")

    def test_newer_manifest_version_refused(self):
        self.set_manifest(version="99.0.0")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "newer"):
            upgrade.plan_upgrade(self.new_src, self.target)
        with self.assertRaisesRegex(ValueError, "newer"):
            upgrade.apply_upgrade(self.new_src, self.target, upgrade.Plan([], [], [], [], False), approved=True)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_plan_has_no_side_effects(self):
        (self.target / OTHER_OUT).write_bytes(b"edit\n")
        (self.target / CHANGED_OUT).write_bytes(b"edit\n")
        before = self.snapshot()
        upgrade.plan_upgrade(self.new_src, self.target)
        self.assertEqual(self.snapshot(), before)

    def test_package_manifest_is_not_upgradable(self):
        package = self.root / "package"
        engine.install(ROOT, package, ["claude"], ["base"], package=True)
        before = {str(p.relative_to(package)): p.read_bytes() for p in package.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(ValueError, "package manifest is not a project install"):
            upgrade.plan_upgrade(self.new_src, package)
        after = {str(p.relative_to(package)): p.read_bytes() for p in package.rglob("*") if p.is_file()}
        self.assertEqual(after, before)

    def test_deleted_managed_file_is_restored(self):
        (self.target / OTHER_OUT).unlink()
        before = self.snapshot()
        plan = upgrade.plan_upgrade(ROOT, self.target)
        self.assertEqual(plan, upgrade.Plan([OTHER_OUT], [], [], [], False))
        upgrade.apply_upgrade(ROOT, self.target, plan, approved=False)
        _, desired = engine.render(ROOT, ["claude", "codex"], ["base"])
        self.assertEqual((self.target / OTHER_OUT).read_bytes(), desired[OTHER_OUT])
        self.assertEqual({k: v for k, v in self.snapshot().items() if k != OTHER_OUT}, before)

    def test_lf_normalization_of_crlf_install_is_not_a_modification(self):
        path = self.target / CHANGED_OUT
        text = path.read_bytes().replace(b"\r\n", b"\n")
        crlf = text.replace(b"\n", b"\r\n")
        files = self.manifest()["files"]
        files[CHANGED_OUT] = engine.digest(crlf)  # installed on Windows with autocrlf
        self.set_manifest(files=files)
        path.write_bytes(text)  # later normalized to LF
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        self.assertIn(CHANGED_OUT, plan.write)  # template changed, user did not
        self.assertNotIn(CHANGED_OUT, plan.conflicts)
        self.assertEqual(plan.conflicts, [])

    def test_failed_rollback_is_reported_on_the_original_exception(self):
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        first = plan.write[0]
        flaky, _ = self.flaky_write(3)
        real_open = open

        def bad_open(file, *args, **kwargs):
            if Path(file) == self.target / first:
                raise OSError("locked")
            return real_open(file, *args, **kwargs)

        with mock.patch.object(Path, "write_bytes", flaky), mock.patch.object(upgrade, "open", bad_open, create=True):
            with self.assertRaises(OSError) as ctx:
                upgrade.apply_upgrade(self.new_src, self.target, plan, approved=False)
        self.assertEqual(str(ctx.exception), "disk full")
        notes = "\n".join(getattr(ctx.exception, "__notes__", []))
        self.assertIn(first, notes)
        self.assertNotIn(plan.write[1], notes)

    def test_stale_plan_is_rejected(self):
        plan = upgrade.plan_upgrade(self.new_src, self.target)
        (self.target / OTHER_OUT).write_bytes(b"edit after plan\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "stale"):
            upgrade.apply_upgrade(self.new_src, self.target, plan, approved=True)
        self.assertEqual(self.snapshot(), before)

    def test_parse_version(self):
        self.assertEqual(upgrade.parse_version("1.3.0"), (1, 3, 0))
        self.assertEqual(upgrade.parse_version("10.20.30-rc.1"), (10, 20, 30))
        for bad in ("", "1.3", "a.b.c", "1.3.0.1", "v1.3.0", None):
            with self.assertRaises(ValueError):
                upgrade.parse_version(bad)
        self.assertLess(upgrade.parse_version("1.9.0"), upgrade.parse_version("1.10.0"))


if __name__ == "__main__":
    unittest.main()
