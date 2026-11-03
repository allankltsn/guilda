"""Isola a configuração do guilda nos testes.

Importe este módulo no topo de todo teste que chame `cli.main` ou use `config`/`selfupdate`.
No import ele aponta GUILDA_CONFIG para um arquivo temporário com a verificação desligada,
de modo que nenhuma suíte lê, reescreve ou age conforme o config real do usuário (rede, pip, uv).
"""
import atexit
import json
import os
import shutil
import tempfile
from pathlib import Path

DIR = Path(tempfile.mkdtemp(prefix="guilda-test-config-"))
CONFIG_PATH = DIR / "config.json"
CONFIG_PATH.write_text(json.dumps({"update_check": "off", "last_check": None}), encoding="utf-8")
os.environ["GUILDA_CONFIG"] = str(CONFIG_PATH)
atexit.register(shutil.rmtree, DIR, ignore_errors=True)
