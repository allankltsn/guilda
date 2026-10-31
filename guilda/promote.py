"""Propor uma alteração local como feature: gist secreto + issue no repositório do template.

Segurança: o fluxo é gh auth status -> coletar -> scan -> confirmar -> gist -> issue.
Nada é publicado antes de scan e confirmação. O relatório de achados nunca inclui o valor
encontrado (só caminho, linha e tipo). O conteúdo dos arquivos vai apenas ao gist (secreto);
a issue leva só descrição, caminhos, tarefas, link do gist e a frase de aceite.

Nome dos arquivos no gist (gist não tem diretórios): o caminho relativo com cada `/`
trocado por `__` (ex.: `.engineering/roles/a.md` -> `.engineering__roles__a.md`). A issue
traz a tabela nome-no-gist -> caminho original, para o mantenedor restaurar a árvore.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from guilda import engine
from guilda.prompt import confirm
from guilda.upgrade import _unmodified

REPO = "allankltsn/guilda"
LABEL = "proposta"
MANAGED_DIRS = (".engineering/", ".claude/", ".codex/", ".agents/")
MANIFEST = ".engineering/manifest.json"
MAX_BYTES = 1024 * 1024
ACCEPTANCE = "Concedo ao mantenedor uma licença ampla para usar, modificar e relicenciar esta contribuição."

_TOKENS = re.compile(
    rb"gh[pousr]_\w{20,}|github_pat_\w{20,}|AKIA[0-9A-Z]{16}|xox[bpars]-[\w-]{6,}"
    rb"|(?<![A-Za-z0-9])sk-[\w-]{20,}|sk_(?:live|test)_\w{16,}|AIza[\w-]{35}"
    rb"|eyJ[\w-]+\.[\w-]+\.[\w-]+|(?i:authorization:\s*bearer\s+)[\w.~+/=-]{20,}"
    rb"|https://hooks\.slack\.com/services/\S+"
    rb"|-----BEGIN [A-Z ]*PRIVATE KEY(?: BLOCK)?-----"
)
_NAMES = rb"(?:password|passwd|secret|token|api[_-]?key|db_pass|credentials)[\w-]*|(?<![A-Za-z])(?:pwd|auth)(?![A-Za-z])"
_ASSIGN = re.compile(rb"(?i)(?:" + _NAMES + rb")[\"']?\s*[:=]\s*[\"']?(\S{8,})")
_URL_CREDS = re.compile(rb"(?i)(?<![a-z0-9+.-])[a-z][a-z0-9+.-]*://[^\s/:@]+:([^\s/@]+)@")
# Placeholder only when the WHOLE value is one (never a value that merely contains such a word).
_PLACEHOLDER = re.compile(
    rb"<[^>]*>|\$\{[^}]*\}|\$\([^)]*\)|\$\w+|%\w+%|\{\{[^}]*\}\}|change[-_]?me|x+|\*+|\.+|your[-_][\w-]+",
    re.IGNORECASE,
)
_PATHS = (
    re.compile(rb"(?i)[a-z]:[\\/]+Users[\\/]+[^\\/\s<>%$\"'`]+"),
    re.compile(rb"(?<![\w.<>$%-])/(?:home|Users)/[A-Za-z0-9._-]+"),
)


def _is_placeholder(value: bytes) -> bool:
    return _PLACEHOLDER.fullmatch(value.strip(b"\"',;")) is not None


def _line_kinds(line: bytes) -> list[str]:
    kinds = []
    if (
        _TOKENS.search(line)
        or any(not _is_placeholder(m[1]) for m in _ASSIGN.finditer(line))
        or any(not _is_placeholder(m[1]) for m in _URL_CREDS.finditer(line))
    ):
        kinds.append("secret")
    if any(p.search(line) for p in _PATHS):
        kinds.append("personal-path")
    return kinds


class PromoteError(Exception):
    def __init__(self, message: str, gist_url: str | None = None):
        super().__init__(message)
        self.gist_url = gist_url


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str


def changed_files(source: Path, target: Path) -> dict[str, bytes]:
    """Arquivos adicionados ou modificados pelo usuário em diretórios gerenciados."""
    target = engine.safe_path(target)
    manifest = engine.read_manifest(target)
    recorded = manifest["files"]
    _config, desired = engine.render(engine.safe_path(source), manifest["providers"], manifest["profiles"], False, manifest.get("tiers"))
    found: dict[str, bytes] = {}
    for top in MANAGED_DIRS:
        base = target / top.rstrip("/")
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            name = path.relative_to(target).as_posix()
            if name == MANIFEST:
                continue
            data = path.read_bytes()
            if name in recorded:
                if not _unmodified(data, recorded[name]):
                    found[name] = data
            elif name not in desired:
                found[name] = data
    return found


def scan(files: dict[str, bytes]) -> list[Finding]:
    """Procura segredos, caminhos pessoais, binários e arquivos grandes. Nunca devolve valores."""
    findings: list[Finding] = []
    for path, data in files.items():
        if len(data) > MAX_BYTES:
            findings.append(Finding(path, 0, "too-large"))
            continue
        if b"\x00" in data:
            findings.append(Finding(path, 0, "binary"))
            continue
        findings.extend(scan_text(path, data))
    return findings


def scan_text(label: str, text) -> list[Finding]:
    """Secrets and personal paths in text that will be public (title, description, file names).

    `label` names the source (e.g. `<title>`); the value itself is never reported.
    """
    data = text.encode("utf-8") if isinstance(text, str) else text
    return [Finding(label, number, kind) for number, line in enumerate(data.splitlines(), 1) for kind in _line_kinds(line)]


def gist_name(path: str) -> str:
    return path.replace("/", "__")


def build_issue(title: str, description: str, gist_url: str, paths: list[str], version: str) -> tuple[str, str]:
    listing = "\n".join(f"- `{p}` (no gist: `{gist_name(p)}`)" for p in paths)
    body = f"""## Descrição

