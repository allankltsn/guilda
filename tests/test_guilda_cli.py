"""Tests for the `guilda` command line.

Installing renders ~330 files, so a pristine project and a modified "new
template" copy are built once in setUpClass and copied per test. Conflicts are
built like tests/test_guilda_upgrade.py does: the project is installed from the
real source and upgraded from a modified copy of it (patched in as
guilda.engine.SOURCE, which is what the CLI upgrades from).
"""
import contextlib
import io
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

import guilda.cli as cli  # noqa: E402
import guilda.engine as engine  # noqa: E402
import tests.test_guilda_upgrade as tu  # noqa: E402

MANIFEST = tu.MANIFEST
CHANGED_OUT = tu.CHANGED_OUT


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


def capture(func, argv, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch.object(sys, "stdin", stdin if stdin is not None else io.StringIO()):
        code = func(argv)
    return code, out.getvalue(), err.getvalue()


def run(argv, stdin=None):
    return capture(cli.main, argv, stdin)


def rmtree(path):
    resolved = Path(path).resolve()
    assert resolved.parent == ROOT.parent.resolve() and resolved.name.startswith("template-test-")

    def writable(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    for attempt in range(6):
        try:
            shutil.rmtree(resolved, onerror=writable)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(0.5 * (attempt + 1))


def snapshot(target):
    return {p.relative_to(target).as_posix(): p.read_bytes() for p in sorted(Path(target).rglob("*")) if p.is_file()}


def normalized(text, target):
    """Engine JSON with the (JSON-escaped) target path replaced, so two targets compare equal."""
    return json.loads(text.replace(json.dumps(str(target))[1:-1], "T"))


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        cls.root.mkdir()
        cls.new_src = tu.UpgradeTests.copy_source(cls, "new-src", {tu.CHANGED: tu.extend})
        cls.pristine = cls.root / "pristine"
        engine.install(ROOT, cls.pristine, ["claude", "codex"], ["base"])

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.root)

    def setUp(self):
        self.work = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        self.work.mkdir()
        self.addCleanup(rmtree, self.work)
        self.target = self.work / "consumer"

    def project(self):
        shutil.copytree(self.pristine, self.target)
        return self.target

    def conflicting_project(self):
        """Local edit + template change on the same file => one conflict."""
        self.project()
        (self.target / CHANGED_OUT).write_bytes(b"user edit\n")
        return mock.patch.object(engine, "SOURCE", self.new_src)

    def upgrade(self, *extra, stdin=None):
        return run(["upgrade", str(self.target), *extra], stdin)

    def test_init_sync_check_doctor_package_behave_as_before(self):
        eng = self.work / "eng"
        flags = ["--providers", "claude,codex", "--profiles", "base"]
        for command in ("init", "sync"):
            got = run([command, "--target", str(self.target), *flags])
            expected = capture(engine.main, [command, "--target", str(eng), *flags])
            self.assertEqual((got[0], expected[0]), (0, 0))
            self.assertEqual(normalized(got[1], self.target), normalized(expected[1], eng))
        got = run(["check", "--target", str(self.target)])
        expected = capture(engine.main, ["check", "--target", str(eng)])
        self.assertEqual((got[0], expected[0]), (0, 0))
        self.assertEqual(normalized(got[1], self.target), normalized(expected[1], eng))
        got, expected = run(["doctor"]), capture(engine.main, ["doctor"])
        self.assertEqual((got[0], expected[0]), (0, 0))
        self.assertEqual(json.loads(got[1]), json.loads(expected[1]))
        pkg, pkg2 = self.work / "pkg", self.work / "pkg2"
        got = run(["package", "--provider", "claude", "--target", str(pkg)])
        expected = capture(engine.main, ["package", "--provider", "claude", "--target", str(pkg2)])
        self.assertEqual((got[0], expected[0]), (0, 0))
        self.assertEqual(normalized(got[1], pkg), normalized(expected[1], pkg2))
        self.assertEqual(snapshot(pkg).keys(), snapshot(pkg2).keys())
        code, _, err = run(["init"])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("error: --target required"))

    def test_upgrade_without_tty_fails_listing_conflicts(self):
        with self.conflicting_project():
            before = snapshot(self.target)
            code, out, err = self.upgrade(stdin=io.StringIO())
        self.assertEqual(code, 1)
        self.assertIn(CHANGED_OUT, err)
        self.assertEqual(snapshot(self.target), before)

    def test_upgrade_yes_approves(self):
        with self.conflicting_project():
            code, out, err = self.upgrade("--yes", stdin=io.StringIO())
        self.assertEqual((code, err), (0, ""))
        self.assertIn("Extra rule added by the new template", (self.target / CHANGED_OUT).read_text(encoding="utf-8"))

    def test_upgrade_prompt_shows_files_and_warns_data_loss(self):
        with self.conflicting_project():
            before = snapshot(self.target)
            code, out, err = self.upgrade(stdin=FakeTTY("n\n"))
            self.assertEqual(code, 1)
            self.assertIn(CHANGED_OUT, out + err)
            self.assertIn("perdidas", out + err)
            self.assertIn("guilda promote", out + err)
            self.assertEqual(snapshot(self.target), before)
            code, out, err = self.upgrade(stdin=FakeTTY("y\n"))
            self.assertEqual(code, 0, err)
        self.assertIn("Extra rule added", (self.target / CHANGED_OUT).read_text(encoding="utf-8"))

    def test_upgrade_without_conflicts_does_not_prompt(self):
        self.project()
        with mock.patch.object(engine, "SOURCE", self.new_src):
            code, out, err = self.upgrade(stdin=io.StringIO())
        self.assertEqual(code, 0, err)
        self.assertIn("Extra rule added", (self.target / CHANGED_OUT).read_text(encoding="utf-8"))

    def test_upgrade_dry_run_prints_plan_and_writes_nothing(self):
        with self.conflicting_project():
            before = snapshot(self.target)
            code, out, err = self.upgrade("--dry-run", stdin=io.StringIO())
        self.assertEqual(code, 0, err)
        self.assertEqual(snapshot(self.target), before)
        for label in ("write", "remove", "keep", "conflicts", "migrate_name"):
            self.assertIn(label, out)
        self.assertIn(CHANGED_OUT, out)

    def test_install_command_matches_install_py(self):
        code, out, err = run(["install", str(self.target)])
        self.assertEqual((code, err), (0, ""))
        self.assertIn(f"instalação (concluída) em {self.target.resolve()}", out)
        self.assertIn("perfis: base, product-team, github-projects | provedores: claude, codex", out)
        self.assertIn("arquivos gravados", out)
        self.assertIn("verificação (check): ok", out)
        manifest = json.loads((self.target / MANIFEST).read_text(encoding="utf-8"))
        self.assertEqual(set(snapshot(self.target)), set(manifest["files"]) | {MANIFEST})
        code, out, err = run(["install", str(self.target), "--dry-run"])
        self.assertEqual(code, 0, err)
        self.assertIn("atualização (simulação)", out)
        self.assertIn("rode sem --dry-run para aplicar.", out)

    def test_install_py_is_a_thin_entry(self):
        import install

        with mock.patch.object(cli, "main", return_value=7) as main:
            self.assertEqual(install.main(["x", "--dry-run"]), 7)
        main.assert_called_once_with(["install", "x", "--dry-run"])

    def test_confirm_does_not_read_without_tty(self):
        class NoTTY(io.StringIO):
            def readline(self, *args):
                raise AssertionError("read without a TTY")

        out = io.StringIO()
        self.assertFalse(cli.confirm("ok? ", stdin=NoTTY("s\n"), stdout=out))
        self.assertFalse(cli.confirm("ok? ", stdin=object(), stdout=out))
        for answer, expected in (("s", True), ("SIM", True), ("y", True), ("Yes", True), ("n", False), ("", False), ("talvez", False)):
            self.assertEqual(cli.confirm("ok? ", stdin=FakeTTY(answer + "\n"), stdout=out), expected, answer)

    def test_mod_command_dry_run(self):
        code, out, err = run(["mod", "token-handoff", "--dry-run", "--target", str(self.work)])
        self.assertEqual((code, err), (0, ""))
        self.assertIn("mod token-handoff", out)
        self.assertIn("(project)", out)
        self.assertIn("seriam gravados: ", out)
        self.assertIn("comandos: ", out)
        self.assertEqual(list(self.work.iterdir()), [])
        code, out, err = run(["mod", "nao-existe", "--target", str(self.work)])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("erro: mod nao-existe: "))

    def test_legacy_project_install_points_to_upgrade_and_upgrade_migrates(self):
        self.project()
        manifest = json.loads((self.target / MANIFEST).read_text(encoding="utf-8"))
        manifest["name"] = "engineering-template"
        (self.target / MANIFEST).write_bytes(engine.json_bytes(manifest))
        code, out, err = run(["sync", "--target", str(self.target), "--providers", "claude,codex", "--profiles", "base"])
        self.assertEqual(code, 1)
        self.assertIn("run guilda upgrade", err)
        code, out, err = run(["install", str(self.target)])
        self.assertEqual(code, 1)
        self.assertIn("run guilda upgrade", err)
        code, out, err = self.upgrade("--yes")
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads((self.target / MANIFEST).read_text(encoding="utf-8"))["name"], "guilda")
        code, out, err = run(["check", "--target", str(self.target)])
        self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()
