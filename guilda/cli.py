"""Comando `guilda`: init, sync, check, doctor, package, install, upgrade e mod."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from guilda import engine, mods, upgrade

DEFAULT_PROFILES = "base,product-team,github-projects"
DEFAULT_PROVIDERS = "claude,codex"
ENGINE_COMMANDS = ("init", "sync", "check", "doctor", "package")
INSTALL_HELP = """Instala (ou atualiza) o template de engenharia num projeto.

Uso:
    guilda install <projeto>                  # instala; se já instalado, atualiza
    guilda install <projeto> --dry-run        # só mostra o que mudaria
    guilda install                            # usa o diretório atual como projeto

Opções (todas opcionais):
    --profiles a,b   perfis (padrão: base,product-team,github-projects; em atualização, os já instalados)
    --providers a,b  claude,codex (padrão: claude,codex; em atualização, os já instalados)
    --tier papel=camada   repetível; ex.: --tier reviewer=deep
    --mod nome       instala um mod do Claude Code de integrations/mod (repetível); ex.: --mod token-handoff
    --mod-scope s    project (padrão: só este projeto) ou global (todos os projetos do usuário)
"""
YES = {"s", "sim", "y", "yes"}


def confirm(prompt: str, stdin=None, stdout=None) -> bool:
    """Pergunta s/n. Sem TTY devolve False sem ler nada."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    isatty = getattr(stdin, "isatty", None)
    if not callable(isatty) or not isatty():
        return False
    stdout.write(prompt)
    stdout.flush()
    return stdin.readline().strip().lower() in YES


def print_mod(name: str, scope: str, target: Path, dry_run: bool) -> int:
    """Instala um mod e imprime o resumo (usado por `install --mod` e por `mod`)."""
    try:
        mod = mods.install_mod(name, scope, target, dry_run)
    except (ValueError, OSError) as exc:
        print(f"erro: mod {name}: {exc}", file=sys.stderr)
        return 1
    print(f"mod {name} {mod['version']} ({scope}) — ATENÇÃO: {mod['warning']}")
    if dry_run:
        print("  seriam gravados: " + "; ".join(mod["write"]))
        print("  comandos: " + "; ".join(mod["commands"]))
    elif mod["installed"]:
        print(f"  instalado e registrado em {mod['registry']}")
    else:
        print(f"  arquivos copiados, mas o plugin NÃO foi instalado ({mod.get('claude_error', 'claude ausente do PATH')}).")
        print("  rode à mão: " + "; ".join(mod["commands"]))
        print(f"  registrado como não verificado em {mod['registry']}")
    return 0


def run_install(args) -> int:
    target = args.target.resolve()
    if target.exists() and not target.is_dir():
        print(f"erro: {target} não é um diretório", file=sys.stderr)
        return 1
    source = engine.SOURCE.resolve()
    if target == source or source in target.parents:
        print("erro: o destino não pode ser o próprio template; informe o caminho do seu projeto", file=sys.stderr)
        return 1

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
        result = engine.install(engine.SOURCE, target, providers, profiles, args.dry_run, sync=bool(installed), tiers=tiers)
        if not args.dry_run:
            engine.check(engine.SOURCE, target)
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
        if print_mod(name, args.mod_scope, target, args.dry_run):
            return 1
    return 0


def print_plan(plan: upgrade.Plan) -> None:
    for label, items in (("write", plan.write), ("remove", plan.remove), ("keep", plan.keep), ("conflicts", plan.conflicts)):
        print(f"{label} ({len(items)}):")
        for item in items:
            print(f"  {item}")
    print(f"migrate_name: {str(plan.migrate_name).lower()}")


def run_upgrade(args) -> int:
    target = args.target.resolve()
    try:
        plan = upgrade.plan_upgrade(engine.SOURCE, target)
        if args.dry_run:
            print_plan(plan)
            return 0
        approved = False
        if plan.conflicts and not args.yes:
            interactive = callable(getattr(sys.stdin, "isatty", None)) and sys.stdin.isatty()
            stream = sys.stdout if interactive else sys.stderr
            print(f"conflitos ({len(plan.conflicts)}): arquivos com alteração local que o template também mudou:", file=stream)
            for item in plan.conflicts:
                print(f"  {item}", file=stream)
            print("ATENÇÃO: continuar SOBRESCREVE esses arquivos e as alterações locais serão perdidas (não há backup).", file=stream)
            print("Para não perder uma alteração local, rode antes `guilda promote`.", file=stream)
            if not confirm("Continuar e sobrescrever? [s/N] ", sys.stdin, sys.stdout):
                print("erro: upgrade cancelado; nada foi alterado (use --yes para aprovar).", file=sys.stderr)
                return 1
            approved = True
        result = upgrade.apply_upgrade(engine.SOURCE, target, plan, approved=approved or bool(args.yes))
        engine.check(engine.SOURCE, target)
    except (ValueError, KeyError, OSError, TypeError, upgrade.UpgradeRefused) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    print(f"atualização concluída em {target}")
    print(f"  {len(result['write'])} arquivos gravados, {len(result['remove'])} removidos, {len(result['kept'])} mantidos")
    if result["migrated"]:
        print("  manifesto migrado para o nome guilda")
    print("  verificação (check): ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="guilda", description="Template de engenharia: instala, atualiza e verifica projetos.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="comando")
    for name in ENGINE_COMMANDS:
        # Mesmos parâmetros do motor; repassados sem alteração.
        p = sub.add_parser(name, add_help=False, help=f"{name} (flags do motor: --target --providers --provider --profiles --tier --dry-run)")
        p.add_argument("rest", nargs=argparse.REMAINDER)

    p = sub.add_parser("install", help="instala (ou atualiza) o template num projeto", description=INSTALL_HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", nargs="?", type=Path, default=Path.cwd(), help="projeto de destino (padrão: diretório atual)")
    p.add_argument("--profiles")
    p.add_argument("--providers")
    p.add_argument("--tier", action="append", default=None, metavar="PAPEL=CAMADA")
    p.add_argument("--mod", action="append", default=[], metavar="NOME", help="mod de integrations/mod; repetível")
    p.add_argument("--mod-scope", choices=("project", "global"), default="project")
    p.add_argument("--dry-run", action="store_true")

    p = sub.add_parser("upgrade", help="atualiza um projeto instalado para o template atual")
    p.add_argument("target", nargs="?", type=Path, default=Path.cwd(), help="projeto de destino (padrão: diretório atual)")
    p.add_argument("--dry-run", action="store_true", help="só mostra o plano")
    p.add_argument("--yes", action="store_true", help="aprova a sobrescrita de arquivos com alteração local")

    p = sub.add_parser("mod", help="instala um mod do Claude Code")
    p.add_argument("name", metavar="nome")
    p.add_argument("--scope", choices=("project", "global"), default="project")
    p.add_argument("--target", type=Path, default=Path.cwd())
    p.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] in ENGINE_COMMANDS:
        return engine.main(argv)  # mesmos parâmetros do motor, sem reinterpretar
    args = build_parser().parse_args(argv)
    if args.command == "install":
        return run_install(args)
    if args.command == "upgrade":
        return run_upgrade(args)
    return print_mod(args.name, args.scope, args.target.resolve(), args.dry_run)
