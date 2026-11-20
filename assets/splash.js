// Splash page: one tile per presentation, in the fixed order below.
// Built decks come from window.CATALOG (catalog.js, written by tools/deck_tool.py).
// A slot whose deck is not built yet shows as "in preparation" until its id appears in the catalog.
(function () {
  "use strict";
  const SLOTS = [
    { num: 1, id: "2026-11-19_unknot-overview" },
    { num: 2, id: "2026-11-19_atlas-ml-overview" },
    { num: 3, id: "2026-11-20_qn-performers" },  ];
  const cat = (window.CATALOG && window.CATALOG.decks) || [];
  const byId = Object.fromEntries(cat.map((d) => [d.id, d]));
  const host = document.getElementById("decks");
  const el = (t, c, txt) => { const e = document.createElement(t); if (c) e.className = c; if (txt !== undefined) e.textContent = txt; return e; };
  const mb = (n) => (n ? (n / 1048576).toFixed(1) + " MB" : "");
  const nice = (s) => { if (!s) return ""; const d = new Date(s + "T12:00:00"); return isNaN(d) ? s : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }); };
  const tiles = [];

  SLOTS.forEach((slot) => {
    const d = slot.id && byId[slot.id];
    const t = el("article", "deck" + (d ? "" : " planned"));
    t.tabIndex = 0;
    t.appendChild(el("span", "num", String(slot.num).padStart(2, "0")));
    const page = d ? "decks/" + d.id + "/index.html" : null;   // explicit file: folder links fail from disk

    const shot = el(d ? "a" : "div", "shot");
    if (d) { shot.href = page; shot.setAttribute("aria-label", "Present " + d.title); }
    const img = el("img"); img.alt = ""; img.loading = "lazy";
    img.src = d ? "decks/" + d.id + "/" + d.thumb : slot.thumb;
    shot.appendChild(img);
    if (!d) shot.appendChild(el("span", "stamp", "IN PREPARATION"));
    t.appendChild(shot);

    const b = el("div", "body");
    b.appendChild(el("div", "meta", d ? [nice(d.date), d.slides + " slides", "presentation " + slot.num].join(" · ") : "presentation " + slot.num + " · not built yet"));
    const h = el("h2");
    if (d) { const a = el("a", "", d.title); a.href = page; h.appendChild(a); } else h.textContent = slot.title;
    b.appendChild(h);
    b.appendChild(el("p", "sub", d ? d.subtitle : slot.sub));
    const tags = el("div", "tags"); ((d ? d.tags : slot.tags) || []).slice(0, 6).forEach((x) => tags.appendChild(el("span", "tag", x))); b.appendChild(tags);

    const act = el("div", "actions");
    if (d) {
      const p = el("a", "btn primary", "PRESENT"); p.href = page; act.appendChild(p);
      [["html", "LIVE HTML", "one file, works offline"], ["pdf", "PDF", "one slide per page"], ["pptx", "PPTX", "with speaker notes"]].forEach(([k, label, title]) => {
        const f = d.files && d.files[k]; if (!f) return;
        const a = el("a", "btn"); a.href = "decks/" + d.id + "/" + f.path; a.title = title;
        if (k !== "html") a.setAttribute("download", f.name);
        a.append(label + " "); a.appendChild(el("small", "", mb(f.bytes))); act.appendChild(a);
      });
    } else {
      act.appendChild(el("span", "btn", "PRESENT"));
      act.appendChild(el("p", "note", "Coming next."));
    }
    b.appendChild(act);
    t.appendChild(b);
    t.dataset.page = page || "";
    host.appendChild(t);
    tiles.push(t);
  });

  // selection: 1 / 2 keys, arrows, Enter presents; remembered for this visit only
  let sel = 0;
  function select(i) { sel = Math.max(0, Math.min(tiles.length - 1, i)); tiles.forEach((t, k) => t.classList.toggle("sel", k === sel)); }
  tiles.forEach((t, k) => { t.addEventListener("focus", () => select(k)); t.addEventListener("mouseenter", () => select(k)); });
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT") return;
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= tiles.length) { select(n - 1); tiles[n - 1].focus(); }
    else if (e.key === "ArrowRight" || e.key === "ArrowDown") { select(sel + 1); tiles[sel].focus(); e.preventDefault(); }
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { select(sel - 1); tiles[sel].focus(); e.preventDefault(); }
    else if (e.key === "Enter" && tiles[sel].dataset.page) { location.href = tiles[sel].dataset.page; }
  });
  select(0);
})();
