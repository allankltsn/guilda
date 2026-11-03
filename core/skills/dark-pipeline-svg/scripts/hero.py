#!/usr/bin/env python3
"""Gera banners de título de projeto (hero) em SVG animado (SMIL). Só biblioteca padrão.

Uso:
  python hero.py projeto.json saida.svg [--html]

Layout: à esquerda título, subtítulo e pills da stack; à direita um painel criativo
cujo tipo muda conforme o projeto: terminal, editor, pipeline, metrics, architecture, custom.
Veja SKILL.md (seção 13) e examples/hero-*.json para o formato de cada painel.
"""
import argparse
import json
import sys
from xml.sax.saxutils import escape

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
DEFAULT = {"bg": "#0b0f17", "surface": "#111827", "border": "#1f2937", "text": "#e6edf3", "muted": "#8b96a8",
           "dim": "#4b5563", "accent": "#2dd4bf", "accent2": "#60a5fa", "ok": "#4ade80", "warn": "#f59e0b", "err": "#ef4444"}


def fmt(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def appear(t, dur=0.3):
    return f'<animate attributeName="opacity" to="1" begin="{fmt(t)}s" dur="{dur}s" fill="freeze"/>'


class Ctx:
    def __init__(self, pal):
        self.p = pal
        self.n = 0

    def uid(self, prefix):
        self.n += 1
        return f"{prefix}{self.n}"


def window(c, x, y, w, h, title, chrome=True):
    p = c.p
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{p["surface"]}" stroke="{p["border"]}"/>']
    if chrome:
        for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
            out.append(f'<circle cx="{x + 20 + i * 16}" cy="{y + 20}" r="5" fill="{col}"/>')
        out.append(f'<text x="{x + w - 16}" y="{y + 24}" font-family="{MONO}" font-size="11.5" fill="{p["muted"]}" text-anchor="end">{escape(title)}</text>')
    else:
        out.append(f'<text x="{x + 18}" y="{y + 24}" font-family="{MONO}" font-size="11.5" fill="{p["muted"]}">{escape(title)}</text>')
    return out


def typed(c, x, y, content, size, t, chars_w=0.6):
    fill = c.p["text"]
    """Texto revelado da esquerda para a direita (efeito de digitação)."""
    cid = c.uid("ty")
    plain = "".join(seg[0] if isinstance(seg, list) else seg for seg in content)
    w = len(plain) * size * chars_w + 4
    dur = max(0.3, len(plain) * 0.03)
    spans = "".join(f'<tspan fill="{s[1]}">{escape(s[0])}</tspan>' if isinstance(s, list) else escape(s) for s in content)
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y - size - 2}" width="0" height="{size * 1.6}">'
            f'<animate attributeName="width" to="{fmt(w)}" begin="{fmt(t)}s" dur="{fmt(dur)}s" fill="freeze"/></rect></clipPath>'
            f'<g clip-path="url(#{cid})"><text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{fill}" xml:space="preserve" style="white-space:pre">{spans}</text></g>'), t + dur


def panel_terminal(c, x, y, w, h, spec):
    p = c.p
    out = window(c, x, y, w, h, spec.get("title", "terminal"))
    t, ly = 1.0, y + 52
    colors = {"out": p["muted"], "ok": p["ok"], "err": p["err"], "warn": p["warn"]}
    for line in spec["lines"]:
        if ly > y + h - 14:
            print("aviso: terminal com linhas demais, o excedente foi cortado", file=sys.stderr)
            break
        if "cmd" in line:
            svg, end = typed(c, x + 20, ly, [[ "$ ", p["muted"] ], [line["cmd"], p["text"]]], 12.5, t)
            out.append(svg)
            t = end + 0.3
        else:
            kind = next(k for k in colors if k in line)
            out.append(f'<text x="{x + 20}" y="{ly}" font-family="{MONO}" font-size="12.5" fill="{colors[kind]}" opacity="0">  {escape(line[kind])}{appear(t, 0.2)}</text>')
            t += 0.5
        ly += 22
    out.append(f'<rect x="{x + 20}" y="{ly - 12}" width="8" height="14" fill="{p["accent"]}" opacity="0"><animate attributeName="opacity" values="0;1;0" begin="{fmt(t)}s" dur="1s" repeatCount="indefinite"/></rect>')
    return out


