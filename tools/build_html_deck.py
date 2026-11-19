#!/usr/bin/env python3
"""Build a deck written as live HTML (source/<NN_name>/deck.src.html) into this repo's player format.

  python tools/build_html_deck.py source/01_unknot_overview            # build + install into decks/<id>/
  python tools/build_html_deck.py source/01_unknot_overview --no-install  # build only, into build/<id>/

A source folder holds:
  deck.src.html   the deck: 1280x720 <section class="slide"> pages, TeX math in \\( \\) and \\[ \\]
  meta.json       id, stem, title, subtitle, author, date, description, tags, notes (one per slide)
  assets/         images the deck references by relative path (inlined at build time)

What comes out (in build/<id>/, then installed by tools/deck_tool.py):
  <stem>_single_file.html   the live deck, fully self-contained: fonts inlined, images inlined, math pre-rendered
                            to SVG. No network needed; arrow keys to move.
  slides/s-NN.png           1920x1080 renders, one per slide (the repo player shows these)
  <stem>.pdf                vector PDF printed from the HTML, one slide per page
  <stem>.pptx               one full-slide image per slide + speaker notes from meta.json

Needs: pip install playwright pillow python-pptx  &&  python -m playwright install chromium
MathJax (tools/vendor/tex-svg-full.js) and the fonts (tools/vendor/fonts/) are vendored, so nothing is fetched.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "tools" / "vendor"
FONTS = [  # (family, weight, file)
    ("Orbitron", 700, "orbitron-latin-700-normal.woff2"),
    ("Orbitron", 900, "orbitron-latin-900-normal.woff2"),
    ("Inter", 400, "inter-latin-400-normal.woff2"),
    ("Inter", 600, "inter-latin-600-normal.woff2"),
    ("Share Tech Mono", 400, "share-tech-mono-latin-400-normal.woff2"),
]
MIME = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml"}
T0 = time.time()


# ---------------------------------------------------------------- progress
def step(i: int, n: int, msg: str) -> None:
    print(f"\n[{i}/{n}] {msg}  (+{time.time() - T0:.1f}s)", flush=True)


def bar(done: int, total: int, label: str = "") -> None:
    w = 28
    f = int(w * done / max(total, 1))
    end = "\n" if done >= total else ""
    print(f"\r      [{'#' * f}{'.' * (w - f)}] {done}/{total} {label}", end=end, flush=True)


def info(msg: str) -> None:
    print(f"      {msg}", flush=True)


def die(msg: str) -> None:
    print(f"\nERROR: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------- inlining
def b64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode("ascii")


def font_css() -> str:
    rules = []
    for fam, wt, fn in FONTS:
        p = VENDOR / "fonts" / fn
        if not p.exists():
            die(f"missing vendored font {p}")
        rules.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{wt};font-display:block;"
                     f"src:url(data:font/woff2;base64,{b64(p)}) format('woff2')}}")
    return "<style id=\"inlined-fonts\">\n" + "\n".join(rules) + "\n</style>"


def inline_images(html: str, src_dir: Path) -> tuple[str, int]:
    count = 0

    def sub(m: re.Match) -> str:
        nonlocal count
        rel = m.group(2)
        if rel.startswith(("data:", "http:", "https:", "//")):
            return m.group(0)
        p = (src_dir / rel).resolve()
        if not p.exists():
            die(f"image not found: {rel}")
        count += 1
        return f'{m.group(1)}"data:{MIME.get(p.suffix.lower(), "application/octet-stream")};base64,{b64(p)}"'

    return re.sub(r'(\bsrc=)"([^"]+)"', sub, html), count


# ---------------------------------------------------------------- build
def build(src_dir: Path, out: Path, meta: dict) -> dict:
    from playwright.sync_api import sync_playwright

    N = 6
    stem = meta["stem"]
    step(1, N, f"Reading {src_dir.name}/deck.src.html")
    html = (src_dir / "deck.src.html").read_text(encoding="utf-8")
    if "<!-- BUILD:HEAD" not in html:
        die("deck.src.html has no <!-- BUILD:HEAD --> marker in <head>")
    html, n_img = inline_images(html, src_dir)
    info(f"{n_img} image(s) inlined")
    html = re.sub(r"<!-- BUILD:HEAD.*?-->", lambda _m: font_css(), html, count=1, flags=re.S)
    info(f"{len(FONTS)} font faces inlined")

    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "_typeset.html"
    loader = f'<script id="mj-loader" src="{(VENDOR / "tex-svg-full.js").as_uri()}"></script>'
    tmp.write_text(html.replace("</head>", loader + "\n</head>", 1), encoding="utf-8")

    single = out / f"{stem}_single_file.html"
    slides_dir = out / "slides"
    if slides_dir.exists():
        shutil.rmtree(slides_dir)
    slides_dir.mkdir()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            step(2, N, "Typesetting math (MathJax -> inline SVG)")
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(tmp.as_uri())
            page.wait_for_function("window.MathJax && MathJax.startup && MathJax.startup.promise", timeout=30000)
            page.evaluate("MathJax.startup.promise")
            n_math = page.evaluate("document.querySelectorAll('mjx-container').length")
            errs = page.evaluate("document.querySelectorAll('mjx-merror, [data-mjx-error]').length")
            info(f"{n_math} formulas typeset" + (f", {errs} TeX ERRORS" if errs else ""))
            if errs:
                die("MathJax reported TeX errors; fix the source")
            page.evaluate("""() => {
                for (const s of [...document.querySelectorAll('script')])
                    if (s.id === 'mj-loader' || /window\\.MathJax\\s*=/.test(s.textContent)) s.remove();
                document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
            }""")
            body = "<!DOCTYPE html>\n" + page.evaluate("document.documentElement.outerHTML")
            single.write_text(body, encoding="utf-8")
            page.close()
            tmp.unlink()
            info(f"{single.name}  ({single.stat().st_size / 1048576:.2f} MB, no network needed)")

            step(3, N, "Rendering slide images (1920x1080)")
            page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1.5)
            page.goto(single.as_uri())
            page.evaluate("document.fonts.ready")
            page.evaluate("document.body.classList.add('render'); window.deckFit()")
            n = page.evaluate("document.querySelectorAll('.slide').length")
            if n != len(meta.get("notes", [])):
                info(f"WARNING: {n} slides but {len(meta.get('notes', []))} notes in meta.json")
            pngs = []
            for i in range(n):
                page.evaluate(f"window.deckShow({i})")
                page.wait_for_timeout(120)
                p = slides_dir / f"s-{i + 1:02d}.png"
                page.screenshot(path=str(p), clip={"x": 0, "y": 0, "width": 1280, "height": 720})
                pngs.append(p)
                bar(i + 1, n, "slides")
            links = page.evaluate("""() => [...document.querySelectorAll('.slide')].map(s => {
                s.classList.add('active');
                const r = s.getBoundingClientRect();
                const out = [...s.querySelectorAll('a[href]')].map(a => { const q = a.getBoundingClientRect();
                    return {href: a.getAttribute('href'), text: a.textContent.trim().slice(0, 80),
                            x: +((q.left - r.left) / r.width).toFixed(4), y: +((q.top - r.top) / r.height).toFixed(4),
                            w: +(q.width / r.width).toFixed(4), h: +(q.height / r.height).toFixed(4)}; })
                    .filter(l => l.w > 0 && l.h > 0);
                s.classList.remove('active'); return out; })""")
            (out / "links.json").write_text(json.dumps(links, indent=1), encoding="utf-8")
            info(f"{sum(len(l) for l in links)} link(s) found; they stay clickable in the player, PDF and PPTX")
            overflow = page.evaluate("""() => [...document.querySelectorAll('.slide')].map((s, i) => {
                s.classList.add('active');
                const r = s.getBoundingClientRect(); let bad = 0;
                s.querySelectorAll('*').forEach(e => { const q = e.getBoundingClientRect();
                    if (q.width && (q.right > r.right + 1 || q.bottom > r.bottom + 1)) bad++; });
                s.classList.remove('active'); return bad; })""")
            for i, b in enumerate(overflow, 1):
                if b:
                    info(f"WARNING: slide {i}: {b} element(s) extend past the 1280x720 frame")
            page.close()

            step(4, N, "Printing vector PDF")
            page = browser.new_page()
            page.goto(single.as_uri())
            page.evaluate("document.fonts.ready")
            pdf = out / f"{stem}.pdf"
            page.pdf(path=str(pdf), width="1280px", height="720px", print_background=True,
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            page.close()
            info(f"{pdf.name}  ({pdf.stat().st_size / 1048576:.2f} MB)")
        finally:
            browser.close()

    step(5, N, "Building PPTX (slide images + speaker notes)")
    from pptx import Presentation
    from pptx.util import Emu
    pres = Presentation()
    pres.slide_width, pres.slide_height = Emu(12192000), Emu(6858000)
    pres.core_properties.title = meta["title"]
    pres.core_properties.author = meta.get("author", "")
    notes = meta.get("notes", [])
    links = json.loads((out / "links.json").read_text(encoding="utf-8"))
    from pptx.enum.shapes import MSO_SHAPE
    for i, p in enumerate(pngs):
        s = pres.slides.add_slide(pres.slide_layouts[6])
        s.shapes.add_picture(str(p), 0, 0, width=pres.slide_width, height=pres.slide_height)
        for l in (links[i] if i < len(links) else []):                # transparent click box over each link
            W, H = pres.slide_width, pres.slide_height
            box = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, int(l["x"] * W), int(l["y"] * H), int(l["w"] * W), int(l["h"] * H))
            box.fill.background(); box.line.fill.background(); box.shadow.inherit = False
            box.click_action.hyperlink.address = l["href"]
        if i < len(notes) and notes[i]:
            s.notes_slide.notes_text_frame.text = notes[i]
        bar(i + 1, len(pngs), "PPTX slides")
    pptx = out / f"{stem}.pptx"
    pres.save(str(pptx))
    info(f"{pptx.name}  ({pptx.stat().st_size / 1048576:.2f} MB)")
    return {"slides": len(pngs)}


def install(out: Path, meta: dict) -> None:
    step(6, 6, "Installing into decks/ with tools/deck_tool.py")
    cmd = [sys.executable, str(ROOT / "tools" / "deck_tool.py"), "add", str(out),
           "--id", meta["id"], "--name", meta["stem"], "--title", meta["title"],
           "--subtitle", meta.get("subtitle", ""), "--author", meta.get("author", ""),
           "--date", meta["date"], "--description", meta.get("description", ""),
           "--tags", ",".join(meta.get("tags", [])), "--force"]
    if meta.get("updated"):
        cmd += ["--updated", meta["updated"]]
    r = subprocess.run(cmd)
    if r.returncode:
        die("deck_tool.py add failed")
    links = json.loads((out / "links.json").read_text(encoding="utf-8"))
    dj = ROOT / "decks" / meta["id"] / "deck.json"
    d = json.loads(dj.read_text(encoding="utf-8"))
    d["links"] = links
    dj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "deck_tool.py"), "build"])
    if r.returncode:
        die("deck_tool.py build failed")
    info(f"links written to decks/{meta['id']}/deck.json")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="source/<NN_name> folder holding deck.src.html and meta.json")
    ap.add_argument("--no-install", action="store_true", help="build into build/<id>/ only; leave decks/ alone")
    a = ap.parse_args()
    src = Path(a.source).resolve()
    meta = json.loads((src / "meta.json").read_text(encoding="utf-8"))
    out = ROOT / "build" / meta["id"]
    if out.exists():
        shutil.rmtree(out)
    r = build(src, out, meta)
    if not a.no_install:
        install(out, meta)
    print(f"\nDone: {r['slides']} slides  ({time.time() - T0:.1f}s)")


if __name__ == "__main__":
    main()
