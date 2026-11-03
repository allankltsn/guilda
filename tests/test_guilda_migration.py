import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from tests import guilda_test_isolation  # noqa: E402,F401  (isola o config do usuário)
import guilda.engine as engine  # noqa: E402
import guilda.mods as mods  # noqa: E402


def _has_tag(tag):
    try:
        return subprocess.run(["git", "rev-parse", "--verify", "--quiet", tag + "^{commit}"], cwd=ROOT, capture_output=True, stdin=subprocess.DEVNULL, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.target = self.root / "consumer"

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

    def install(self, **kw):
        return engine.install(ROOT, self.target, ["claude", "codex"], ["base"], **kw)

    def manifest_path(self):
        return self.target / ".engineering/manifest.json"

    def make_legacy(self):
        self.install()
        data = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        data["name"] = engine.LEGACY_NAMES[0]
        self.manifest_path().write_text(json.dumps(data), encoding="utf-8")
        return data

    def test_new_manifest_name_is_guilda(self):
        self.install()
        data = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "guilda")
        self.assertEqual(engine.TEMPLATE_NAME, "guilda")

    def test_legacy_manifest_rejected_by_check_and_sync(self):
        self.make_legacy()
        with self.assertRaisesRegex(ValueError, "run guilda upgrade"):
            engine.check(ROOT, self.target)
        with self.assertRaisesRegex(ValueError, "run guilda upgrade"):
            self.install(sync=True)

    def test_legacy_manifest_accepted_with_allow_legacy(self):
        data = self.make_legacy()
        engine.validate_manifest(ROOT, data, allow_legacy=True)

    # --- 1.3.0 installs made from a dirty checkout (core/graphify-out/ shipped into .engineering/) ---
    def legacy_from_fixture(self):
        """Project whose manifest has exactly the paths a real 1.3.0 install recorded.

        tests/fixtures/manifest-1.3.0-dirty-checkout.json holds the metadata and the path list of a
        manifest written by the v1.3.0 installer (`git archive v1.3.0`, plus core/graphify-out/
        with graph.json, GRAPH_REPORT.md and cache/a.json, then `python install.py <proj>`).
        File contents are not in the fixture: paths the current template renders get the current
        bytes; the others get synthetic bytes. Every hash matches the file on disk (unmodified).
        """
        fixture = json.loads((ROOT / "tests/fixtures/manifest-1.3.0-dirty-checkout.json").read_text(encoding="utf-8"))
        engine.install(ROOT, self.target, fixture["providers"], fixture["profiles"])
        files = {}
        for name in fixture["paths"]:
            path = self.target / name
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(f"1.3.0 content of {name}\n".encode())
            files[name] = engine.digest(path.read_bytes())
        manifest = {k: fixture[k] for k in ("name", "version", "providers", "profiles", "package", "tiers")}
        manifest["files"] = files
        self.manifest_path().write_bytes(engine.json_bytes(manifest))
        return manifest

    def test_upgrade_migrates_1_3_0_install_with_stray_engineering_files(self):
        from guilda import cli, upgrade
        from tests.test_guilda_cli import capture

        manifest = self.legacy_from_fixture()
        strays = sorted(n for n in manifest["files"] if "/graphify-out/" in n)
        self.assertEqual(len(strays), 3)
        edited = ".engineering/graphify-out/graph.json"
        (self.target / edited).write_bytes(b'{"regenerated": true}\n')  # tool output changed after install
        plan = upgrade.plan_upgrade(ROOT, self.target)
        self.assertTrue(plan.migrate_name)
        self.assertEqual(plan.conflicts, [])
        self.assertEqual(sorted(set(strays) & set(plan.remove)), sorted(set(strays) - {edited}))
        self.assertIn(edited, plan.keep)
        code, out, err = capture(cli.main, ["upgrade", str(self.target)])
        self.assertEqual((code, err), (0, ""), out)
        data = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        self.assertEqual(data["name"], "guilda")
        self.assertFalse([n for n in data["files"] if "graphify-out" in n])
        # Intact copies are removed; the changed one stays on disk, now unmanaged.
        self.assertFalse((self.target / ".engineering/graphify-out/GRAPH_REPORT.md").exists())
        self.assertFalse((self.target / ".engineering/graphify-out/cache").exists())  # emptied dir pruned
        self.assertEqual((self.target / edited).read_bytes(), b'{"regenerated": true}\n')
        engine.check(ROOT, self.target)
        code, out, err = capture(cli.main, ["install", str(self.target), "--dry-run"])
        self.assertEqual(code, 0, err)

    def test_legacy_stray_paths_stay_bounded(self):
        manifest = self.legacy_from_fixture()
        sha = "0" * 64
        for bad in (".claude/graphify-out/x.json", ".engineering/manifest.json", "notes/graphify-out/x.json"):
            data = {**manifest, "files": {**manifest["files"], bad: sha}}
            with self.assertRaisesRegex(ValueError, "manifest ownership violation", msg=bad):
                engine.validate_manifest(ROOT, data, allow_legacy=True)
        # Only a legacy (1.x) manifest gets this tolerance; a guilda manifest stays strict.
        data = {**manifest, "name": "guilda"}
        with self.assertRaisesRegex(ValueError, "manifest ownership violation"):
            engine.validate_manifest(ROOT, data, allow_legacy=True)
        with self.assertRaisesRegex(ValueError, "legacy manifest name"):
            engine.validate_manifest(ROOT, manifest)

    @unittest.skipUnless(_has_tag("v1.3.0"), "tag v1.3.0 indisponível (clone raso)")
    def test_upgrade_migrates_install_made_by_the_real_1_3_0_installer(self):
        from guilda import cli
        from tests.test_guilda_cli import capture

        archive = subprocess.run(["git", "archive", "--format=tar", "v1.3.0"], cwd=ROOT, capture_output=True, check=True, stdin=subprocess.DEVNULL).stdout
        old = self.root / "template-1.3.0"
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(old, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))  # nosec: our own tag
        noise = old / "core/graphify-out"
        (noise / "cache").mkdir(parents=True)
        (noise / "graph.json").write_bytes(b'{"nodes": []}\n')
        (noise / "GRAPH_REPORT.md").write_bytes(b"# Graph report\n")
        (noise / "cache/a.json").write_bytes(b'{"k": 1}\n')
        done = subprocess.run([sys.executable, str(old / "install.py"), str(self.target)], capture_output=True, text=True, encoding="utf-8", stdin=subprocess.DEVNULL, timeout=300)
        self.assertEqual(done.returncode, 0, done.stderr)
        before = json.loads(self.manifest_path().read_text(encoding="utf-8"))
        self.assertEqual((before["name"], before["version"]), ("engineering-template", "1.3.0"))
        self.assertIn(".engineering/graphify-out/graph.json", before["files"])
        code, out, err = capture(cli.main, ["upgrade", str(self.target), "--dry-run"])
        self.assertEqual(code, 0, err)
        code, out, err = capture(cli.main, ["upgrade", str(self.target), "--yes"])
        self.assertEqual(code, 0, err)
        self.assertFalse((self.target / ".engineering/graphify-out").exists())
        engine.check(ROOT, self.target)

    def test_unreadable_manifest_is_clear_error(self):
        self.install()
        self.manifest_path().write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "manifest unreadable"):
            engine.read_manifest(self.target)
        with self.assertRaisesRegex(ValueError, "manifest unreadable"):
            engine.check(ROOT, self.target)

    def test_missing_manifest_points_to_init(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError, "run guilda init"):
            engine.read_manifest(self.target)

    def test_new_mod_marketplace_is_guilda_mods(self):
        self.assertEqual(mods.MARKETPLACE, "guilda-mods")
        self.target.mkdir()

        class Done:
            returncode = 0
            stdout = ""
            stderr = ""

        mods.install_mod("token-handoff", "project", self.target, home=self.root / "home", run=lambda *a, **k: Done(), platform="win32")
        market = json.loads((self.target / ".claude/mods/.claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(market["name"], "guilda-mods")
        self.assertEqual(market["owner"]["name"], "guilda")


if __name__ == "__main__":
    unittest.main()
