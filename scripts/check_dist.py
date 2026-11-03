"""Inspeciona os arquivos reais de dist/ (wheel e sdist) antes da publicação (só stdlib)."""
import sys
import tarfile
import zipfile
from pathlib import Path

# Segmentos de caminho proibidos (casamento por segmento, nunca por substring).
PROIBIDOS_WHEEL = ("docs", "assets", "tests", ".github", "graphify-out", ".dev", ".worktrees", "plans", "specs")
PROIBIDOS_SDIST = ("superpowers", "plans", "specs", "graphify-out", ".worktrees", ".dev")


def _proibidos(nomes, proibidos, rotulo):
    problemas = []
    for nome in nomes:
        for seg in nome.split("/"):
            if seg in proibidos:
                problemas.append(f"{rotulo} contém caminho proibido: {nome}")
                break
    return problemas


def check(dist: Path) -> list[str]:
    """Uma mensagem por problema; lista vazia quando a distribuição está correta."""
    dist = Path(dist)
    problemas: list[str] = []
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    if len(wheels) != 1:
        problemas.append(f"Esperado exatamente 1 wheel em {dist}, encontrado {len(wheels)}.")
    if len(sdists) != 1:
        problemas.append(f"Esperado exatamente 1 sdist em {dist}, encontrado {len(sdists)}.")
    for wheel in wheels[:1]:
        with zipfile.ZipFile(wheel) as z:
            nomes = z.namelist()
        if "guilda/_data/template.json" not in nomes:
            problemas.append("O wheel não contém guilda/_data/template.json.")
        if not any(n.startswith("guilda/_data/core/") for n in nomes):
            problemas.append("O wheel não contém guilda/_data/core/.")
        if not any(n.split("/")[-1] == "LICENSE" for n in nomes):
            problemas.append("O wheel não contém LICENSE.")
        problemas += _proibidos(nomes, PROIBIDOS_WHEEL, "O wheel")
    for sdist in sdists[:1]:
        with tarfile.open(sdist) as t:
            nomes = [n.split("/", 1)[1] for n in t.getnames() if "/" in n]
        problemas += _proibidos(nomes, PROIBIDOS_SDIST, "O sdist")
    return problemas


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    problemas = check(Path(argv[0] if argv else "dist"))
    for problema in problemas:
        print(f"ERRO: {problema}", file=sys.stderr)
    if not problemas:
        print("Distribuição confere.")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
