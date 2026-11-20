<img src="assets/icon/icon.svg" width="96" alt="">

# ATLAS presentations · 19 Nov 2026

Two decks by Nathan Herling (UA ATLAS HEP Group). Each one plays in the browser and can be downloaded as a **PDF**, a **PowerPoint (.pptx)** file, or a **single self-contained HTML** file.

This is a static site: plain HTML, CSS and JS with no framework. It runs on GitHub Pages and also straight from disk (double-click `index.html`). It uses the same landing page and player as [ATLAS_presentations_](https://n-herling-mk1.github.io/ATLAS_presentations_/).

## Decks

Open `index.html` (the splash page) and pick a deck. Inside a deck, the ⌂ button returns to the splash page.

| # | Date | Deck | Slides | Status |
|---|---|---|---|---|
| 1 | 19 Nov 2026 | [UNKNOT: project overview](decks/2026-11-19_unknot-overview/index.html) | 10 | locked |
| 2 | 19 Nov 2026 | [Arizona ATLAS ML projects: overview](decks/2026-11-19_atlas-ml-overview/index.html) | 10 | draft |
| 3 | 20 Nov 2026 | [DisCo alone vs DisCo + queen: top and bottom performers](decks/2026-11-20_qn-performers/index.html) | 19 | draft |

Deck 1, slides 1–5 are the vetted overview; slide 6 marks the end of vetted work, and slides 7–10 are working material carried over from the mk1 deck.

Deck 2 covers the whole project line in the [Gallery of Rogues](https://n-herling-mk1.github.io/ATLAS_Master_Project_Repo/):

| Slide | Content |
|---|---|
| 1 | Cover: the thirteen project logos |
| 2 | What every project page holds, with a link to the master view |
| 3 | Thirteen projects, one anatomy (matrix) |
| 4 | Main spine: SIG/BG → GAMBIT → BASELINE \| DNCn_QN + DisCo → ABCD plane health, and GAMBIT in short |
| 5 | INFO 555 techniques we (Nathan) want to bring in |
| 6 | The queen (DNCn_QN) in words |
| 7 | Endcap pull figure, annotated |
| 8 | Barrel pull figure, annotated |
| 9 | The queen's two mk2 variants: QB and QDR / τ̂² |
| 10 | The loss in full, and where she should work |

Deck 3 is the first read of the QN performers pipeline (the 15 best and 15 worst runs per region, endcap R15/R16a and barrel R16). Every number on it comes from `source/03_qn_performers/deck_numbers.py`, which reads the pipeline's `data/manifest.js` and writes `numbers.json`. Figures are in `source/03_qn_performers/assets/` (`figure_sources.json` maps each to its run); the ABCD planes come from `qp_deckfigs.py` in the QN performers repo.

> **Internal, exploratory.** UNKNOT numbers are mk1 results on background data only. DNCn_QN / DisCo numbers are internal studies. None of this is an ATLAS result.

## Layout

```
index.html                 splash page: one tile per presentation (Present / Live HTML / PDF / PPTX)
catalog.js                 GENERATED list of built decks, read by the splash page
assets/
  splash.css, splash.js    splash page; splash.js also holds the fixed slot order and the "in preparation" tile
  fonts/                   Orbitron, Inter, Share Tech Mono (woff2, SIL OFL), so the splash works offline
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
python tools/build_html_deck.py source/02_atlas_ml_overview
```

The build prints a progress line per stage:

1. inline the fonts and images
2. pre-render the math to SVG with the vendored MathJax
3. render each slide to a 1920x1080 PNG and warn about anything that spills off a slide
4. print a vector PDF
5. build the PPTX: one full-slide image per slide, with the speaker notes from `meta.json`
6. install the result into `decks/<id>/` and rewrite `catalog.js`

`--no-install` stops after step 5 and leaves the output in `build/<id>/`, which is git-ignored.

**Links:** every `<a href>` on a slide stays clickable. The build records each link's box in `deck.json` (`links`), and the player lays a click area over the slide image; links to other sites open in a new tab. The PDF keeps them as link annotations, and the PPTX has a transparent hyperlinked box over each one.

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

- Project logos: [ATLAS_Master_Project_Repo](https://n-herling-mk1.github.io/ATLAS_Master_Project_Repo/) (Gallery of Rogues)
- Deck 2, slides 7–8: figures from [DisCo + the queen, endcap and barrel](https://n-herling-mk1.github.io/ATLAS_presentations_DNCn_QN/) (slides 5–6), annotations added; the endcap legend was replaced by an HTML key
- MathJax 3.2.2 (Apache-2.0, `tools/vendor/LICENSE_MathJax.txt`). Fonts: Orbitron, Inter, Share Tech Mono (SIL OFL, `tools/vendor/fonts/LICENSE_OFL.txt`).

Part of the [ATLAS presentations](https://n-herling-mk1.github.io/ATLAS_presentations_/) collection · Nathan Herling · UA ATLAS HEP Group
