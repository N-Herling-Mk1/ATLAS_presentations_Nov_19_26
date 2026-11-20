#!/usr/bin/env python
"""r1_spread_fig.py - draw the deck's two R1/R2 figures as inline SVG and write them into deck.src.html:
  R1STRIP : the R1-spread strip plot, top 15 vs bottom 15, endcap and barrel (slide 5)
(slide 4's box plots come from 0_qn_performers/pipeline/qp_r1r2_boxes.py, copied into assets/)

    python r1_spread_fig.py [--numbers numbers.json] [--deck deck.src.html]

Reads only numbers.json (the lists and r1_spread written by deck_numbers.py); nothing is typed by hand.
Shared log axis 0.1-100 % for both regions so the two can be compared directly.
Marks: shape + colour per group (colour alone is not enough for the near-black tau-hat-squared),
red ring = the run is shown on the per-run ROC / plane slides (top 1-4, bottom 1-5),
grey line = list range, black tick = list median, dashed red span = gap from worst top to best bottom.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re

GROUP = {  # colour, shape, label - same colours as the rest of the deck (:root --g-*)
    "DisCo alone": ("#2a78d6", "circle", "DisCo alone"),
    "+QB": ("#eb6834", "square", "+QB"),
    "+QBd": ("#eb6834", "square", "+QBd"),
    "+QDR": ("#1baf7a", "diamond", "+QDR"),
    "+tau2": ("#2b2b2b", "triangle", "+τ̂²"),
}
ACC, INK, MUTE, GRID, RANGE = "#e8230a", "#111111", "#6b6b6b", "#e6e6e6", "#a8a8a8"
W, PH = 740, 232                     # svg width, panel height
X0, X1 = 104, 724                    # plot x-range
LO, HI = -1.0, 2.0                   # log10 axis: 0.1 % .. 100 %
ROW = {"top": 66, "bottom": 152}     # row centre y inside a panel
AXIS_Y = 200
R = 4.6                              # marker half-size
SHOWN = {"top": 4, "bottom": 5}      # ranks drawn on the per-run slides


def x_of(v):
    return X0 + (X1 - X0) * (math.log10(max(v, 10 ** LO)) - LO) / (HI - LO)


def marker(shape, cx, cy, fill):
    s = R
    ring = 'stroke="#ffffff" stroke-width="1.6"'
    if shape == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s:.1f}" fill="{fill}" {ring}/>'
    if shape == "square":
        return f'<rect x="{cx - s * 0.9:.1f}" y="{cy - s * 0.9:.1f}" width="{s * 1.8:.1f}" height="{s * 1.8:.1f}" rx="1.2" fill="{fill}" {ring}/>'
    if shape == "diamond":
        d = s * 1.25
        return f'<path d="M{cx:.1f},{cy - d:.1f}L{cx + d:.1f},{cy:.1f}L{cx:.1f},{cy + d:.1f}L{cx - d:.1f},{cy:.1f}Z" fill="{fill}" {ring}/>'
    d = s * 1.3  # triangle
    return f'<path d="M{cx:.1f},{cy - d:.1f}L{cx + d * 0.95:.1f},{cy + d * 0.7:.1f}L{cx - d * 0.95:.1f},{cy + d * 0.7:.1f}Z" fill="{fill}" {ring}/>'


def swarm(xs):
    """Greedy vertical offsets so markers at close x do not overlap. Returns offsets in input order."""
    step = 6.5                       # < marker size: dense clusters overlap, separated by the white ring
    slots = [0] + [sgn * step * k for k in range(1, 8) for sgn in (-1, 1)]
    placed, off = [], [0] * len(xs)
    for i in sorted(range(len(xs)), key=lambda k: xs[k]):
        for dy in slots:
            if all(abs(xs[i] - px) >= 2 * R + 1 or dy != pdy for px, pdy in placed):
                off[i] = dy
                placed.append((xs[i], dy))
                break
    return off


def fmt(v):
    return f"{v:.2f}"


def panel(reg, o, y0):
    sp, L = o["r1_spread"], o["lists"]
    out = [f'<g transform="translate(0,{y0})">']
    info = o["info"]
    out.append(f'<text x="0" y="14" font-family="Orbitron" font-weight="700" font-size="11.5" letter-spacing="1.6" fill="{INK}">'
               f'<tspan fill="{ACC}">{reg.upper()}</tspan> · {info["n_gated"]:,} GATED RUNS · R1 OF THE TOP 15 AND BOTTOM 15</text>')
    # grid + axis
    for dec in (0.1, 1, 10, 100):
        out.append(f'<line x1="{x_of(dec):.1f}" y1="24" x2="{x_of(dec):.1f}" y2="{AXIS_Y}" stroke="{GRID}" stroke-width="1"/>')
    out.append(f'<line x1="{X0}" y1="{AXIS_Y}" x2="{X1}" y2="{AXIS_Y}" stroke="{INK}" stroke-width="1"/>')
    for t in (0.1, 0.3, 1, 3, 10, 30, 100):
        xt = x_of(t)
        out.append(f'<line x1="{xt:.1f}" y1="{AXIS_Y}" x2="{xt:.1f}" y2="{AXIS_Y + 4}" stroke="{INK}" stroke-width="1"/>'
                   f'<text x="{xt:.1f}" y="{AXIS_Y + 16}" text-anchor="middle" font-family="Share Tech Mono, monospace" font-size="11" fill="{MUTE}">{t:g}</text>')
    out.append(f'<text x="{X1}" y="{AXIS_Y + 30}" text-anchor="end" font-family="Inter, sans-serif" font-size="11" fill="{MUTE}">R1 = |band bias|, % (log scale)</text>')
    for end in ("top", "bottom"):
        y, s = ROW[end], sp[end]
        out.append(f'<text x="0" y="{y - 2}" font-family="Orbitron" font-weight="700" font-size="10.5" letter-spacing="1" fill="{INK}">{end.upper()} 15</text>'
                   f'<text x="0" y="{y + 14}" font-family="Share Tech Mono, monospace" font-size="11" fill="{MUTE}">median {fmt(s["median"])}</text>')
        out.append(f'<line x1="{x_of(s["min"]):.1f}" y1="{y}" x2="{x_of(s["max"]):.1f}" y2="{y}" stroke="{RANGE}" stroke-width="2"/>')
        xm = x_of(s["median"])
        out.append(f'<line x1="{xm:.1f}" y1="{y - 16}" x2="{xm:.1f}" y2="{y + 16}" stroke="{INK}" stroke-width="2"/>')
        xs = [x_of(abs(e["bias"])) for e in L[end]]
        offs = swarm(xs)
        for e, xv, dy in zip(L[end], xs, offs):
            col, shape, glab = GROUP.get(e["group"], ("#888888", "circle", e["group"]))
            tag = ("T" if end == "top" else "B") + str(e["rank"])
            tip = (f'{tag} · {glab} α {e["alpha"]:g} β {e["beta"]:g} · {e["block"]} s{e["seed"]} · '
                   f'R1 {fmt(abs(e["bias"]))} % (bias {e["bias"]:+.2f}) · {e["flags"]} FLAG')
            g = f'<g><title>{html.escape(tip)}</title>'
            if e["rank"] <= SHOWN[end]:
                g += f'<circle cx="{xv:.1f}" cy="{y + dy:.1f}" r="{R + 3.4:.1f}" fill="none" stroke="{ACC}" stroke-width="1.6"/>'
            g += marker(shape, xv, y + dy, col) + "</g>"
            out.append(g)
    # gap span between worst top and best bottom
    xa, xb, yg = x_of(sp["top"]["max"]), x_of(sp["bottom"]["min"]), (ROW["top"] + ROW["bottom"]) / 2
    out.append(f'<line x1="{xa:.1f}" y1="{ROW["top"]}" x2="{xa:.1f}" y2="{yg}" stroke="{ACC}" stroke-width="1" stroke-dasharray="2 2"/>'
               f'<line x1="{xb:.1f}" y1="{yg}" x2="{xb:.1f}" y2="{ROW["bottom"]}" stroke="{ACC}" stroke-width="1" stroke-dasharray="2 2"/>'
               f'<line x1="{xa:.1f}" y1="{yg}" x2="{xb:.1f}" y2="{yg}" stroke="{ACC}" stroke-width="1.6" stroke-dasharray="5 3"/>'
               f'<text x="{(xa + xb) / 2:.1f}" y="{yg - 5}" text-anchor="middle" font-family="Share Tech Mono, monospace" font-size="11.5" fill="{ACC}" stroke="#ffffff" stroke-width="3" paint-order="stroke">gap {sp["gap"]:.1f} pts</text>')
    out.append("</g>")
    return "\n".join(out)


def legend(y0):
    items, x, out = ["DisCo alone", "+QB", "+QDR", "+tau2"], 0, [f'<g transform="translate(0,{y0})" font-family="Inter, sans-serif" font-size="12" fill="{MUTE}">']
    for k in items:
        col, shape, lab = GROUP[k]
        out.append(marker(shape, x + 6, 0, col) + f'<text x="{x + 16}" y="4">{lab}</text>')
        x += 30 + 7.2 * len(lab)
    out.append(f'<circle cx="{x + 8}" cy="0" r="{R + 3.4:.1f}" fill="none" stroke="{ACC}" stroke-width="1.6"/>'
               f'<text x="{x + 22}" y="4">shown on the ROC / plane slides</text>')
    x += 230
    out.append(f'<line x1="{x}" y1="0" x2="{x + 16}" y2="0" stroke="{RANGE}" stroke-width="2"/><text x="{x + 22}" y="4">range</text>')
    x += 70
    out.append(f'<line x1="{x + 4}" y1="-8" x2="{x + 4}" y2="8" stroke="{INK}" stroke-width="2"/><text x="{x + 12}" y="4">median</text>')
    out.append("</g>")
    return "\n".join(out)


def build(numbers):
    regs = [r for r in ("endcap", "barrel") if r in numbers["regions"]]
    h = len(regs) * (PH + 8) + 22
    parts = [f'<svg class="r1strip" viewBox="0 0 {W} {h}" width="{W}" height="{h}" xmlns="http://www.w3.org/2000/svg" role="img" '
             f'aria-label="R1 of the top 15 and bottom 15 runs per region on a shared log axis">']
    for i, r in enumerate(regs):
        parts.append(panel(r, numbers["regions"][r], i * (PH + 8)))
    parts.append(legend(h - 10))
    parts.append("</svg>")
    return "\n".join(parts)


def write_block(src, name, svg):
    pat = re.compile(r"(<!-- " + name + r":BEGIN[^>]*-->)(.*?)(<!-- " + name + r":END -->)", re.S)
    if not pat.search(src):
        return src, False
    return pat.sub(lambda m: m.group(1) + "\n" + svg + "\n" + m.group(3), src), True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--numbers", default="numbers.json")
    ap.add_argument("--deck", default="deck.src.html")
    a = ap.parse_args()
    print(f"[1/3] reading {a.numbers}")
    numbers = json.load(open(a.numbers, encoding="utf-8"))
    if "r1_spread" not in next(iter(numbers["regions"].values())):
        raise SystemExit("numbers.json has no r1_spread: run  python deck_numbers.py --spread-only numbers.json  first")
    print("[2/3] drawing the R1 strip plot")
    src = open(a.deck, encoding="utf-8").read()
    src, ok = write_block(src, "R1STRIP", build(numbers))
    if not ok:
        raise SystemExit(f"no R1STRIP markers in {a.deck}")
    open(a.deck, "w", encoding="utf-8").write(src)
    print(f"[3/3] wrote R1STRIP into {a.deck}")


if __name__ == "__main__":
    main()
