"""Confere se a tag de release bate com a versão do template e do pacote (só stdlib)."""
import json
import os
import re
import sys
from pathlib import Path

TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
VERSAO_RE = re.compile(r"""^__version__\s*=\s*["']([^"']+)["']""", re.MULTILINE)


def check(tag: str, root: Path) -> list[str]:
    """Devolve uma mensagem (em português) por problema; lista vazia quando está tudo certo."""
    problemas: list[str] = []
    root = Path(root)

    if not TAG_RE.match(tag):
        problemas.append(f"A tag '{tag}' não tem o formato vMAJOR.MINOR.PATCH (ex.: v2.0.0).")
    versao_tag = tag[1:] if TAG_RE.match(tag) else None

    template = None
    try:
        template = json.loads((root / "template.json").read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        problemas.append("Não foi possível ler a versão em template.json.")
    else:
        if template is None:
            problemas.append("template.json não tem o campo 'version'.")

    pacote = None
    try:
        achado = VERSAO_RE.search((root / "guilda" / "__version__.py").read_text(encoding="utf-8"))
        pacote = achado.group(1) if achado else None
    except OSError:
        pass
    if pacote is None:
        problemas.append("Não foi possível ler __version__ em guilda/__version__.py.")

    if versao_tag and template is not None and template != versao_tag:
        problemas.append(f"A tag {tag} difere da versão de template.json ({template}).")
    if template is not None and pacote is not None and template != pacote:
        problemas.append(f"A versão de template.json ({template}) difere de __version__ ({pacote}).")
    return problemas


def main() -> int:
    tag = os.environ.get("GITHUB_REF_NAME", "")
    problemas = check(tag, Path(__file__).resolve().parent.parent)
    for problema in problemas:
        print(f"ERRO: {problema}", file=sys.stderr)
    if not problemas:
        print(f"Tag {tag} confere com template.json e __version__.")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
