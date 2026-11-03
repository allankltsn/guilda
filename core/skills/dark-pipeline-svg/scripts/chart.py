#!/usr/bin/env python3
"""Gera gráficos SVG animados (SMIL) no tema dark pipeline. Só biblioteca padrão.

Uso:
  python chart.py dados.json saida.svg [--type stacked|bars|donut] [--html]

dados.json:
  {"title": "Top linguagens", "type": "stacked", "width": 400, "bg": "transparent",
   "unit": "%", "mode": "share",
   "items": [{"label": "Python", "value": 55, "color": "#3b82f6"}, ...]}

mode "share" (padrão): percentual = valor / soma, mostrado com 2 casas.
mode "absolute": barras proporcionais a "max" (padrão 100), valor mostrado como está.
Qualquer quantidade de itens; cor ausente usa a paleta do design system.
"""
import argparse
import json
import math
import sys
from xml.sax.saxutils import escape

PALETTE = ["#3b82f6", "#2dd4bf", "#f59e0b", "#4ade80", "#a78bfa", "#f472b6", "#ef4444"]
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"


def fmt(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def prepare(data):
    items = data["items"]
    if not items:
        raise SystemExit("items vazio")
    mode = data.get("mode", "share")
    total = sum(i["value"] for i in items) or 1
    out = []
    for n, i in enumerate(items):
        share = i["value"] / total * 100
        out.append({
            "label": i["label"],
            "color": i.get("color", PALETTE[n % len(PALETTE)]),
            "share": share,
            "ratio": (i["value"] / data.get("max", 100)) if mode == "absolute" else share / 100,
            "shown": f"{fmt(i['value'])}{data.get('unit', '')}" if mode == "absolute" else f"{share:.2f}%",
        })
    return out


def frame(data, w, h, body):
    bg = data.get("bg", "#0b0f17")
    text = data.get("text", "#e6edf3")
    title = data.get("title", "")
    rect = "" if bg == "transparent" else f'<rect width="{w}" height="{h}" rx="6" fill="{bg}" stroke="#1f2937"/>'
    head = f'<text x="25" y="35" font-size="18" font-weight="600" fill="{data.get("title_color", "#2dd4bf")}">{escape(title)}</text>' if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}" role="img" aria-label="{escape(title)}">\n'
            f'<style>.t{{fill:{text};font-size:12px}}.v{{fill:#8b96a8;font-size:12px;font-family:{MONO}}}</style>\n'
            f'{rect}\n{head}\n{body}\n</svg>\n')