def panel_editor(c, x, y, w, h, spec):
    p = c.p
    roles = {"kw": p["accent2"], "fn": p["accent"], "str": p["ok"], "num": p["warn"], "com": p["dim"], "err": p["err"]}
    out = window(c, x, y, w, h, spec.get("title", "main"))
    t, ly = 1.0, y + 52
    for n, line in enumerate(spec["lines"], 1):
        if ly > y + h - 12:
            print("aviso: editor com linhas demais, o excedente foi cortado", file=sys.stderr)
            break
        segs = [line] if isinstance(line, str) else [[s[0], roles.get(s[1], p["text"])] if isinstance(s, list) else s for s in line]
        out.append(f'<text x="{x + 20}" y="{ly}" font-family="{MONO}" font-size="12" fill="{p["dim"]}">{n}</text>')
        svg, end = typed(c, x + 44, ly, segs, 12, t)
        out.append(svg)
        t = end + 0.1
        ly += 20
    out.append(f'<rect x="{x + 44}" y="{ly - 14}" width="7" height="14" fill="{p["accent"]}" opacity="0"><animate attributeName="opacity" values="0;1;0" begin="{fmt(t)}s" dur="1s" repeatCount="indefinite"/></rect>')
    return out


def panel_pipeline(c, x, y, w, h, spec):
    p = c.p
    out = window(c, x, y, w, h, spec.get("title", "pipeline"), chrome=False)
    stages = spec["stages"]
    step = min(34, (h - 60) / max(len(stages), 1))
    col = {"ok": p["ok"], "run": p["accent"], "fail": p["err"], "pending": p["dim"]}
    cx, top = x + 30, y + 52
    out.append(f'<line x1="{cx}" y1="{fmt(top)}" x2="{cx}" y2="{fmt(top + step * (len(stages) - 1))}" stroke="{p["border"]}" stroke-width="2"/>')
    for n, st in enumerate(stages):
        cy = top + n * step
        s = st.get("status", "pending")
        k = col[s]
        t = 0.8 + n * 0.35
        g = [f'<g opacity="0">{appear(t)}']
        g.append(f'<circle cx="{cx}" cy="{fmt(cy)}" r="8" fill="{p["surface"]}" stroke="{k}" stroke-width="2">'
                 + (f'<animate attributeName="stroke-opacity" values="0.3;1;0.3" dur="1.6s" repeatCount="indefinite"/>' if s == "run" else "") + '</circle>')
        if s == "ok":
            g.append(f'<path d="M{cx - 3.5},{fmt(cy)} l2.5,2.8 l4.5,-5.5" fill="none" stroke="{k}" stroke-width="1.8" stroke-linecap="round"/>')
        elif s == "fail":
            g.append(f'<path d="M{cx - 3},{fmt(cy - 3)} l6,6 m0,-6 l-6,6" stroke="{k}" stroke-width="1.8" stroke-linecap="round"/>')
        elif s == "run":
            g.append(f'<circle cx="{cx}" cy="{fmt(cy)}" r="3" fill="{k}"/>')
        g.append(f'<text x="{cx + 20}" y="{fmt(cy + 4)}" font-family="{MONO}" font-size="12.5" fill="{p["text"] if s != "pending" else p["muted"]}">{escape(st["label"])}</text>')
        if st.get("detail"):
            g.append(f'<text x="{x + w - 18}" y="{fmt(cy + 4)}" font-family="{MONO}" font-size="11.5" fill="{k}" text-anchor="end">{escape(st["detail"])}</text>')
        g.append("</g>")
        out.append("".join(g))
    if len(stages) > 1:
        out.append(f'<circle cx="{cx}" r="3" fill="{p["accent"]}" opacity="0.9"><animate attributeName="cy" values="{fmt(top)};{fmt(top + step * (len(stages) - 1))}" dur="2.4s" repeatCount="indefinite"/>'
                   f'<animate attributeName="opacity" values="0;1;1;0" dur="2.4s" repeatCount="indefinite"/></circle>')
    return out


