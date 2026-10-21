"""One-off patch: adds OT (original trainer) marks to src/index.template.html.

- Menu option "Show OT marks" (off by default) shows a small Ash-cap button at each card's top-left.
- Grey cap = not marked, full colour = marked; clicking it toggles the mark.
- Separate OT marks for the regular and the shiny dex, saved in this browser and in backups.
- Selection mode gets "Mark OT" / "Unmark OT" buttons while OT marks are shown.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "index.template.html"
CAP = (ROOT / "tools" / "data" / "ot-cap.txt").read_text(encoding="utf-8").strip()
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


CSS = """  /* ---------- OT (original trainer) marks: Ash's cap at the card's top-left ---------- */
  .ot-btn {
    display: none; position: absolute; top: 4px; left: 4px; z-index: 2; width: 24px; height: 24px; padding: 0;
    border: 0; border-radius: 4px; cursor: pointer; background: var(--cap) center / contain no-repeat;
    filter: grayscale(1) brightness(.7); opacity: .5; transition: filter .2s, opacity .2s, transform .15s;
  }
  body.show-ot .ot-btn { display: block; }
  .card.on:not(.t-shiny) .ot-btn, .card.os.t-shiny .ot-btn { filter: none; opacity: 1; }
  .ot-btn.pop { animation: ot-pop .35s cubic-bezier(.3,1.6,.5,1); }
  @keyframes ot-pop { 40% { transform: scale(1.4) rotate(-12deg); } }
  .ot-btn:focus-visible { outline: 2px solid var(--accent-hi); outline-offset: 1px; }
  body:not(.show-ot) .ot-only { display: none; }
  @media (hover: hover) { .ot-btn:hover { opacity: 1; transform: scale(1.12); } }

  /* ---------- Pokédex detail tile ---------- */"""
rep("  /* ---------- Pokédex detail tile ---------- */", CSS)
rep("  :root {\n", f'  :root {{\n    --cap: url("{CAP}");\n')

# menu: a Display section with the OT switch
rep("""          <label class="opt"><span>Colour fill on click</span><input type="checkbox" id="optPaintFx" role="switch" checked></label>""",
    """          <label class="opt"><span>Colour fill on click</span><input type="checkbox" id="optPaintFx" role="switch" checked></label>
          <hr>
          <div class="head">Display</div>
          <label class="opt"><span>Show OT marks</span><input type="checkbox" id="optShowOt" role="switch"></label>""")
# selection bar
rep("""  <button type="button" id="selUnmark">Mark missing</button>""",
    """  <button type="button" id="selUnmark">Mark missing</button>
  <button type="button" id="selOt" class="ot-only">Mark OT</button>
  <button type="button" id="selUnOt" class="ot-only">Unmark OT</button>""")

# storage
rep("""const KEYS = { normal: "living-dex-checker-v2", shiny: "living-dex-checker-shiny-v2" };""",
    """const KEYS = { normal: "living-dex-checker-v2", shiny: "living-dex-checker-shiny-v2" };
// OT (original trainer) marks: separate lists for the regular and the shiny dex
const OT_KEYS = { normal: "living-dex-checker-ot-v1", shiny: "living-dex-checker-shiny-ot-v1" };""")
rep("""const sets = { normal: load("normal"), shiny: load("shiny") };""",
    """const sets = { normal: load("normal"), shiny: load("shiny") };
