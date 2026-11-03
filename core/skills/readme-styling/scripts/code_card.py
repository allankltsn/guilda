#!/usr/bin/env python3
"""Gera cartões de código em SVG (tema dark pipeline, realce por linguagem). Só biblioteca padrão.

Uso:
  python code_card.py comandos.txt saida.svg --lang bash --title "Instalar"
  cat script.py | python code_card.py - saida.svg --lang python --title "uso.py"

Linguagens: tree (árvore de diretórios), bash (sh, shell), console (linhas com "$ " são comandos, o resto é saída),
python, yaml, json, text. Opções: --anim (revela linha a linha; padrão estático, porque o cartão carrega informação essencial
e uma animação que falha deixaria o texto invisível), --width N (mínimo).

Por quê: o GitHub escolhe o tema dos blocos de código e quase não colore comandos de CLI. O cartão
fixa as cores do projeto, mas é imagem: não dá para copiar. No README, deixe o texto copiável logo
abaixo, em <details> (veja SKILL.md, seção 5).
"""
import argparse
import re
import sys
from xml.sax.saxutils import escape

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
C = {"bg": "#0b0f17", "surface": "#111827", "border": "#1f2937", "text": "#e6edf3", "muted": "#8b96a8",
     "dim": "#4b5563", "cmd": "#60a5fa", "flag": "#f59e0b", "str": "#4ade80", "num": "#f472b6",
     "ph": "#a78bfa", "kw": "#f472b6", "fn": "#2dd4bf", "key": "#60a5fa", "ok": "#4ade80", "err": "#ef4444"}
FS, CW, LH, PAD_X, HEAD = 14, 8.4, 22, 20, 40


