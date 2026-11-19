<img src="assets/icon/icon.svg" width="96" alt="">

# ATLAS presentations · 19 Nov 2026

Two decks by Nathan Herling (UA ATLAS HEP Group). Each one plays in the browser and can be downloaded as a **PDF**, a **PowerPoint (.pptx)** file, or a **single self-contained HTML** file.

This is a static site: plain HTML, CSS and JS with no framework. It runs on GitHub Pages and also straight from disk (double-click `index.html`). It uses the same landing page and player as [ATLAS_presentations_](https://n-herling-mk1.github.io/ATLAS_presentations_/).

## Decks

Open `index.html` (the splash page) and pick a deck. Inside a deck, the ⌂ button returns to the splash page.

| # | Date | Deck | Slides | Status |
|---|---|---|---|---|
| 1 | 19 Nov 2026 | [UNKNOT: project overview](decks/2026-11-19_unknot-overview/index.html) | 10 | locked |
| 2 | 19 Nov 2026 | Project compendium + DNCn_QN overview | – | in preparation |

Deck 1, slides 1–5 are the vetted overview; slide 6 marks the end of vetted work, and slides 7–10 are working material carried over from the mk1 deck.

> **Internal, exploratory.** UNKNOT numbers are mk1 results on background data only. They are preliminary and are not an ATLAS result.

## Layout

```
index.html                 splash page: one tile per presentation (Present / Live HTML / PDF / PPTX)
catalog.js                 GENERATED list of built decks, read by the splash page
assets/
  splash.css, splash.js    splash page; splash.js also holds the fixed slot order and the "in preparation" tile
  fonts/                   Orbitron, Inter, Share Tech Mono (woff2, SIL OFL), so the splash works offline
  img/                     project logos for tiles that are not built yet
  player.css, player.js    the slide player, shared by every deck
  templates/player.html    template for each deck's index.html
  icon/                    repo icon
source/<NN_name>/          decks written as live HTML: the source you edit
  deck.src.html            1280x720 slides, TeX math in \( \) and \[ \]
  meta.json                id, title, description, tags, speaker notes (one per slide)
  assets/                  images the deck uses (e.g. the project logo)
decks/<id>/                GENERATED from source/ (do not edit by hand)
  deck.json, index.html, deck.js
  slides/s-NN.png          1920x1080 slide images (what the player shows)
  thumbs/s-NN.jpg          thumbnails
  downloads/               .pdf (vector) · .pptx (with notes) · _single_file.html (live deck, works offline)
tools/
  build_html_deck.py       source/<NN_name>  ->  decks/<id>/
  deck_tool.py             the hub's deck installer (also handles decks from a folder / .zip / PDF)
  vendor/                  MathJax (tex-svg-full.js) and the woff2 fonts, so builds need no network
```

## Build a deck

```bash
pip install playwright pillow python-pptx
python -m playwright install chromium

python tools/build_html_deck.py source/01_unknot_overview
```

The build prints a progress line per stage:

1. inline the fonts and images
2. pre-render the math to SVG with the vendored MathJax
3. render each slide to a 1920x1080 PNG and warn about anything that spills off a slide
4. print a vector PDF
5. build the PPTX: one full-slide image per slide, with the speaker notes from `meta.json`
6. install the result into `decks/<id>/` and rewrite `catalog.js`

`--no-install` stops after step 5 and leaves the output in `build/<id>/`, which is git-ignored.

**PPTX note:** each PowerPoint slide is a picture of the HTML slide, with editable speaker notes. The slide text itself is not editable in PowerPoint. The single-file HTML is the sharp, live version.

## Player keys

| Key | Action |
|---|---|
| → Space PgDn / ← PgUp | next / previous slide |
| Home / End | first / last slide |
| G | overview grid |
| N | speaker notes |
| D | downloads menu |
| F | full screen |
| ? | key list |
| `#N` in the URL | open on slide N |

## Sources

- UNKNOT logo: [ATLAS_Master_Project_Repo · unknot](https://n-herling-mk1.github.io/ATLAS_Master_Project_Repo/#unknot)
- MathJax 3.2.2 (Apache-2.0, `tools/vendor/LICENSE_MathJax.txt`). Fonts: Orbitron, Inter, Share Tech Mono (SIL OFL, `tools/vendor/fonts/LICENSE_OFL.txt`).

Part of the [ATLAS presentations](https://n-herling-mk1.github.io/ATLAS_presentations_/) collection · Nathan Herling · UA ATLAS HEP Group
