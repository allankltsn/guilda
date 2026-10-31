import json
import os
import shutil
import stat
import sys
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import guilda.engine as engine  # noqa: E402
import guilda.mods as mods  # noqa: E402


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