def fmt(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def _scan(line, rules, default="text"):
    """Tokeniza uma linha com regras [(cor, regex)]; o primeiro que casar na posição vence."""
    out, i = [], 0
    while i < len(line):
        for color, rx in rules:
            m = rx.match(line, i)
            if m and m.end() > i:
                out.append((m.group(0), color))
                i = m.end()
                break
        else:
            out.append((line[i], default))
            i += 1
    merged = []
    for text, color in merged_iter(out):
        merged.append((text, color))
    return merged


def merged_iter(tokens):
    cur_t, cur_c = "", None
    for t, c in tokens:
        if c == cur_c:
            cur_t += t
        else:
            if cur_t:
                yield cur_t, cur_c
            cur_t, cur_c = t, c
    if cur_t:
        yield cur_t, cur_c


def rx(p, flags=0):
    return re.compile(p, flags)


BASH_RULES = [
    ("dim", rx(r"#.*")),
    ("str", rx(r"\"(?:\\.|[^\"\\])*\"|'[^']*'")),
    ("ph", rx(r"<[^<>\s]+>")),
    ("flag", rx(r"(?<![\w-])--?[A-Za-z][\w-]*(?:=[^\s]*)?")),
    ("ph", rx(r"\$\{?[A-Za-z_]\w*\}?")),
    ("muted", rx(r"\|\||&&|[|;<>]|\\$")),
    ("num", rx(r"(?<![\w.-])\d+(?:\.\d+)*(?![\w.-])")),
    ("text", rx(r"[\w./:=,@%+~-]+")),
]
BASH_CMD_SEP = re.compile(r"^(\s*)((?:sudo\s+)?[\w./-]+)")


def tokenize_bash(line):
    toks = _scan(line, BASH_RULES)
    # o primeiro "text" depois de início de linha ou de operador é o comando
    out, expect_cmd = [], True
    for text, color in toks:
        if text.strip() == "":
            out.append((text, color))
            continue
        if color == "muted" and text.strip() in ("|", "||", "&&", ";"):
            expect_cmd = True
        elif color == "text" and expect_cmd:
            color, expect_cmd = "cmd", False
        elif color == "dim":
            pass
        else:
            expect_cmd = False if color != "muted" else expect_cmd
        out.append((text, color))
    return list(merged_iter(out))


PY_KW = (r"def|class|return|if|elif|else|for|while|in|not|and|or|is|import|from|as|with|try|except|"
         r"finally|raise|pass|lambda|yield|async|await|None|True|False")
PY_RULES = [
    ("dim", rx(r"#.*")),
    ("str", rx(r"[rbf]?(?:\"\"\".*?\"\"\"|'''.*?'''|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')", re.S)),
    ("kw", rx(rf"\b(?:{PY_KW})\b")),
    ("fn", rx(r"[A-Za-z_]\w*(?=\()")),
    ("num", rx(r"\b\d+(?:\.\d+)?\b")),
    ("muted", rx(r"[()\[\]{}:,.=+\-*/<>!%@]")),
    ("text", rx(r"\w+")),
]

YAML_RULES = [
    ("dim", rx(r"#.*")),
    ("key", rx(r"[\w.\-/\"]+(?=:(?:\s|$))")),
    ("str", rx(r"\"(?:\\.|[^\"\\])*\"|'[^']*'")),
    ("kw", rx(r"\b(?:true|false|null|yes|no)\b")),
    ("num", rx(r"(?<![\w.-])\d+(?:\.\d+)*(?![\w.-])")),
    ("muted", rx(r"[-:\[\]{},|>]")),
    ("text", rx(r"[^\s:\[\]{},]+")),
]

JSON_RULES = [
    ("key", rx(r"\"(?:\\.|[^\"\\])*\"(?=\s*:)")),
    ("str", rx(r"\"(?:\\.|[^\"\\])*\"")),
    ("kw", rx(r"\b(?:true|false|null)\b")),
    ("num", rx(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?")),
    ("muted", rx(r"[{}\[\]:,]")),
]


TREE_LINE = re.compile(r"^([│├└─\s]*)(.*)$")


def tokenize_tree(line):
    """Árvore de diretórios: glifos apagados, pasta (termina em /) em azul, descrição após 2+ espaços."""
    m = TREE_LINE.match(line)
    glyphs, rest = m.group(1), m.group(2)
    if rest and "├" not in glyphs and "└" not in glyphs and len(glyphs) >= 12:
        return [(glyphs, "dim"), (rest, "muted")]  # continuação da descrição da linha anterior
    parts = re.split(r"(\s{2,})", rest, maxsplit=1)
    name = parts[0]
    color = "key" if name.endswith("/") else "text"
    out = [(glyphs, "dim"), (name, color)]
    if len(parts) == 3:
        out += [(parts[1], "text"), (parts[2], "muted")]
    return [t for t in out if t[0]]


def tokenize(lang, lines):
    """Devolve, por linha, a lista de (texto, cor). console decide por linha."""
    rules = {"python": PY_RULES, "py": PY_RULES, "yaml": YAML_RULES, "yml": YAML_RULES, "json": JSON_RULES}
    result = []
    for line in lines:
        if lang in ("bash", "sh", "shell", "powershell", "ps1"):
            result.append(tokenize_bash(line))
        elif lang == "tree":
            result.append(tokenize_tree(line))
        elif lang == "console":
            m = re.match(r"^(\$|>)\s+(.*)$", line)
            if m:
                result.append([(m.group(1) + " ", "dim")] + tokenize_bash(m.group(2)))
            elif line.strip().startswith("#"):
                result.append([(line, "dim")])
            else:
                low = line.lower()
                color = "err" if re.search(r"\b(error|erro|fail|falh)", low) else "ok" if re.search(r"\b(ok|done|pronto|success)\b|✓", low) else "muted"
                result.append([(line, color)])
        elif lang in rules:
            result.append(_scan(line, rules[lang]))
        else:
            result.append([(line, "text")])
    return result


def render(code, lang, title, min_width, anim):
    lines = code.rstrip("\n").expandtabs(4).split("\n")
    toks = tokenize(lang, lines)
    longest = max((len(l) for l in lines), default=1)
    width = max(min_width, int(longest * CW + 2 * PAD_X + 8))
    height = HEAD + len(lines) * LH + 22
    label = {"bash": "bash", "sh": "bash", "shell": "bash", "console": "console", "python": "python", "py": "python",
             "yaml": "yaml", "yml": "yaml", "json": "json", "tree": "tree"}.get(lang, "text")
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
         f'font-family="{MONO}" role="img" aria-label="{escape(title or label)}: {len(lines)} linhas de {label}">',
         f'<rect width="{width}" height="{height}" rx="10" fill="{C["bg"]}"/>',
         f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{C["surface"]}" stroke="{C["border"]}"/>',
         f'<path d="M0.5 {HEAD} V10.5 a10 10 0 0 1 10 -10 H{width - 10.5} a10 10 0 0 1 10 10 V{HEAD} Z" fill="{C["bg"]}"/>',
         f'<line x1="0" y1="{HEAD}" x2="{width}" y2="{HEAD}" stroke="{C["border"]}"/>']
    for i, col in enumerate((C["err"], C["flag"], C["ok"])):
        o.append(f'<circle cx="{20 + i * 18}" cy="{HEAD // 2}" r="5" fill="{col}" opacity="0.85"/>')
    if title:
        o.append(f'<text x="{width // 2}" y="{HEAD // 2 + 4}" text-anchor="middle" font-size="12" fill="{C["muted"]}">{escape(title)}</text>')
    o.append(f'<text x="{width - 16}" y="{HEAD // 2 + 4}" text-anchor="end" font-size="11" fill="{C["dim"]}">{label}</text>')
    for n, parts in enumerate(toks):
        y = HEAD + 14 + (n + 1) * LH - 6
        begin = f'<animate attributeName="opacity" to="1" begin="{fmt(0.25 + n * 0.18)}s" dur="0.3s" fill="freeze"/>' if anim else ""
        op = "0" if anim else "1"
        spans = "".join(f'<tspan fill="{C.get(c, C["text"])}">{escape(t)}</tspan>' for t, c in parts if t)
        o.append(f'<text x="{PAD_X}" y="{y}" font-size="{FS}" xml:space="preserve" opacity="{op}">{spans}{begin}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="arquivo com o código, ou - para stdin")
    ap.add_argument("out", help="arquivo .svg de saída")
    ap.add_argument("--lang", default="bash")
    ap.add_argument("--title", default="")
    ap.add_argument("--width", type=int, default=480, help="largura mínima")
    ap.add_argument("--anim", action="store_true", help="revela linha a linha (SMIL); sem a flag o cartão é estático")
    a = ap.parse_args()
    code = sys.stdin.read() if a.source == "-" else open(a.source, encoding="utf-8").read()
    svg = render(code, a.lang.lower(), a.title, a.width, a.anim)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"{a.lang}: {len(code.splitlines())} linhas -> {a.out}")


if __name__ == "__main__":
    main()
