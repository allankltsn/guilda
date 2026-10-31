import json
import tempfile
import unittest
from pathlib import Path

import guilda
from guilda import paths

ROOT = Path(__file__).resolve().parents[1]


class GuildaPackageTests(unittest.TestCase):
    def test_version_matches_template_json(self):
        data = json.loads((ROOT / "template.json").read_text(encoding="utf-8"))
        self.assertEqual(guilda.__version__, data["version"])

    def test_data_root_in_checkout_is_repo_root(self):
        root = paths.data_root()
        self.assertTrue((root / "template.json").is_file())
        self.assertTrue((root / "core").is_dir())

    def test_data_root_prefers_embedded_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp)
            (pkg / "_data").mkdir()
            (pkg / "_data" / "template.json").write_text("{}", encoding="utf-8")
            self.assertEqual(paths._resolve(package_dir=pkg), pkg / "_data")


if __name__ == "__main__":
    unittest.main()
