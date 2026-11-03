#!/usr/bin/env python3
"""Instala (ou atualiza) o template de engenharia num projeto.

Uso:
    python install.py <projeto>                  # instala; se já instalado, atualiza
    python install.py <projeto> --dry-run        # só mostra o que mudaria
    python install.py                            # usa o diretório atual como projeto

Opções (todas opcionais):
    --profiles a,b   perfis (padrão: base,product-team,github-projects; em atualização, os já instalados)
    --providers a,b  claude,codex (padrão: claude,codex; em atualização, os já instalados)
    --tier papel=camada   repetível; ex.: --tier reviewer=deep
    --mod nome       instala um mod do Claude Code de integrations/mod (repetível); ex.: --mod token-handoff
    --mod-scope s    project (padrão: só este projeto) ou global (todos os projetos do usuário)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    sys.path.insert(0, str(ROOT))
    from guilda import cli

    return cli.main(["install", *(sys.argv[1:] if argv is None else argv)])


if __name__ == "__main__":
    raise SystemExit(main())
