"""Configuração do usuário do `guilda` (arquivo JSON fora de qualquer projeto)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

UPDATE_CHECK_VALUES = ("off", "notify", "auto")
DEFAULTS = {"update_check": "off", "last_check": None}


def _home(environ, windows: bool) -> Path:
    key = "USERPROFILE" if windows else "HOME"
    return Path(environ[key]) if environ.get(key) else Path.home()


def path(environ=None, platform=None) -> Path:
    """Caminho do config.json. Lê o ambiente a cada chamada."""
    environ = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform
    if platform.startswith("win"):
        base = environ.get("APPDATA") or str(_home(environ, True) / "AppData" / "Roaming")
        return Path(base) / "guilda" / "config.json"
    base = environ.get("XDG_CONFIG_HOME") or str(_home(environ, False) / ".config")
    return Path(base) / "guilda" / "config.json"


def validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise ValueError("configuração deve ser um objeto")
    if data.get("update_check", "off") not in UPDATE_CHECK_VALUES:
        raise ValueError(f"update_check inválido: {data.get('update_check')!r} (use {'|'.join(UPDATE_CHECK_VALUES)})")


def load() -> dict:
    """Padrões mesclados com o arquivo; qualquer problema volta aos padrões (nunca levanta)."""
    cfg = dict(DEFAULTS)
    try:
        data = json.loads(path().read_text(encoding="utf-8"))
        validate(data)
        last = data.get("last_check", None)
        if last is not None and not isinstance(last, str):
            raise ValueError("last_check inválido")
        cfg.update(data)
    except Exception:  # noqa: BLE001 - config ilegível nunca derruba a CLI
        return dict(DEFAULTS)
    return cfg


def save(data: dict) -> None:
    """Valida e grava de forma atômica (arquivo temporário + replace)."""
    validate(data)
    target = path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".config-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({**DEFAULTS, **data}, handle, indent=2)
            handle.write("\n")
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