def panel_metrics(c, x, y, w, h, spec):
    p = c.p
    out = window(c, x, y, w, h, spec.get("title", "metrics"), chrome=False)
    kpis = spec.get("kpis", [])[:3]
    kw = (w - 36 - (len(kpis) - 1) * 8) / max(len(kpis), 1)
    for n, k in enumerate(kpis):
        kx = x + 18 + n * (kw + 8)
        out.append(f'<g opacity="0">{appear(0.8 + n * 0.2)}<rect x="{fmt(kx)}" y="{y + 40}" width="{fmt(kw)}" height="46" rx="8" fill="none" stroke="{p["border"]}"/>'
                   f'<text x="{fmt(kx + 10)}" y="{y + 62}" font-size="18" font-weight="700" fill="{k.get("color", p["accent"])}">{escape(k["value"])}</text>'
                   f'<text x="{fmt(kx + 10)}" y="{y + 78}" font-family="{MONO}" font-size="10" fill="{p["muted"]}">{escape(k["label"])}</text></g>')
    values = spec.get("series", [])
    if values:
        base, area_h = y + h - 18, h - 130 if kpis else h - 70
        area_h = max(area_h, 30)
        bw = (w - 36) / len(values)
        mx = max(values) or 1
        for n, v in enumerate(values):
            bh = area_h * v / mx
            col = spec.get("series_color", p["accent"])
            out.append(f'<rect x="{fmt(x + 18 + n * bw + bw * 0.15)}" y="{fmt(base)}" width="{fmt(bw * 0.7)}" height="0" rx="2" fill="{col}" fill-opacity="{fmt(0.35 + 0.65 * v / mx)}">'
                       f'<animate attributeName="height" to="{fmt(bh)}" begin="{fmt(1.2 + n * 0.06)}s" dur="0.5s" fill="freeze"/>'
                       f'<animate attributeName="y" to="{fmt(base - bh)}" begin="{fmt(1.2 + n * 0.06)}s" dur="0.5s" fill="freeze"/></rect>')
    return out


