#!/usr/bin/env python3
"""Recolore ícones Lucide (assets/icons/lucide) para uso em README. Só biblioteca padrão.

Uso:
  python lucide_icon.py rocket rocket.svg --color "#2dd4bf" --size 20
  python lucide_icon.py rocket shield-check git-branch --color "#2dd4bf" --out-dir assets/icons/teal
  python lucide_icon.py --list [filtro]

Por quê: o GitHub renderiza <img src="x.svg"> sem herdar CSS, então `currentColor` vira preto e
some no tema dark. O script grava uma cópia com a cor fixa (stroke), tamanho e espessura escolhidos.
"""
import argparse
import re
import sys
from pathlib import Path


def find_icons_dir(explicit):
    if explicit:
        return Path(explicit)
    for base in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]:
        candidate = base / "assets" / "icons" / "lucide"
        if candidate.is_dir():
            return candidate
    sys.exit("assets/icons/lucide não encontrado; passe --dir")


def recolor(svg, color, size, stroke):
    svg = re.sub(r"<!--.*?-->\s*", "", svg, flags=re.S)
    svg = re.sub(r'\sclass="[^"]*"', "", svg)
    svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
    svg = re.sub(r'width="24"', f'width="{size}"', svg, count=1)
    svg = re.sub(r'height="24"', f'height="{size}"', svg, count=1)
    svg = re.sub(r'stroke-width="[\d.]+"', f'stroke-width="{stroke}"', svg, count=1)
    return re.sub(r"\s*\n\s*", " ", svg).replace('" >', '">').strip() + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="nome(s) do ícone, sem .svg; com um nome, o 2º argumento posicional pode ser o arquivo de saída")
    ap.add_argument("--color", default="#2dd4bf")
    ap.add_argument("--size", type=int, default=20)
    ap.add_argument("--stroke", default="2", help="espessura do traço (Lucide usa 2; 1.5 fica mais fino)")
    ap.add_argument("--out-dir", help="grava <nome>.svg nesta pasta")
    ap.add_argument("--dir", help="pasta dos ícones originais")
    ap.add_argument("--list", action="store_true", help="lista os nomes disponíveis (filtro opcional em names[0])")
    args = ap.parse_args()
    icons = find_icons_dir(args.dir)

    if args.list:
        needle = args.names[0] if args.names else ""
        for p in sorted(icons.glob("*.svg")):
            if needle in p.stem:
                print(p.stem)
        return

    names, out_file = list(args.names), None
    if len(names) == 2 and names[1].endswith(".svg"):
        names, out_file = names[:1], Path(names[1])
    if not names:
        ap.error("informe ao menos um ícone")
    for name in names:
        src = icons / f"{name}.svg"
        if not src.is_file():
            sys.exit(f"ícone inexistente: {name} (use --list {name[:4]})")
        out = recolor(src.read_text(encoding="utf-8"), args.color, args.size, args.stroke)
        target = out_file or (Path(args.out_dir or ".") / f"{name}.svg")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(out, encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
