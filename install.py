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
import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILES = "base,product-team,github-projects"
DEFAULT_PROVIDERS = "claude,codex"


def load_mods():
    spec = importlib.util.spec_from_file_location("template_mods", ROOT / "scripts" / "mods.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_cli():
    spec = importlib.util.spec_from_file_location("template_cli", ROOT / "scripts" / "template.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", nargs="?", type=Path, default=Path.cwd(), help="projeto de destino (padrão: diretório atual)")
    parser.add_argument("--profiles")
    parser.add_argument("--providers")
    parser.add_argument("--tier", action="append", default=None, metavar="PAPEL=CAMADA")
    parser.add_argument("--mod", action="append", default=[], metavar="NOME", help="mod de integrations/mod; repetível")
    parser.add_argument("--mod-scope", choices=("project", "global"), default="project")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    target = args.target.resolve()
    if target.exists() and not target.is_dir():
        print(f"erro: {target} não é um diretório", file=sys.stderr)
        return 1
    if target == ROOT or ROOT in target.parents:
        print("erro: o destino não pode ser o próprio template; informe o caminho do seu projeto", file=sys.stderr)
        return 1

    cli = load_cli()
    manifest_path = target / ".engineering" / "manifest.json"
    installed = None
    if manifest_path.is_file():
        try:
            installed = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError:
            print(f"erro: manifesto ilegível: {manifest_path}", file=sys.stderr)
            return 1

    # Atualização reaproveita a escolha anterior, a menos que o usuário passe novas opções.
    profiles = (args.profiles or (",".join(installed["profiles"]) if installed else DEFAULT_PROFILES)).split(",")
    providers = (args.providers or (",".join(installed["providers"]) if installed else DEFAULT_PROVIDERS)).split(",")
    tiers = dict(installed.get("tiers", {})) if installed else {}
    for item in args.tier or []:
        role, sep, tier = item.partition("=")
        if not sep:
            print(f"erro: --tier espera PAPEL=CAMADA: {item}", file=sys.stderr)
            return 1
        tiers[role] = tier

    mode = "atualização" if installed else "instalação"
    try:
        result = cli.install(cli.SOURCE, target, providers, profiles, args.dry_run, sync=bool(installed), tiers=tiers)
        if not args.dry_run:
            cli.check(cli.SOURCE, target)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        if "drift" in str(exc) or "conflict" in str(exc):
            print("dica: há arquivos locais que conflitam com o template; resolva-os (mova ou reverta) e rode de novo.", file=sys.stderr)
        return 1

    verb = "seriam gravados" if args.dry_run else "gravados"
    print(f"{mode} ({'simulação' if args.dry_run else 'concluída'}) em {target}")
    print(f"  perfis: {', '.join(profiles)} | provedores: {', '.join(providers)}")
    print(f"  {len(result['write'])} arquivos {verb}, {len(result['remove'])} removidos")
    if args.dry_run:
        print("  rode sem --dry-run para aplicar.")
    else:
        print("  verificação (check): ok")
    for name in args.mod:
        try:
            mod = load_mods().install_mod(name, args.mod_scope, target, args.dry_run)
        except (ValueError, OSError) as exc:
            print(f"erro: mod {name}: {exc}", file=sys.stderr)
            return 1
        print(f"mod {name} {mod['version']} ({args.mod_scope}) — ATENÇÃO: {mod['warning']}")
        if args.dry_run:
            print("  seriam gravados: " + "; ".join(mod["write"]))
            print("  comandos: " + "; ".join(mod["commands"]))
        elif mod["installed"]:
            print(f"  instalado e registrado em {mod['registry']}")
        else:
            print(f"  arquivos copiados, mas o plugin NÃO foi instalado ({mod.get('claude_error', 'claude ausente do PATH')}).")
            print("  rode à mão: " + "; ".join(mod["commands"]))
            print(f"  registrado como não verificado em {mod['registry']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
