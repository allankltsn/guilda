"""Comando `guilda`: init, sync, check, doctor, package, install, upgrade, mod, promote, self-update e config."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from guilda import __version__, config, engine, mods, promote, selfupdate, upgrade
from guilda.prompt import YES, confirm  # noqa: F401  (confirm é reexportado)

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
        # Not engine.check: it treats the files kept on purpose (result["kept"]) as drift.
        upgrade.verify(engine.SOURCE, target)
    except (ValueError, KeyError, OSError, TypeError, upgrade.UpgradeRefused) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    print(f"atualização concluída em {target}")
    print(f"  {len(result['write'])} arquivos gravados, {len(result['remove'])} removidos, {len(result['kept'])} mantidos")
    if result["migrated"]:
        print("  manifesto migrado para o nome guilda")
    print("  verificação (check): ok")
    return 0


def run_promote(args, runner) -> int:
    try:
        result = promote.promote(engine.SOURCE, args.target.resolve(), args.title, args.description, assume_yes=args.yes, runner=runner, stdin=sys.stdin, stdout=sys.stdout)
    except promote.PromoteError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        if exc.gist_url and exc.gist_url not in str(exc):
            print(f"gist: {exc.gist_url}", file=sys.stderr)
        return 1
    print(f"gist (secreto): {result['gist']}")
    print(f"issue: {result['issue']}")
    return 0


def run_self_update(args, runner) -> int:
    command = selfupdate.upgrade_command()
    if args.dry_run:
        print("executaria: " + " ".join(command))
        return 0
    if not args.yes:
        print("self-update INSTALA software: " + " ".join(command), file=sys.stderr)
        if not confirm("Continuar? [s/N] ", sys.stdin, sys.stdout):
            print("erro: self-update cancelado; nada foi executado (use --yes para aprovar).", file=sys.stderr)
            return 1
    code = selfupdate.upgrade_self(runner)
    if code:
        print(f"erro: a atualização do guilda falhou (código {code})", file=sys.stderr)
        return 1
    print("guilda atualizado.")
    return 0


def run_config(args) -> int:
    cfg = config.load()
    if args.config_action == "get":
        print(json.dumps(cfg, indent=2))
        return 0
    try:
        cfg["update_check"] = args.value
        config.save(cfg)
    except (ValueError, OSError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 1
    print(f"update-check = {args.value}")
    return 0


def startup_check(opener, runner) -> None:
    """Verificação automática opcional no início; NUNCA falha nem interrompe o comando."""
    try:
        cfg = config.load()
        if cfg["update_check"] == "off":
            return
        now = datetime.now(timezone.utc)
        if not selfupdate.is_due(now, cfg):
            return
        # Grava antes de consultar: no máximo uma consulta por dia, mesmo se a rede falhar.
        config.save({**cfg, "last_check": now.isoformat()})
        newest = selfupdate.check_if_due(now, cfg, opener)
        if not newest:
            return
        if cfg["update_check"] == "notify":
            print(f"guilda {newest} disponível (instalada: {__version__}). Rode: guilda self-update", file=sys.stderr)
        else:
            code = selfupdate.upgrade_self(runner, capture=True)
            print(f"guilda atualizado para {newest}" if code == 0 else "guilda: falha ao atualizar automaticamente (veja: guilda self-update)", file=sys.stderr)
    except Exception:  # noqa: BLE001 - a verificação nunca derruba o comando
        return


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

    p = sub.add_parser("promote", help="propõe suas alterações locais como feature (gist secreto + issue)")
    p.add_argument("target", type=Path, metavar="projeto")
    p.add_argument("--title", required=True)
    p.add_argument("--description", required=True)
    p.add_argument("--yes", action="store_true", help="envia sem perguntar (a varredura de segredos continua obrigatória)")

    p = sub.add_parser("self-update", help="atualiza o próprio guilda (pip ou uv)")
    p.add_argument("--dry-run", action="store_true", help="só mostra o comando que rodaria")
    p.add_argument("--yes", action="store_true", help="não pergunta antes de instalar")

    p = sub.add_parser("config", help="mostra ou altera a configuração do usuário")
    csub = p.add_subparsers(dest="config_action", required=True, metavar="ação")
    csub.add_parser("get", help="mostra a configuração efetiva (JSON)")
    p = csub.add_parser("set", help="altera um valor")
    p.add_argument("key", choices=("update-check",))
    p.add_argument("value", choices=config.UPDATE_CHECK_VALUES)

    p = sub.add_parser("mod", help="instala um mod do Claude Code")
    p.add_argument("name", metavar="nome")
    p.add_argument("--scope", choices=("project", "global"), default="project")
    p.add_argument("--target", type=Path, default=Path.cwd())
    p.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None, runner=subprocess.run, opener=urllib.request.urlopen) -> int:
    """`runner` e `opener` são ganchos de teste (gh/pip/uv e consulta ao PyPI)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] in ENGINE_COMMANDS:
        if "-h" not in argv and "--help" not in argv:
            startup_check(opener, runner)
        return engine.main(argv)  # mesmos parâmetros do motor, sem reinterpretar
    args = build_parser().parse_args(argv)  # --help e erros de uso saem aqui, antes da verificação
    if args.command == "self-update":
        return run_self_update(args, runner)
    if args.command == "config":
        return run_config(args)  # sem verificação: não polui o JSON de `get` nem age antes de `set`
    startup_check(opener, runner)
    if args.command == "install":
        return run_install(args)
    if args.command == "upgrade":
        return run_upgrade(args)
    if args.command == "promote":
        return run_promote(args, runner)
    return print_mod(args.name, args.scope, args.target.resolve(), args.dry_run)
