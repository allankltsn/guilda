"""Tests for guilda config and self-update. NO test touches the real network, pip, uv or the user's real config:
every query goes through a fake opener, every command through a fake runner, and the config lives in a temp dir."""
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import guilda.cli as cli  # noqa: E402
import guilda.config as config  # noqa: E402
import guilda.selfupdate as selfupdate  # noqa: E402
from guilda import __version__  # noqa: E402

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def bump(version, part=1):
    nums = [int(x) for x in version.split(".")]
    nums[part] += 1
    return ".".join(str(n) for n in nums)


NEWER = bump(__version__)


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def pypi(releases):
    return {"releases": {v: ([{"yanked": False}] if files is True else files) for v, files in releases.items()}}


class FakeOpener:
    def __init__(self, payload=None, error=None):
        self.payload = payload if payload is not None else pypi({__version__: True, NEWER: True})
        self.error = error
        self.calls = []

    def __call__(self, url, timeout=None):
        self.calls.append((url, timeout))
        if self.error:
            raise self.error
        return FakeResponse(self.payload)


class ForbiddenOpener:
    def __init__(self):
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        raise AssertionError("network must not be touched")


class FakeRunner:
    def __init__(self, code=0):
        self.calls = []
        self.code = code

    def __call__(self, argv, **kwargs):
        self.calls.append((list(argv), kwargs))
        return SimpleNamespace(returncode=self.code)


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


class SelfUpdateTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT.parent / ("template-test-" + uuid.uuid4().hex)
        self.root.mkdir()
        self.addCleanup(rmtree, self.root)
        home = str(self.root / "home")
        env = {"APPDATA": home, "XDG_CONFIG_HOME": home, "HOME": home, "USERPROFILE": home}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.config_file = config.path()
        self.assertTrue(str(self.config_file).startswith(home))

    def write_config(self, **values):
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(values), encoding="utf-8")

    def run_cli(self, argv, stdin=None, runner=None, opener=None):
        out, err = io.StringIO(), io.StringIO()
        kwargs = {}
        if runner is not None:
            kwargs["runner"] = runner
        if opener is not None:
            kwargs["opener"] = opener
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch.object(sys, "stdin", stdin if stdin is not None else io.StringIO()):
            code = cli.main(argv, **kwargs)
        return code, out.getvalue(), err.getvalue()

    # --- selfupdate ---

    def test_default_is_off_and_makes_no_network_call(self):
        opener = ForbiddenOpener()
        self.assertEqual(config.load(), {"update_check": "off", "last_check": None})
        self.assertIsNone(selfupdate.check_if_due(NOW, config.load(), opener))
        self.assertEqual(opener.calls, 0)

    def test_notify_checks_at_most_once_per_day(self):
        opener = FakeOpener()
        cfg = {"update_check": "notify", "last_check": None}
        self.assertEqual(selfupdate.check_if_due(NOW, cfg, opener), NEWER)
        self.assertEqual(len(opener.calls), 1)
        recent = {"update_check": "notify", "last_check": (NOW - timedelta(hours=23)).isoformat()}
        self.assertIsNone(selfupdate.check_if_due(NOW, recent, opener))
        self.assertEqual(len(opener.calls), 1)
        old = {"update_check": "notify", "last_check": (NOW - timedelta(hours=25)).isoformat()}
        self.assertEqual(selfupdate.check_if_due(NOW, old, opener), NEWER)
        self.assertEqual(len(opener.calls), 2)
        self.assertEqual(opener.calls[0][0], "https://pypi.org/pypi/guilda/json")
        self.assertLessEqual(opener.calls[0][1], 5)

    def test_auto_runs_upgrade_self_once(self):
        self.write_config(update_check="auto", last_check=None)
        opener, runner = FakeOpener(), FakeRunner()
        code, _out, err = self.run_cli(["config", "get"], runner=runner, opener=opener)
        self.assertEqual(code, 0)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(len(opener.calls), 1)
        self.assertIn(NEWER, err)
        self.assertIsNotNone(config.load()["last_check"])
        # Second command within 24 h: no query, no upgrade.
        self.run_cli(["config", "get"], runner=runner, opener=opener)
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(len(opener.calls), 1)

    def test_pre_release_versions_are_ignored(self):
        releases = pypi({
            "1.0.0": True, "2.1.0rc1": True, "2.0.0-rc1": True, "2.0.0a1": True,
            "1.9.0": True, "3.0.0": [{"yanked": True}], "4.0.0": [], "bogus": True,
        })
        self.assertEqual(selfupdate.latest_version(FakeOpener(releases)), "1.9.0")
        with self.assertRaises(ValueError):
            selfupdate.latest_version(FakeOpener(pypi({"2.0.0rc1": True})))

    def test_cli_never_touches_network_when_off(self):
        opener = ForbiddenOpener()
        runner = FakeRunner()
        project = self.root / "proj"
        project.mkdir()
        self.run_cli(["doctor", "--target", str(project)], opener=opener, runner=runner)
        self.run_cli(["config", "get"], opener=opener, runner=runner)
        self.assertEqual(opener.calls, 0)
        self.assertEqual(runner.calls, [])

    def test_check_if_due_swallows_network_errors(self):
        cfg = {"update_check": "notify", "last_check": None}
        self.assertIsNone(selfupdate.check_if_due(NOW, cfg, FakeOpener(error=OSError("offline"))))
        self.assertIsNone(selfupdate.check_if_due(NOW, cfg, FakeOpener(payload={"nope": 1})))
        with self.assertRaises(ValueError):
            selfupdate.latest_version(FakeOpener(error=OSError("offline")))

    def test_upgrade_self_picks_uv_or_pip_without_shell(self):
        runner = FakeRunner()
        py = str(self.root / "venv" / "bin" / "python")
        self.assertEqual(selfupdate.upgrade_self(runner, executable=py, prefix=str(self.root / "venv"), environ={}), 0)
        self.assertEqual(runner.calls[-1][0], [py, "-m", "pip", "install", "--upgrade", "guilda"])
        uv_prefix = "/home/u/.local/share/uv/tools/guilda"
        selfupdate.upgrade_self(runner, executable=uv_prefix + "/bin/python", prefix=uv_prefix, environ={})
        self.assertEqual(runner.calls[-1][0], ["uv", "tool", "upgrade", "guilda"])
        win_prefix = r"C:\Users\u\AppData\Roaming\uv\data\tools\guilda"
        selfupdate.upgrade_self(runner, executable=win_prefix + r"\Scripts\python.exe", prefix=win_prefix, environ={})
        self.assertEqual(runner.calls[-1][0], ["uv", "tool", "upgrade", "guilda"])
        custom = str(self.root / "mytools")
        selfupdate.upgrade_self(runner, executable=custom + "/guilda/bin/python", prefix=custom + "/guilda", environ={"UV_TOOL_DIR": custom})
        self.assertEqual(runner.calls[-1][0], ["uv", "tool", "upgrade", "guilda"])
        for _argv, kwargs in runner.calls:
            self.assertFalse(kwargs.get("shell", False))
        self.assertEqual(selfupdate.upgrade_self(FakeRunner(code=3), executable=py, prefix="/x", environ={}), 3)

    def test_startup_check_never_fails_the_command(self):
        self.write_config(update_check="notify", last_check=None)
        opener = FakeOpener(error=OSError("offline"))
        code, _out, err = self.run_cli(["config", "get"], opener=opener)
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        # Even an unwritable config must not break the command.
        self.write_config(update_check="notify", last_check=None)
        with mock.patch.object(config, "save", side_effect=OSError("disk full")):
            code, _out, err = self.run_cli(["config", "get"], opener=FakeOpener())
        self.assertEqual(code, 0)
        # Notify prints exactly one line to stderr.
        self.write_config(update_check="notify", last_check=None)
        code, _out, err = self.run_cli(["config", "get"], opener=FakeOpener())
        self.assertEqual(code, 0)
        self.assertEqual(err.strip(), f"guilda {NEWER} disponível (instalada: {__version__}). Rode: guilda self-update")

    def test_startup_check_skipped_for_self_update_and_help(self):
        self.write_config(update_check="notify", last_check=None)
        opener = ForbiddenOpener()
        code, out, _err = self.run_cli(["self-update", "--dry-run"], opener=opener)
        self.assertEqual(code, 0)
        with self.assertRaises(SystemExit):
            self.run_cli(["--help"], opener=opener)
        with self.assertRaises(SystemExit):
            self.run_cli(["doctor", "--help"], opener=opener)
        self.assertEqual(opener.calls, 0)

    # --- self-update command ---

    def test_self_update_requires_confirmation_without_yes(self):
        runner = FakeRunner()
        code, _out, err = self.run_cli(["self-update"], runner=runner)  # no TTY
        self.assertEqual(code, 1)
        self.assertIn("erro:", err)
        self.assertEqual(runner.calls, [])
        code, _out, _err = self.run_cli(["self-update"], stdin=FakeTTY("n\n"), runner=runner)
        self.assertEqual(code, 1)
        self.assertEqual(runner.calls, [])
        code, _out, _err = self.run_cli(["self-update"], stdin=FakeTTY("s\n"), runner=runner)
        self.assertEqual((code, len(runner.calls)), (0, 1))
        code, _out, _err = self.run_cli(["self-update", "--yes"], runner=runner)
        self.assertEqual((code, len(runner.calls)), (0, 2))
        code, _out, err = self.run_cli(["self-update", "--yes"], runner=FakeRunner(code=2))
        self.assertEqual(code, 1)
        self.assertIn("erro:", err)

    def test_self_update_dry_run_runs_nothing(self):
        runner = FakeRunner()
        code, out, _err = self.run_cli(["self-update", "--dry-run"], runner=runner)
        self.assertEqual(code, 0)
        self.assertEqual(runner.calls, [])
        self.assertIn("guilda", out)
        self.assertIn(" ".join(selfupdate.upgrade_command()), out)

    # --- config ---

    def test_config_path_per_platform(self):
        win = config.path(environ={"APPDATA": r"C:\Users\u\AppData\Roaming"}, platform="win32")
        self.assertEqual(win, Path(r"C:\Users\u\AppData\Roaming") / "guilda" / "config.json")
        fallback = config.path(environ={"USERPROFILE": r"C:\Users\u"}, platform="win32")
        self.assertEqual(fallback, Path(r"C:\Users\u") / "AppData" / "Roaming" / "guilda" / "config.json")
        xdg = config.path(environ={"XDG_CONFIG_HOME": "/x/cfg", "HOME": "/h"}, platform="linux")
        self.assertEqual(xdg, Path("/x/cfg") / "guilda" / "config.json")
        no_xdg = config.path(environ={"HOME": "/h"}, platform="linux")
        self.assertEqual(no_xdg, Path("/h") / ".config" / "guilda" / "config.json")

    def test_invalid_config_falls_back_to_defaults(self):
        defaults = {"update_check": "off", "last_check": None}
        self.config_file.parent.mkdir(parents=True)
        for text in ("{not json", "[]", '{"update_check": "sometimes"}', '{"update_check": 3}', '{"last_check": 5}', ""):
            self.config_file.write_text(text, encoding="utf-8")
            self.assertEqual(config.load(), defaults, text)
        self.config_file.write_bytes(b"\xff\xfe\x00")
        self.assertEqual(config.load(), defaults)
        self.config_file.write_text('{"update_check": "notify"}', encoding="utf-8")
        self.assertEqual(config.load(), {"update_check": "notify", "last_check": None})

    def test_config_save_is_atomic_and_validates(self):
        with self.assertRaises(ValueError):
            config.save({"update_check": "sometimes", "last_check": None})
        self.assertFalse(self.config_file.exists())
        config.save({"update_check": "auto", "last_check": NOW.isoformat()})
        self.assertEqual(config.load(), {"update_check": "auto", "last_check": NOW.isoformat()})
        self.assertEqual(json.loads(self.config_file.read_text(encoding="utf-8"))["update_check"], "auto")
        self.assertEqual(os.listdir(self.config_file.parent), ["config.json"])
        # A failure during replace keeps the old file and leaves no temp file behind.
        with mock.patch("os.replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                config.save({"update_check": "off", "last_check": None})
        self.assertEqual(config.load()["update_check"], "auto")
        self.assertEqual(os.listdir(self.config_file.parent), ["config.json"])

    def test_config_command_get_and_set(self):
        code, out, _err = self.run_cli(["config", "get"])
        self.assertEqual((code, json.loads(out)), (0, {"update_check": "off", "last_check": None}))
        code, out, _err = self.run_cli(["config", "set", "update-check", "notify"])
        self.assertEqual(code, 0)
        self.assertIn("notify", out)
        self.assertEqual(config.load()["update_check"], "notify")
        code, out, _err = self.run_cli(["config", "get"], opener=FakeOpener(pypi({__version__: True})))
        self.assertEqual(json.loads(out)["update_check"], "notify")
        with self.assertRaises(SystemExit):
            self.run_cli(["config", "set", "update-check", "sometimes"])
        self.assertEqual(config.load()["update_check"], "notify")


if __name__ == "__main__":
    unittest.main()
