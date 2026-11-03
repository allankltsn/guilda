"""Atualização do próprio `guilda` (distinta de `guilda upgrade`, que atualiza o projeto).

Sem rede por conta própria: a consulta ao PyPI só acontece quando o usuário liga a
verificação automática (`update_check` = notify|auto) ou roda `guilda self-update`.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from guilda import __version__
from guilda.upgrade import parse_version

PYPI_URL = "https://pypi.org/pypi/guilda/json"
TIMEOUT = 5
INTERVAL = timedelta(hours=24)
_PLAIN = re.compile(r"\d+\.\d+\.\d+\Z")


def latest_version(opener=urllib.request.urlopen) -> str:
    """Maior versão X.Y.Z estável do PyPI com ao menos um arquivo não retirado (yanked)."""
    try:
        with opener(PYPI_URL, timeout=TIMEOUT) as response:
            releases = json.loads(response.read().decode("utf-8"))["releases"]
        best = None
        for version, files in releases.items():
            if not _PLAIN.match(version) or not any(not f.get("yanked", False) for f in files):
                continue
            if best is None or parse_version(version) > parse_version(best):
                best = version
    except Exception as exc:  # noqa: BLE001 - rede/parse viram uma mensagem curta
        raise ValueError(f"não foi possível consultar o PyPI ({type(exc).__name__})") from None
    if best is None:
        raise ValueError("nenhuma versão estável encontrada no PyPI")
    return best


def is_due(now: datetime, cfg: dict) -> bool:
    """Verdadeiro quando a verificação automática está ligada e passaram 24 h da última."""
    if cfg.get("update_check", "off") == "off":
        return False
    last = cfg.get("last_check")
    if not last:
        return True
    try:
        previous = datetime.fromisoformat(last)
        if (previous.tzinfo is None) != (now.tzinfo is None):
            return True
        return now - previous >= INTERVAL
    except (TypeError, ValueError):
        return True


def check_if_due(now: datetime, cfg: dict, opener=urllib.request.urlopen) -> str | None:
    """Versão mais nova que a instalada, ou None. Não grava `last_check` (isso é do chamador)."""
    if not is_due(now, cfg):
        return None
    try:
        newest = latest_version(opener)
        return newest if parse_version(newest) > parse_version(__version__) else None
    except ValueError:
        return None


def installed_by_uv(executable: str | None = None, prefix: str | None = None, environ=None) -> bool:
    """Heurística: o interpretador/prefixo está no diretório de ferramentas do uv.

    Verdadeiro se o caminho começa em $UV_TOOL_DIR, ou contém os segmentos consecutivos
    `uv/tools` ou `uv/data/tools` (padrões do uv em Linux, macOS e Windows).
    """
    environ = os.environ if environ is None else environ
    paths = [executable or sys.executable, prefix or sys.prefix]
    tool_dir = environ.get("UV_TOOL_DIR")
    for raw in paths:
        norm = os.path.normcase(os.path.normpath(raw))
        if tool_dir:
            base = os.path.normcase(os.path.normpath(tool_dir))
            if norm == base or norm.startswith(base + os.sep):
                return True
        parts = [p.lower() for p in re.split(r"[\\/]+", raw)]
        for i, part in enumerate(parts):
            if part == "uv" and parts[i + 1:i + 2] == ["tools"]:
                return True
            if part == "uv" and parts[i + 1:i + 3] == ["data", "tools"]:
                return True
    return False


def upgrade_command(executable: str | None = None, prefix: str | None = None, environ=None) -> list[str]:
    if installed_by_uv(executable, prefix, environ):
        return ["uv", "tool", "upgrade", "guilda"]
    return [executable or sys.executable, "-m", "pip", "install", "--upgrade", "guilda"]


def upgrade_self(runner=subprocess.run, executable: str | None = None, prefix: str | None = None, environ=None, capture: bool = False) -> int:
    """Roda o comando de atualização (sem shell) e devolve o código de saída.

    Com `capture`, a saída do pip/uv é capturada (não vaza para o comando do usuário).
    """
    extra = {"capture_output": True, "text": True} if capture else {}
    try:
        return int(runner(upgrade_command(executable, prefix, environ), **extra).returncode)
    except OSError:
        return 1
