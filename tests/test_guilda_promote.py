"""Tests for `guilda promote`. NO test ever touches GitHub: every `gh` call goes through FakeRunner."""
import io
import os
import shutil
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import guilda.cli as cli  # noqa: E402
import guilda.engine as engine  # noqa: E402
import guilda.promote as promote  # noqa: E402
import tests.test_guilda_cli as tc  # noqa: E402

CHANGED_OUT = ".engineering/roles/architect.md"
ADDED = ".claude/custom-note.md"
GIST = "https://gist.github.com/someone/abc123def456"
ISSUE = f"https://github.com/{promote.REPO}/issues/7"
ACCEPT = "Concedo ao mantenedor uma licença ampla para usar, modificar e relicenciar esta contribuição."
SECRET_VALUE = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2"


class FakeRunner:
    """Records every call; never runs anything. `fail` names a (sub)command that returns non-zero."""

    def __init__(self, fail=None, auth_ok=True):
        self.calls = []
        self.fail = fail
        self.auth_ok = auth_ok
        self.gist_files = None
        self.gist_cwd = None
        self.issue_body = None
        self.issue_dir = None

    @staticmethod
    def key(argv):
        return " ".join(argv[1:3])

    def __call__(self, argv, **kwargs):
        argv = list(argv)
        self.calls.append((argv, kwargs))
        key = self.key(argv)
        if key == "gist create":
            self.gist_cwd = Path(kwargs["cwd"])
            self.gist_files = {name: (self.gist_cwd / name).read_bytes() for name in os.listdir(self.gist_cwd)}
        if key == "issue create" and "--body-file" in argv:
            body_file = Path(argv[argv.index("--body-file") + 1])
            self.issue_dir = body_file.parent
            self.issue_body = body_file.read_text(encoding="utf-8")
        if key == "auth status":
            return SimpleNamespace(returncode=0 if self.auth_ok else 1, stdout="", stderr="not logged in")
        if self.fail == key:
            return SimpleNamespace(returncode=1, stdout="", stderr="boom")
        if key == "gist create":
            return SimpleNamespace(returncode=0, stdout=GIST + "\n", stderr="")
        if key == "issue create":
            return SimpleNamespace(returncode=0, stdout=ISSUE + "\n", stderr="")
        raise AssertionError(f"unexpected command {argv}")

    def keys(self):
        return [self.key(a) for a, _ in self.calls]

    def argv_of(self, key):
        return [a for a, _ in self.calls if self.key(a) == key]


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


class PromoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        cls.root.mkdir()
        cls.pristine = cls.root / "pristine"
        engine.install(ROOT, cls.pristine, ["claude", "codex"], ["base"])

    @classmethod
    def tearDownClass(cls):
        tc.rmtree(cls.root)

    def setUp(self):
        self.work = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        self.work.mkdir()
        self.addCleanup(tc.rmtree, self.work)
        self.target = self.work / "consumer"
        shutil.copytree(self.pristine, self.target)

    def edit(self, name=CHANGED_OUT, data=b"my improved architect\n"):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def run_promote(self, runner, assume_yes=True, stdin=None, stdout=None):
        return promote.promote(ROOT, self.target, "Título", "Descrição", assume_yes=assume_yes, runner=runner, stdin=stdin, stdout=stdout or io.StringIO())

    # --- changed_files ---
    def test_changed_files_lists_added_and_modified_only(self):
        self.edit()
        self.edit(ADDED, b"note\n")
        self.edit("README-local.md", b"outside managed dirs\n")
        found = promote.changed_files(ROOT, self.target)
        self.assertEqual(found, {CHANGED_OUT: b"my improved architect\n", ADDED: b"note\n"})
        self.assertNotIn(".engineering/manifest.json", found)

    def test_changed_files_tolerates_line_ending_conversion(self):
        original = (self.target / CHANGED_OUT).read_bytes().replace(b"\r\n", b"\n")
        self.edit(data=original.replace(b"\n", b"\r\n"))
        self.assertEqual(promote.changed_files(ROOT, self.target), {})

    # --- scan ---
    def kinds(self, data, path="a.md"):
        return sorted({f.kind for f in promote.scan({path: data})})

    def test_scan_flags_token_private_key_and_personal_paths(self):
        cases = [
            (b"x\n-----BEGIN RSA PRIVATE KEY-----\nabc\n", "secret"),
            (b"-----BEGIN PRIVATE KEY-----\n", "secret"),
            (SECRET_VALUE.encode(), "secret"),
            (b"github_pat_" + b"a" * 25, "secret"),
            (b"AKIA" + b"ABCDEFGHIJKLMNOP", "secret"),
            (b"xoxb-123456-abcdef", "secret"),
            (b"sk-" + b"a" * 24, "secret"),
            (b"sk-proj-abcDEF123_ghiJKL456-mnoPQR789", "secret"),
            (b"sk-ant-api03-abcDEF123ghiJKL456-mnoPQR", "secret"),
            (b"Authorization: Bearer abcdefghijklmnopqrstuvwx", "secret"),
            (b"eyJhbGciOiJI.eyJzdWIiOiIx.SflKxwRJSMeKKF2QT4", "secret"),
            (b"postgres://admin:s3cretpass@db.example.com/x", "secret"),
            (b"sk_" + b"live_" + b"a" * 20, "secret"),
            (b"sk_" + b"test_" + b"a" * 20, "secret"),
            (b"AIza" + b"A" * 35, "secret"),
            (b"https://hooks.slack.com/services/T000/B000/XXXXabc", "secret"),
            (b"-----BEGIN PGP PRIVATE KEY BLOCK-----", "secret"),
            (b"ghu_" + b"a" * 24, "secret"),
            (b"ghr_" + b"a" * 24, "secret"),
            (b"pwd = realvalue123", "secret"),
            (b"DB_PASS: realvalue123", "secret"),
            (b"credentials: realvalue123", "secret"),
            (b"auth: realvalue123", "secret"),
            (b"password: hunter2hunter2", "secret"),
            (b"API_KEY = 'abcd1234efgh'", "secret"),
            (b"C:\\Users\\allan\\proj", "personal-path"),
            (b"C:/Users/allan/proj", "personal-path"),
            (b"see /home/allan/x", "personal-path"),
            (b"see /Users/allan/x", "personal-path"),
        ]
        for data, kind in cases:
            self.assertEqual(self.kinds(data), [kind], data)
        found = promote.scan({"a.md": b"ok\nok\nC:\\Users\\bob\\x\n"})
        self.assertEqual(found, [promote.Finding("a.md", 3, "personal-path")])

    def test_scan_flags_binary_and_oversize(self):
        found = promote.scan({"b.bin": b"ab\x00cd", "big.md": b"a" * (1024 * 1024 + 1), "ok.md": b"a" * 1024 * 1024})
        self.assertEqual(sorted((f.path, f.line, f.kind) for f in found), [("b.bin", 0, "binary"), ("big.md", 0, "too-large")])

    def test_scan_ignores_placeholders(self):
        for text in (
            b"password: <your-password>", b"token = ${GITHUB_TOKEN}", b"secret: changeme",
            b"api_key: xxxxxxxxxxxx", b"token: ...........", b"password: short",
            b"C:\\Users\\<user>\\x", b"/home/<name>/x", b"%USERNAME%", b"$HOME/x", b"C:\\Users\\%USERNAME%\\x",
            b"task-management-system-design-overview", b"author: somebodyelse",
            b"postgres://admin:${DB_PASS}@db/x", b"Authorization: Bearer ${TOKEN}", b"https://example.com/a/b",
            b"nothing here", b"sk-short", b"ghp_short",
        ):
            self.assertEqual(promote.scan({"a.md": text}), [], text)

    def test_scan_does_not_treat_values_that_merely_contain_a_placeholder_word_as_placeholders(self):
        for text in (b"password: realsecretchangeme", b"token: abXXXXcd1234567", b"password: hunter2...x"):
            self.assertEqual(self.kinds(text), ["secret"], text)

    def test_scan_text_flags_without_echoing_the_value(self):
        found = promote.scan_text("<title>", f"oi {SECRET_VALUE}\nC:\\Users\\zelda\\x")
        self.assertEqual(found, [promote.Finding("<title>", 1, "secret"), promote.Finding("<title>", 2, "personal-path")])
        self.assertNotIn(SECRET_VALUE, repr(found))

    def test_scan_flags_secret_in_file_name_without_echoing_it(self):
        name = f".claude/{SECRET_VALUE}.md"
        self.edit(name, b"hi\n")
        runner = FakeRunner()
        with self.assertRaises(promote.PromoteError) as ctx:
            self.run_promote(runner)
        self.assertNotIn(SECRET_VALUE, str(ctx.exception))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_findings_never_contain_the_secret_value(self):
        text = f"password: hunter2hunter2\nkey {SECRET_VALUE}\nC:\\Users\\zelda\\a\n".encode()
        findings = promote.scan({"a.md": text})
        self.assertEqual(len(findings), 3)
        dump = repr(findings) + str([vars(f) for f in findings])
        for value in ("hunter2hunter2", SECRET_VALUE, "zelda"):
            self.assertNotIn(value, dump)

    # --- promote flow ---
    def test_secret_blocks_publishing_and_calls_nothing(self):
        self.edit(data=f"token {SECRET_VALUE}\n".encode())
        runner = FakeRunner()
        with self.assertRaises(promote.PromoteError) as ctx:
            self.run_promote(runner)
        self.assertIn(CHANGED_OUT, str(ctx.exception))
        self.assertNotIn(SECRET_VALUE, str(ctx.exception))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_secret_in_description_blocks_even_with_yes(self):
        self.edit()
        runner = FakeRunner()
        with self.assertRaises(promote.PromoteError) as ctx:
            promote.promote(ROOT, self.target, "T", f"minha chave {SECRET_VALUE}", assume_yes=True, runner=runner, stdout=io.StringIO())
        self.assertIn("<description>", str(ctx.exception))
        self.assertNotIn(SECRET_VALUE, str(ctx.exception))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_personal_path_in_title_blocks(self):
        self.edit()
        runner = FakeRunner()
        with self.assertRaises(promote.PromoteError) as ctx:
            promote.promote(ROOT, self.target, "veja C:\\Users\\zelda\\x", "D", assume_yes=True, runner=runner, stdout=io.StringIO())
        self.assertIn("<title>", str(ctx.exception))
        self.assertNotIn("zelda", str(ctx.exception))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_confirmation_output_shows_the_public_title_and_body(self):
        self.edit()
        out = io.StringIO()
        with self.assertRaises(promote.PromoteError):
            self.run_promote(FakeRunner(), assume_yes=False, stdin=FakeTTY("n\n"), stdout=out)
        text = out.getvalue()
        self.assertIn("[proposta] Título", text)
        self.assertIn("Descrição", text)
        self.assertIn(ACCEPT, text)
        self.assertIn("PÚBLICO", text)

    def test_declined_confirmation_publishes_nothing(self):
        self.edit()
        runner = FakeRunner()
        out = io.StringIO()
        with self.assertRaises(promote.PromoteError):
            self.run_promote(runner, assume_yes=False, stdin=FakeTTY("n\n"), stdout=out)
        self.assertEqual(runner.keys(), ["auth status"])
        self.assertIn(CHANGED_OUT, out.getvalue())  # the file list was shown before asking

    def test_no_tty_without_yes_publishes_nothing(self):
        self.edit()
        runner = FakeRunner()
        with self.assertRaises(promote.PromoteError):
            self.run_promote(runner, assume_yes=False, stdin=io.StringIO("s\n"))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_confirmed_on_tty_publishes(self):
        self.edit()
        runner = FakeRunner()
        result = self.run_promote(runner, assume_yes=False, stdin=FakeTTY("s\n"))
        self.assertEqual(result, {"gist": GIST, "issue": ISSUE})

    def test_gh_not_authenticated_is_clear_error(self):
        self.edit()
        runner = FakeRunner(auth_ok=False)
        with self.assertRaises(promote.PromoteError) as ctx:
            self.run_promote(runner)
        self.assertIn("gh auth login", str(ctx.exception))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_gh_missing_is_clear_error(self):
        def runner(argv, **kwargs):
            raise FileNotFoundError("gh")
        with self.assertRaises(promote.PromoteError):
            self.run_promote(runner)

    def test_no_changed_files_is_clear_error(self):
        runner = FakeRunner()
        with self.assertRaises(promote.PromoteError) as ctx:
            self.run_promote(runner)
        self.assertIn("nenhum arquivo", str(ctx.exception))
        self.assertEqual(runner.keys(), ["auth status"])

    def test_issue_creation_failure_reports_gist_url(self):
        self.edit()
        runner = FakeRunner(fail="issue create")
        with self.assertRaises(promote.PromoteError) as ctx:
            self.run_promote(runner)
        self.assertEqual(ctx.exception.gist_url, GIST)
        self.assertIn(GIST, str(ctx.exception))
        self.assertIn("gh gist delete abc123def456", str(ctx.exception))
        self.assertEqual(runner.keys().count("issue create"), 1)
        self.assertFalse(runner.gist_cwd.exists())  # temp dir removed
        self.assertFalse(runner.issue_dir.exists())

    def test_gist_failure_removes_temp_dir_and_has_no_gist_url(self):
        self.edit()
        runner = FakeRunner(fail="gist create")
        seen = []

        def wrapper(argv, **kwargs):
            if "cwd" in kwargs:
                seen.append(Path(kwargs["cwd"]))
            return runner(argv, **kwargs)
        with self.assertRaises(promote.PromoteError) as ctx:
            self.run_promote(wrapper)
        self.assertIsNone(ctx.exception.gist_url)
        self.assertNotIn("issue create", runner.keys())
        self.assertTrue(seen and not seen[0].exists())

    def test_gist_is_secret(self):
        self.edit()
        self.edit(ADDED, b"note\n")
        runner = FakeRunner()
        result = self.run_promote(runner)
        self.assertEqual(result, {"gist": GIST, "issue": ISSUE})
        argv = runner.argv_of("gist create")[0]
        self.assertNotIn("--public", argv)
        self.assertIn("--", argv)
        self.assertEqual(sorted(runner.gist_files), sorted([".engineering__roles__architect.md", ".claude__custom-note.md"]))
        self.assertEqual(runner.gist_files[".claude__custom-note.md"], b"note\n")
        issue = runner.argv_of("issue create")[0]
        self.assertEqual(issue[issue.index("--repo") + 1], promote.REPO)
        self.assertIn("--body-file", issue)
        self.assertNotIn("--body", issue)
        self.assertNotIn("--label", issue)
        self.assertEqual(issue[issue.index("--title") + 1], "[proposta] Título")
        self.assertEqual(runner.keys(), ["auth status", "gist create", "issue create"])

    def test_title_prefix_is_not_duplicated(self):
        self.edit()
        runner = FakeRunner()
        promote.promote(ROOT, self.target, "[proposta] Já tem", "D", assume_yes=True, runner=runner, stdout=io.StringIO())
        issue = runner.argv_of("issue create")[0]
        self.assertEqual(issue[issue.index("--title") + 1], "[proposta] Já tem")

    # --- build_issue ---
    def test_issue_body_contains_gist_link_paths_and_acceptance(self):
        title, body = promote.build_issue("T", "Minha descrição", GIST, [CHANGED_OUT, ADDED], "1.2.3")
        self.assertEqual(title, "T")
        for needle in (GIST, CHANGED_OUT, ADDED, "Minha descrição", "1.2.3", ACCEPT, "template.json", "core/catalog.md", "CHANGELOG.md", "README.md", "testes", "não confiável"):
            self.assertIn(needle, body)
        self.assertIn(".engineering__roles__architect.md", body)  # mapping gist name -> path

    def test_issue_body_never_contains_file_contents(self):
        self.edit(data=b"UNIQUE-CONTENT-MARKER-12345\n")
        runner = FakeRunner()
        self.run_promote(runner)
        issue = runner.argv_of("issue create")[0]
        self.assertNotIn("UNIQUE-CONTENT-MARKER-12345", " ".join(issue))
        self.assertNotIn("UNIQUE-CONTENT-MARKER-12345", runner.issue_body)
        self.assertIn(b"UNIQUE-CONTENT-MARKER-12345", b"".join(runner.gist_files.values()))

    # --- CLI ---
    def test_cli_promote_wires_and_reports_errors(self):
        self.edit()
        argv = ["promote", str(self.target), "--title", "T", "--description", "D", "--yes"]
        runner = FakeRunner()
        code, out, err = tc.capture(lambda a: cli.main(a, runner=runner), argv)
        self.assertEqual((code, err), (0, ""))
        self.assertIn(GIST, out)
        self.assertIn(ISSUE, out)
        with self.assertRaises(SystemExit):  # --title/--description are required
            tc.capture(lambda a: cli.main(a, runner=FakeRunner()), ["promote", str(self.target)])
        runner = FakeRunner(fail="issue create")
        code, out, err = tc.capture(lambda a: cli.main(a, runner=runner), argv)
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("erro: "))
        self.assertIn(GIST, err)
        runner = FakeRunner()  # no TTY and no --yes: nothing published
        code, out, err = tc.capture(lambda a: cli.main(a, runner=runner), argv[:-1])
        self.assertEqual(code, 1)
        self.assertEqual(runner.keys(), ["auth status"])


if __name__ == "__main__":
    unittest.main()
