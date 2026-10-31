import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from guilda import engine, payload

ROOT = Path(__file__).resolve().parents[1]
IS_GIT = (ROOT / ".git").exists()


def _copy_checkout(dest: Path) -> None:
    for name in ("core", "profiles", "adapters", "integrations"):
        shutil.copytree(ROOT / name, dest / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy2(ROOT / "template.json", dest / "template.json")
    (dest / "guilda").mkdir()
    shutil.copy2(ROOT / "guilda" / "payload.txt", dest / "guilda" / "payload.txt")


class PayloadTests(unittest.TestCase):
    def test_payload_has_no_forbidden_paths(self):
        for entry in payload.read(ROOT):
            self.assertFalse(payload.is_forbidden(entry), entry)

    @unittest.skipUnless(IS_GIT, "not a git checkout")
    def test_payload_matches_git_tracked_files(self):
        self.assertEqual(payload.read(ROOT), payload.generate(ROOT))

    def test_every_payload_file_exists(self):
        for entry in payload.read(ROOT):
            self.assertTrue((ROOT / entry).is_file(), entry)

    def test_load_source_ignores_untracked_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            _copy_checkout(copy)
            noise = copy / "core" / "graphify-out" / "x.json"
            noise.parent.mkdir(parents=True)
            noise.write_text("{}", encoding="utf-8")
            _, _, loaded = engine.load_source(copy)
            self.assertNotIn("core/graphify-out/x.json", loaded)
            _, output = engine.render(copy, ["claude", "codex"], ["base"])
            self.assertFalse([k for k in output if "graphify-out" in str(k)])

    def test_load_source_rejects_file_outside_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            _copy_checkout(copy)
            lst = copy / "guilda" / "payload.txt"
            lst.write_text(lst.read_text(encoding="utf-8") + "core/not-there.md\n", encoding="utf-8")
            with self.assertRaises((ValueError, FileNotFoundError)):
                engine.load_source(copy)

    def test_forbidden_matching_is_by_segment(self):
        self.assertFalse(payload.is_forbidden("core/myplans.md"))
        self.assertFalse(payload.is_forbidden("myplans.md"))
        self.assertTrue(payload.is_forbidden("core/plans/x.md"))
        self.assertTrue(payload.is_forbidden("a/specs/x.md"))
        self.assertTrue(payload.is_forbidden("docs/superpowers/x.md"))
        self.assertFalse(payload.is_forbidden("docs/other.md"))
        self.assertTrue(payload.is_forbidden("core/graphify-out/x.json"))

    @unittest.skipUnless(shutil.which("git"), "git missing")
    def test_generate_rejects_forbidden_tracked_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            bad = repo / "core" / "graphify-out" / "x.json"
            bad.parent.mkdir(parents=True)
            bad.write_text("{}", encoding="utf-8")
            subprocess.run(["git", "add", "core/graphify-out/x.json"], cwd=repo, check=True)
            with self.assertRaises(ValueError):
                payload.generate(repo)

    def test_wheel_force_include_maps_to_guilda_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)
            _copy_checkout(copy)
            noise = copy / "core" / "graphify-out" / "x.json"
            noise.parent.mkdir(parents=True)
            noise.write_text("{}", encoding="utf-8")
            mapping = payload.wheel_force_include(copy)
            self.assertEqual(mapping[str(copy / "template.json")], "guilda/_data/template.json")
            for dest in mapping.values():
                self.assertTrue(dest.startswith("guilda/_data/"))
                self.assertFalse(payload.is_forbidden(dest), dest)
            self.assertNotIn(str(noise), mapping)


if __name__ == "__main__":
    unittest.main()