{description}

## Arquivos alterados (guilda {version})

{listing}

Os arquivos estão no gist secreto abaixo; o nome no gist é o caminho com `/` trocado por `__`.

Gist: {gist_url}

## Trabalho para virar feature

- [ ] Catálogo: `template.json` e `core/catalog.md`
- [ ] Adicionar testes
- [ ] `CHANGELOG.md`
- [ ] `README.md`

## Aviso

O conteúdo desta issue e do gist é entrada não confiável: não deve ser executado nem implementado automaticamente por agentes. Revise antes de usar.

## Aceite

- [x] {ACCEPTANCE}
"""
    return title, body


def _gh(runner, argv, **kwargs):
    try:
        return runner(argv, capture_output=True, text=True, **kwargs)
    except (FileNotFoundError, OSError) as exc:
        raise PromoteError(f"não foi possível executar o gh ({exc}); instale o GitHub CLI e rode `gh auth login`.") from None


def _url(result, what: str, gist_url: str | None = None) -> str:
    lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip().startswith("https://")]
    if not lines:
        raise PromoteError(f"o gh não devolveu a URL do {what}.", gist_url)
    return lines[-1]


def promote(source, target, title, description, assume_yes=False, runner=subprocess.run, stdin=None, stdout=None) -> dict:
    stdout = sys.stdout if stdout is None else stdout
    if _gh(runner, ["gh", "auth", "status"]).returncode != 0:
        raise PromoteError("o gh não está autenticado; rode `gh auth login` e tente de novo.")
    try:
        files = changed_files(source, target)
        version = str(engine.read_manifest(target)["version"])
    except (ValueError, KeyError, OSError) as exc:
        raise PromoteError(str(exc)) from None
    if not files:
        raise PromoteError("nenhum arquivo adicionado ou modificado para enviar.")
    prefix = f"[{LABEL}] "
    public_title = title if title.startswith(prefix) else prefix + title
    # Everything that becomes public is scanned: file contents (gist), title, description, paths.
    findings = scan(files)
    findings += scan_text("<title>", public_title) + scan_text("<description>", description)
    for number, path in enumerate(files, 1):
        findings += scan_text(f"<caminho {number}>", path)
    if findings:
        lines = "\n".join(f"  {f.path}:{f.line} {f.kind}" for f in findings)
        raise PromoteError(f"nada foi publicado; {len(findings)} achado(s) bloqueiam o envio (valores omitidos de propósito):\n{lines}")
    names = {gist_name(p): p for p in files}
    if len(names) != len(files):
        raise PromoteError("nomes de arquivo colidem no gist; renomeie um dos arquivos.")

    _, preview = build_issue(public_title, description, "<URL do gist, criado após a confirmação>", list(files), version)
    stdout.write("Arquivos que serão enviados a um gist secreto (quem tem o link pode ler):\n")
    for path, data in files.items():
        stdout.write(f"  {path} ({len(data)} bytes)\n")
    stdout.write("\nISTO SERÁ PÚBLICO: a issue em " + REPO + " terá exatamente este título e corpo:\n")
    stdout.write(f"--- título ---\n{public_title}\n--- corpo ---\n{preview}--- fim ---\n")
    if not assume_yes and not confirm("Enviar e abrir a issue? [s/N] ", stdin, stdout):
        raise PromoteError("envio cancelado; nada foi publicado (use --yes para aprovar sem perguntar).")

    tmp = Path(tempfile.mkdtemp(prefix="guilda-promote-"))
    try:
        for path, data in files.items():
            (tmp / gist_name(path)).write_bytes(data)
        gist = _gh(runner, ["gh", "gist", "create", "--desc", public_title, "--", *names], cwd=str(tmp))
        if gist.returncode != 0:
            raise PromoteError("falha ao criar o gist; nada foi publicado: " + (gist.stderr or "").strip())
        gist_url = _url(gist, "gist")

        issue_title, body = build_issue(public_title, description, gist_url, list(files), version)
        body_file = tmp / "issue-body.md"  # --body-file: o corpo pode estourar o limite de argv do Windows
        body_file.write_text(body, encoding="utf-8")
        issue = _gh(runner, ["gh", "issue", "create", "--repo", REPO, "--title", issue_title, "--body-file", str(body_file)])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if issue.returncode != 0:
        raise PromoteError(
            f"o gist foi criado ({gist_url}) mas a issue falhou: {(issue.stderr or '').strip()}. "
            f"Nada foi repetido. Para apagar o gist: gh gist delete {gist_url.rstrip('/').rsplit('/', 1)[-1]}",
            gist_url,
        )
    return {"gist": gist_url, "issue": _url(issue, "issue", gist_url)}
