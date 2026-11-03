#!/usr/bin/env python3
"""Instalador de mods do Claude Code (integrations/mod/<nome>); Python 3.11+, só biblioteca padrão.

Um mod é um plugin local (hooks que mudam o comportamento da sessão). O instalador copia os arquivos para
<escopo>/.claude/mods, registra essa pasta como marketplace local e instala o plugin pelo mecanismo do próprio
Claude Code (claude plugin marketplace add / install). O comando é a aprovação explícita do usuário
(policies/installations.md); cada instalação ganha uma linha em docs/operations/registro-instalacoes.md.
"""
from __future__ import annotations

import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
MARKETPLACE = "engineering-template-mods"
SCOPES = ("project", "global")
CLAUDE_SCOPE = {"project": "project", "global": "user"}
# Arquivos de desenvolvimento que não viajam para o projeto do usuário.
SKIP = ("*.test.ts", "tsconfig.json", "scripts")

MODS = {
    "token-handoff": {
        "summary": "aos 400k tokens grava o prompt de continuação, abre a sessão nova com ele e encerra a atual, sem perguntar ao humano",
        "warning": "este mod EXECUTA um script PowerShell e ENCERRA o processo da sessão do Claude Code aos 400k tokens",
        "windows_only": True,
        "scripts": {"scripts/handoff-sessao.ps1": "handoff-sessao.ps1"},
    }
}


def _ignore(_dir, names):
    import fnmatch

    return [n for n in names if any(fnmatch.fnmatch(n, pattern) for pattern in SKIP)]


def _paths(name, scope, target, home):
    base = (Path(target) / ".claude") if scope == "project" else (Path(home) / ".claude")
    return base, base / "mods", base / "scripts"


def _marketplace(mods_root):
    path = mods_root / ".claude-plugin" / "marketplace.json"
    current = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    plugins = {p["name"]: p for p in current.get("plugins", [])}
    return path, plugins


def _registry_row(target, row):
    registry = Path(target) / "docs" / "operations" / "registro-instalacoes.md"
    if not registry.is_file():
        registry.parent.mkdir(parents=True, exist_ok=True)
        template = SOURCE / "core" / "templates" / "registro-instalacoes.md"
        registry.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    lines = registry.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        if line.startswith("|---|") and i > 0 and line.count("|") == lines[i - 1].count("|"):
            lines.insert(i + 1, row)
            break
    else:
        lines.append(row)
    registry.write_text("\n".join(lines), encoding="utf-8")
    return registry


def install_mod(name, scope, target, dry_run=False, home=None, run=subprocess.run, platform=None):
    """Instala o mod `name` no escopo `project` (em `target`) ou `global` (em ~/.claude). Devolve um resumo."""
    if name not in MODS:
        raise ValueError(f"mod desconhecido: {name} (disponíveis: {', '.join(sorted(MODS))})")
    if scope not in SCOPES:
        raise ValueError(f"escopo inválido: {scope} (use {' ou '.join(SCOPES)})")
    spec = MODS[name]
    if spec.get("windows_only") and (platform or sys.platform) != "win32":
        raise ValueError(f"o mod {name} depende de PowerShell e do Windows Terminal; só instala no Windows")
    source = SOURCE / "integrations" / "mod" / name
    if not (source / ".claude-plugin" / "plugin.json").is_file():
        raise ValueError(f"fonte do mod ausente: {source}")
    version = json.loads((source / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
    base, mods_root, scripts_dir = _paths(name, scope, target, home or Path.home())
    claude_scope = CLAUDE_SCOPE[scope]
    plugin_ref = f"{name}@{MARKETPLACE}"
    commands = [
        ["claude", "plugin", "marketplace", "add", str(mods_root), "--scope", claude_scope],
        ["claude", "plugin", "install", plugin_ref, "--scope", claude_scope],
    ]
    remove = f"claude plugin uninstall {plugin_ref} --scope {claude_scope}; apagar {mods_root / name} e {', '.join(str(scripts_dir / d) for d in spec['scripts'].values())}"
    summary = {
        "mod": name, "scope": scope, "version": version, "warning": spec["warning"],
        "write": [str(mods_root / name), str(mods_root / ".claude-plugin" / "marketplace.json")]
                 + [str(scripts_dir / d) for d in spec["scripts"].values()],
        "commands": [" ".join(c) for c in commands], "dry_run": dry_run,
    }
    if dry_run:
        return summary

    dest = mods_root / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, ignore=_ignore)
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for src, out in spec["scripts"].items():
        shutil.copy2(source / src, scripts_dir / out)
    path, plugins = _marketplace(mods_root)
    plugins[name] = {"name": name, "source": f"./{name}", "description": spec["summary"], "version": version}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"name": MARKETPLACE, "owner": {"name": "engineering-template"}, "plugins": list(plugins.values())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    results = []
    ok = shutil.which("claude") is not None
    if ok:
        for command in commands:
            done = run(command, cwd=str(target) if scope == "project" else None, capture_output=True, text=True, timeout=120)
            results.append(done.returncode)
            if done.returncode != 0:
                summary["claude_error"] = (done.stderr or done.stdout or "").strip()[:300]
                ok = False
                break
    summary["installed"] = ok
    verification = "claude plugin marketplace add + install: ok" if ok else "arquivos copiados; plugin NÃO instalado, rode os comandos de `commands` à mão (not verified)"
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    row = (f"| {today} | mod {name} (Claude Code) | integrations/mod/{name} | {version} | {'project' if scope == 'project' else 'user/global'} "
           f"| usuário, via install.py --mod {name} | {', '.join(Path(p).as_posix() for p in summary['write'])} | {remove} | {verification} |")
    summary["registry"] = str(_registry_row(target, row))
    return summary