function loadOt(m) {
  try {
    const arr = JSON.parse(localStorage.getItem(OT_KEYS[m]) || "[]");
    if (Array.isArray(arr)) return new Set(arr.filter(id => byId.has(id)));
  } catch (e) { storageOk = false; }
  return new Set();
}
const otSets = { normal: loadOt("normal"), shiny: loadOt("shiny") };
function saveOt() {
  try { for (const m of ["normal", "shiny"]) localStorage.setItem(OT_KEYS[m], JSON.stringify([...otSets[m]])); }
  catch (e) { storageOk = false; }
}""")

# cards
rep("""  const cls = (sets.normal.has(e.id) ? " cn" : "") + (sets.shiny.has(e.id) ? " cs" : "") + (mode === "shiny" ? " t-shiny" : "");""",
    """  const cls = (sets.normal.has(e.id) ? " cn" : "") + (sets.shiny.has(e.id) ? " cs" : "") + (mode === "shiny" ? " t-shiny" : "") +
              (otSets.normal.has(e.id) ? " on" : "") + (otSets.shiny.has(e.id) ? " os" : "");""")
rep("""    `<span class="tick"></span><div class="num">#${pad(e.dex)}</div><div class="name">${label}</div>` +""",
    """    `<button type="button" class="ot-btn" aria-label="Original trainer mark for ${label}" title="OT: caught by you (click to toggle)"></button>` +
    `<span class="tick"></span><div class="num">#${pad(e.dex)}</div><div class="name">${label}</div>` +""")
rep("""  e.el.classList.toggle("cs", sets.shiny.has(e.id));""",
    """  e.el.classList.toggle("cs", sets.shiny.has(e.id));
  e.el.classList.toggle("on", otSets.normal.has(e.id));
  e.el.classList.toggle("os", otSets.shiny.has(e.id));""")

# clicking the cap toggles the OT mark (never the caught mark)
rep("""  const infoBtn = ev.target.closest(".info-btn");""",
    """  const otBtn = ev.target.closest(".ot-btn");
  if (otBtn) { ev.stopPropagation(); toggleOt(byId.get(otBtn.closest(".card").dataset.id)); return; }
  const infoBtn = ev.target.closest(".info-btn");""")

# selection mode actions
rep("""document.getElementById("selUnmark").addEventListener("click", () => markSelected(false));""",
    """document.getElementById("selUnmark").addEventListener("click", () => markSelected(false));
function markSelectedOt(value) {
  const set = otSets[mode];
  for (const id of selected) { if (value) set.add(id); else set.delete(id); paintCard(byId.get(id)); }
  saveOt();
  toast(`${selected.size.toLocaleString()} Pokémon ${value ? "marked" : "unmarked"} as OT`);
}
document.getElementById("selOt").addEventListener("click", () => markSelectedOt(true));
document.getElementById("selUnOt").addEventListener("click", () => markSelectedOt(false));

function toggleOt(e) {
  const set = otSets[mode];
  if (set.has(e.id)) set.delete(e.id); else set.add(e.id);
  paintCard(e);
  saveOt();
  const btn = e.el.querySelector(".ot-btn");
  btn.classList.remove("pop"); void btn.offsetWidth; btn.classList.add("pop");
}""")

# settings
rep("""const settings = { shinyFx: true, paintFx: true };""", """const settings = { shinyFx: true, paintFx: true, showOt: false };""")
rep("""  document.body.classList.toggle("no-paint", !settings.paintFx);""",
    """  document.body.classList.toggle("no-paint", !settings.paintFx);
  document.getElementById("optShowOt").checked = settings.showOt;
  document.body.classList.toggle("show-ot", settings.showOt);""")
rep("""optPaintFx.addEventListener("change", () => { settings.paintFx = optPaintFx.checked; applySettings(); saveSettings(); });""",
    """optPaintFx.addEventListener("change", () => { settings.paintFx = optPaintFx.checked; applySettings(); saveSettings(); });
document.getElementById("optShowOt").addEventListener("change", ev => { settings.showOt = ev.target.checked; applySettings(); saveSettings(); });""")

# backups carry the OT marks too
rep("""                    caught: ordered(sets.normal), shiny: ordered(sets.shiny) };""",
    """                    caught: ordered(sets.normal), shiny: ordered(sets.shiny),
                    ot: ordered(otSets.normal), shinyOt: ordered(otSets.shiny) };""")
rep("""    if (shiny) { sets.shiny.clear(); shiny.forEach(id => sets.shiny.add(id)); }""",
    """    if (shiny) { sets.shiny.clear(); shiny.forEach(id => sets.shiny.add(id)); }
    for (const [key, m] of [["ot", "normal"], ["shinyOt", "shiny"]]) {
      if (!Array.isArray(data) && key in data) { otSets[m].clear(); clean(data[key]).forEach(id => otSets[m].add(id)); }
    }
    saveOt();""")

SRC.write_text(src, encoding="utf-8")
print("ok")
