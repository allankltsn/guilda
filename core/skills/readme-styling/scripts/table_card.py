#!/usr/bin/env python3
"""Gera cartões de tabela em SVG (tema dark pipeline) a partir de uma tabela markdown. Só biblioteca padrão.

Uso:
  python table_card.py tabela.md saida.svg --title "Opções" [--width 920] [--first 220]

A entrada é uma tabela markdown comum (cabeçalho, linha `| --- |`, linhas). Dentro das células,
`código` vira monoespaçado em teal e **negrito** fica branco. Texto longo quebra em linhas.

Por quê: o GitHub renderiza tabela markdown com o tema dele e sem controle de cor. O cartão fixa o
visual do projeto, mas é imagem: não dá para copiar nem buscar. No README, deixe a tabela em
markdown logo abaixo, em <details> (veja SKILL.md, seção 5).
"""
import argparse
import re
import sys
from xml.sax.saxutils import escape

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
C = {"bg": "#0b0f17", "surface": "#111827", "alt": "#0f1623", "border": "#1f2937", "text": "#c9d4e3",
     "strong": "#e6edf3", "muted": "#8b96a8", "code": "#2dd4bf", "head": "#8b96a8", "accent": "#2dd4bf"}
FS, CW_SANS, CW_MONO, LH, PAD = 13, 7.0, 7.9, 19, 16
HEAD_H = 40


def parse_table(text):
    rows = [l.strip() for l in text.strip().splitlines() if l.strip().startswith("|")]
    cells = [[c.strip() for c in re.split(r"(?<!\\)\|", r.strip().strip("|"))] for r in rows]
    cells = [[c.replace("\\|", "|") for c in r] for r in cells]
    if len(cells) < 2 or not all(re.fullmatch(r":?-{2,}:?", c.replace(" ", "")) for c in cells[1]):
        sys.exit("tabela markdown inválida: falta a linha de separação (| --- | --- |)")
    return cells[0], [r + [""] * (len(cells[0]) - len(r)) for r in cells[2:]]


def segments(cell):
    """Divide a célula em (texto, estilo): code, strong ou plain."""
    out = []
    for part in re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", cell):
        if not part:
            continue
        if part.startswith("`"):
            out.append((part[1:-1], "code"))
        elif part.startswith("**"):
            out.append((part[2:-2], "strong"))
        else:
            out.append((re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", part), "plain"))
    return out


def width_of(text, style):
    return len(text) * (CW_MONO if style == "code" else CW_SANS)


def wrap(cell, max_w):
    """Quebra por palavras preservando o estilo; devolve linhas de [(texto, estilo)]."""
    words = []
    for text, style in segments(cell):
        for w in re.findall(r"\s*\S+\s*", text):
            words.append((w, style))
    lines, cur, cur_w = [], [], 0.0
    for w, style in words:
        ww = width_of(w.rstrip(), style)
        if cur and cur_w + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((w, style))
        cur_w += width_of(w, style)
    if cur:
        lines.append(cur)
    return lines or [[("", "plain")]]


def span(text, style):
    fill = {"code": C["code"], "strong": C["strong"]}.get(style, C["text"])
    extra = f' font-family="{MONO}" font-size="{FS - 1}"' if style == "code" else (' font-weight="700"' if style == "strong" else "")
    return f'<tspan fill="{fill}"{extra}>{escape(text)}</tspan>'


def render(header, rows, title, width, first):
    ncols = len(header)
    inner = width - 2 * PAD
    longest0 = max([len(re.sub(r"[`*]", "", r[0])) for r in rows] + [len(header[0])])
    w0 = first or min(max(int(longest0 * CW_MONO) + 2 * PAD, 130), int(inner * 0.34))
    rest = (inner - w0 + PAD) / max(ncols - 1, 1) if ncols > 1 else 0
    col_w = [w0] + [rest] * (ncols - 1)
    xs = [PAD]
    for w in col_w[:-1]:
        xs.append(xs[-1] + w)
    title_h = 36 if title else 0
    laid = []
    for r in rows:
        wrapped = [wrap(r[i], col_w[i] - PAD - 6) for i in range(ncols)]
        n = max(len(w) for w in wrapped)
        laid.append((wrapped, n, n * LH + 18))
    height = title_h + HEAD_H + sum(h for _, _, h in laid) + 6
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
         f'font-family="{FONT}" font-size="{FS}" role="img" aria-label="{escape(title or "Tabela")}: {len(rows)} linhas, '
         f'colunas {escape(", ".join(header))}">',
         f'<rect width="{width}" height="{height}" rx="10" fill="{C["bg"]}"/>',
         f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{C["surface"]}" stroke="{C["border"]}"/>']
    y = 0
    if title:
        o.append(f'<text x="{PAD}" y="24" font-size="14" font-weight="700" fill="{C["strong"]}">{escape(title)}</text>')
        o.append(f'<rect x="{PAD}" y="31" width="28" height="2" rx="1" fill="{C["accent"]}"/>')
        y = title_h
    o.append(f'<rect x="1" y="{y}" width="{width - 2}" height="{HEAD_H}" fill="{C["bg"]}"/>')
    for i, h in enumerate(header):
        o.append(f'<text x="{xs[i]}" y="{y + 25}" font-size="11" font-weight="700" letter-spacing="1" fill="{C["head"]}">{escape(h.upper())}</text>')
    y += HEAD_H
    o.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" stroke="{C["accent"]}" stroke-opacity="0.5"/>')
    for k, (wrapped, n, h) in enumerate(laid):
        if k % 2:
            o.append(f'<rect x="1" y="{y}" width="{width - 2}" height="{h}" fill="{C["alt"]}"/>')
        for i in range(ncols):
            for li, line in enumerate(wrapped[i]):
                ty = y + 9 + (li + 1) * LH - 4
                o.append(f'<text x="{xs[i]}" y="{ty}" xml:space="preserve">{"".join(span(t, s) for t, s in line)}</text>')
        y += h
        if k < len(laid) - 1:
            o.append(f'<line x1="{PAD}" y1="{y}" x2="{width - PAD}" y2="{y}" stroke="{C["border"]}"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="arquivo com a tabela markdown, ou - para stdin")
    ap.add_argument("out")
    ap.add_argument("--title", default="")
    ap.add_argument("--width", type=int, default=920)
    ap.add_argument("--first", type=int, default=0, help="largura da 1ª coluna em px (0 = automática)")
    a = ap.parse_args()
    text = sys.stdin.read() if a.source == "-" else open(a.source, encoding="utf-8").read()
    header, rows = parse_table(text)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(header, rows, a.title, a.width, a.first))
    print(f"tabela: {len(rows)} linhas, {len(header)} colunas -> {a.out}")


if __name__ == "__main__":
    main()