def stacked(data, items):
    w = data.get("width", 400)
    bar_x, bar_w, bar_h = 25, w - 50, 8
    y0 = 55 if data.get("title") else 25
    cols = 2
    rows = math.ceil(len(items) / cols)
    h = y0 + bar_h + 25 + rows * 25 + 10
    parts = [f'<defs><clipPath id="bar"><rect x="{bar_x}" y="{y0}" width="{bar_w}" height="{bar_h}" rx="4"/></clipPath></defs>',
             f'<rect x="{bar_x}" y="{y0}" width="{bar_w}" height="{bar_h}" rx="4" fill="#1f2937"/>', '<g clip-path="url(#bar)">']
    x = bar_x
    for n, i in enumerate(items):
        sw = bar_w * i["share"] / 100
        parts.append(f'<rect x="{fmt(x)}" y="{y0}" width="0" height="{bar_h}" fill="{i["color"]}">'
                     f'<animate attributeName="width" to="{fmt(sw + 0.5)}" begin="{fmt(0.2 + n * 0.15)}s" dur="0.6s" fill="freeze"/></rect>')
        x += sw
    parts.append("</g>")
    col_w = bar_w / cols
    for n, i in enumerate(items):
        cx = bar_x + (n % cols) * col_w
        cy = y0 + bar_h + 30 + (n // cols) * 25
        parts.append(f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{fmt(0.4 + n * 0.1)}s" dur="0.4s" fill="freeze"/>'
                     f'<circle cx="{fmt(cx + 5)}" cy="{cy - 4}" r="5" fill="{i["color"]}"/>'
                     f'<text class="t" x="{fmt(cx + 15)}" y="{cy}">{escape(i["label"])}:'
                     f'<tspan class="v" dx="6">{i["shown"]}</tspan></text></g>')
    return frame(data, w, h, "\n".join(parts))


def bars(data, items):
    w = data.get("width", 480)
    y0 = 55 if data.get("title") else 20
    label_w, val_w, row = 110, 70, 30
    track_x, track_w = 25 + label_w, w - 50 - label_w - val_w
    h = y0 + len(items) * row + 15
    parts = []
    for n, i in enumerate(items):
        y = y0 + n * row
        fw = max(track_w * min(i["ratio"], 1), 0)
        parts.append(f'<text class="t" x="25" y="{y + 12}">{escape(i["label"])}</text>'
                     f'<rect x="{track_x}" y="{y + 3}" width="{fmt(track_w)}" height="10" rx="5" fill="#1f2937"/>'
                     f'<rect x="{track_x}" y="{y + 3}" width="0" height="10" rx="5" fill="{i["color"]}">'
                     f'<animate attributeName="width" to="{fmt(fw)}" begin="{fmt(0.2 + n * 0.12)}s" dur="0.7s" fill="freeze"/></rect>'
                     f'<text class="v" x="{w - 25}" y="{y + 12}" text-anchor="end" opacity="0">{i["shown"]}'
                     f'<animate attributeName="opacity" to="1" begin="{fmt(0.5 + n * 0.12)}s" dur="0.4s" fill="freeze"/></text>')
    return frame(data, w, h, "\n".join(parts))


def donut(data, items):
    w = data.get("width", 460)
    y0 = 55 if data.get("title") else 20
    r, sw = 60, 22
    size = 2 * (r + sw)
    cx, cy = 25 + r + sw, y0 + r + sw
    h = max(y0 + size + 20, y0 + len(items) * 25 + 20)
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1f2937" stroke-width="{sw}"/>']
    cum = 0.0
    for n, i in enumerate(items):
        ln = i["share"]
        seg = max(ln - 0.4, 0)
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{i["color"]}" stroke-width="{sw}" pathLength="100" '
                     f'stroke-dasharray="0 100" stroke-dashoffset="{fmt(-cum)}" transform="rotate(-90 {cx} {cy})">'
                     f'<animate attributeName="stroke-dasharray" to="{fmt(seg)} {fmt(100 - seg)}" '
                     f'begin="{fmt(0.2 + n * 0.25)}s" dur="0.6s" fill="freeze"/></circle>')
        cum += ln
    lx = 25 + size + 30
    for n, i in enumerate(items):
        y = y0 + 16 + n * 25
        parts.append(f'<g opacity="0"><animate attributeName="opacity" to="1" begin="{fmt(0.4 + n * 0.15)}s" dur="0.4s" fill="freeze"/>'
                     f'<circle cx="{lx + 5}" cy="{y - 4}" r="5" fill="{i["color"]}"/>'
                     f'<text class="t" x="{lx + 15}" y="{y}">{escape(i["label"])}:<tspan class="v" dx="6">{i["shown"]}</tspan></text></g>')
    return frame(data, w, h, "\n".join(parts))


BUILDERS = {"stacked": stacked, "bars": bars, "donut": donut}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data")
    ap.add_argument("out")
    ap.add_argument("--type", choices=BUILDERS)
    ap.add_argument("--html", action="store_true", help="embrulha o SVG numa página HTML escura")
    a = ap.parse_args()
    with open(a.data, encoding="utf-8") as f:
        data = json.load(f)
    kind = a.type or data.get("type", "stacked")
    svg = BUILDERS[kind](data, prepare(data))
    if a.html:
        svg = ('<!doctype html>\n<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>{escape(data.get("title", "Gráfico"))}</title><style>:root{{color-scheme:dark}}body{{margin:0;background:#0b0f17;display:flex;'
               'justify-content:center;padding:40px 16px}svg{max-width:100%;height:auto}</style></head><body>\n' + svg + "</body></html>\n")
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"{kind}: {len(data['items'])} itens -> {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