def panel_architecture(c, x, y, w, h, spec):
    p = c.p
    out = window(c, x, y, w, h, spec.get("title", "arquitetura"), chrome=False)
    nodes = spec["nodes"]
    cols = min(3, len(nodes))
    rows = -(-len(nodes) // cols)
    nw, nh = 88, 34
    area_y = y + 40
    pos = []
    for n in range(len(nodes)):
        r, k = divmod(n, cols)
        in_row = min(cols, len(nodes) - r * cols)
        px = x + (w - 36) * (k + 0.5) / in_row + 18
        py = area_y + (h - 56) * (r + 0.5) / rows
        pos.append((px, py))
    for n, (a, b) in enumerate(spec.get("edges", [])):
        (x1, y1), (x2, y2) = pos[a], pos[b]
        pid = c.uid("e")
        out.append(f'<path id="{pid}" d="M{fmt(x1)},{fmt(y1)} L{fmt(x2)},{fmt(y2)}" stroke="{p["border"]}" stroke-width="1.5" stroke-dasharray="4 3" fill="none"/>'
                   f'<circle r="3.5" fill="{p["accent"]}"><animateMotion dur="{fmt(1.8 + 0.4 * n)}s" repeatCount="indefinite"><mpath href="#{pid}"/></animateMotion>'
                   f'<animate attributeName="opacity" values="0;1;1;0" dur="{fmt(1.8 + 0.4 * n)}s" repeatCount="indefinite"/></circle>')
    for n, node in enumerate(nodes):
        px, py = pos[n]
        k = node.get("color", p["accent"])
        out.append(f'<g opacity="0">{appear(0.6 + n * 0.2)}<rect x="{fmt(px - nw / 2)}" y="{fmt(py - nh / 2)}" width="{nw}" height="{nh}" rx="8" fill="{p["surface"]}" stroke="{k}">'
                   + (f'<animate attributeName="stroke-opacity" values="0.4;1;0.4" dur="2.5s" repeatCount="indefinite"/>' if node.get("active") else "")
                   + f'</rect><text x="{fmt(px)}" y="{fmt(py + 4)}" text-anchor="middle" font-family="{MONO}" font-size="11.5" fill="{p["text"]}">{escape(node["label"])}</text></g>')
    return out


def panel_custom(c, x, y, w, h, spec):
    return [f'<g transform="translate({x},{y})">{spec["svg"]}</g>']


PANELS = {"terminal": panel_terminal, "editor": panel_editor, "pipeline": panel_pipeline,
          "metrics": panel_metrics, "architecture": panel_architecture, "custom": panel_custom}


def hero(spec):
    pal = {**DEFAULT, **spec.get("palette", {})}
    c = Ctx(pal)
    w = spec.get("width", 1200)
    h = spec.get("height", 300)
    panel = spec.get("panel")
    pw = (panel or {}).get("width", 336) if panel else 0
    px = w - 36 - pw
    avail = (px - 36 if panel else w - 72) - 72
    # pills (quebram de linha quando passam da largura disponível)
    pills, cx, row = [], 72, 0
    for n, s in enumerate(spec.get("stack", [])):
        label, color = (s, None) if isinstance(s, str) else (s["label"], s.get("color"))
        bw = len(label) * 7.6 + 28 + (12 if color else 0)
        if cx + bw > 72 + avail and cx > 72:
            cx, row = 72, row + 1
        y = 204 + row * 34
        dot = f'<circle cx="{fmt(cx + 15)}" cy="{y + 13}" r="3.5" fill="{color}"/>' if color else ""
        off = 6 if color else 0
        pills.append(f'<g opacity="0">{appear(2.1 + n * 0.2, 0.4)}<rect x="{cx}" y="{y}" width="{fmt(bw)}" height="26" rx="13" fill="none" stroke="{color or pal["border"]}" stroke-opacity="{0.6 if color else 1}"/>{dot}'
                     f'<text x="{fmt(cx + bw / 2 + off)}" y="{y + 17}" text-anchor="middle">{escape(label)}</text></g>')
        cx += bw + 10
    h = max(h, 204 + row * 34 + 26 + 40)
    # subtítulo
    tag = spec.get("tagline", [])
    parts = [{"text": t} if isinstance(t, str) else t for t in tag]
    chars = sum(len(t["text"]) + 1 for t in parts)
    fs = min(24, avail / max(chars * 0.52, 1))
    spans = " ".join(f'<tspan fill="{pal["accent"]}" font-weight="600">{escape(t["text"])}</tspan>' if t.get("accent") else f'<tspan>{escape(t["text"])}</tspan>' for t in parts)
    title = spec["title"]
    tfs = min(56, avail / max(len(title) * 0.56, 1))
    body = [
        f'<defs><clipPath id="tag"><rect x="72" y="{176 - 30}" width="0" height="40"><animate attributeName="width" to="{fmt(avail)}" begin="1.0s" dur="1.0s" fill="freeze" calcMode="spline" keySplines="0.2 0 0.2 1"/></rect></clipPath>'
        f'<linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{pal["accent"]}"/><stop offset="1" stop-color="{pal["accent2"]}"/></linearGradient></defs>',
        f'<rect width="{w}" height="{h}" fill="{pal["bg"]}"/>',
        f'<g stroke="{pal["border"]}" stroke-width="1" opacity="0.6"><path d="M0 {h - 60} H{w}"/><path d="M0 60 H{w}"/></g>',
        f'<rect x="72" y="60" width="0" height="4" rx="2" fill="url(#g)"><animate attributeName="width" to="120" begin="0.2s" dur="0.6s" fill="freeze"/></rect>',
        f'<text x="72" y="118" font-size="{fmt(tfs)}" font-weight="700" fill="{pal["text"]}" letter-spacing="-1" opacity="0">{escape(title)}{appear(0.4, 0.5)}</text>',
        f'<g clip-path="url(#tag)"><text x="72" y="176" font-size="{fmt(fs)}" fill="{pal["muted"]}">{spans}</text></g>',
        f'<g font-family="{MONO}" font-size="12.5" fill="{pal["muted"]}">{"".join(pills)}</g>',
    ]
    if panel:
        py, ph = 52, h - 104
        inner = PANELS[panel["type"]](c, px, py, pw, ph, panel)
        body.append(f'<g opacity="0">{appear(0.6, 0.5)}{"".join(inner)}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}" role="img" aria-label="{escape(title)}">\n'
            + "\n".join(body) + "\n</svg>\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("--html", action="store_true")
    a = ap.parse_args()
    with open(a.data, encoding="utf-8") as f:
        spec = json.load(f)
    svg = hero(spec)
    if a.html:
        svg = ('<!doctype html>\n<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>{escape(spec["title"])}</title><style>:root{{color-scheme:dark}}body{{margin:0;background:{spec.get("palette", {}).get("bg", DEFAULT["bg"])};'
               'display:flex;justify-content:center;padding:40px 16px}svg{width:100%;max-width:1200px;height:auto}</style></head><body>\n' + svg + "</body></html>\n")
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"hero ({(spec.get('panel') or {}).get('type', 'sem painel')}) -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
