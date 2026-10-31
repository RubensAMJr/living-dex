// Menu: animation and display settings, backup export/import, bulk marking; tucking header.

const SETTINGS_KEY = "living-dex-checker-settings";
const settings = { shinyFx: true, paintFx: true, showOt: false };
try { Object.assign(settings, JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}")); } catch (e) {}
const optShinyFx = document.getElementById("optShinyFx");
const optPaintFx = document.getElementById("optPaintFx");
function applySettings() {
  optShinyFx.checked = settings.shinyFx;
  optPaintFx.checked = settings.paintFx;
  document.body.classList.toggle("no-paint", !settings.paintFx);
  document.getElementById("optShowOt").checked = settings.showOt;
  document.body.classList.toggle("show-ot", settings.showOt);
  // the Not OT filter disappears with the OT marks, so fall back to All
  if (!settings.showOt && view.status === "notot") {
    pressOne(segButtons, segButtons[0], null);
    view.status = "all";
    applyFilters();
  }
}
function saveSettings() {
  try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch (e) {}
}
optShinyFx.addEventListener("change", () => { settings.shinyFx = optShinyFx.checked; applySettings(); saveSettings(); });
optPaintFx.addEventListener("change", () => { settings.paintFx = optPaintFx.checked; applySettings(); saveSettings(); });
document.getElementById("optShowOt").addEventListener("change", ev => { settings.showOt = ev.target.checked; applySettings(); saveSettings(); });
applySettings();

// ---------- menu actions ----------
const menu = document.getElementById("menu");
document.addEventListener("click", ev => { if (!menu.contains(ev.target)) menu.open = false; });

const toastEl = document.getElementById("toast");
let toastTimer;
function toast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toastEl.classList.remove("show"), 2400);
}
function repaintAll() { entries.forEach(paintCard); updateCounts(); applyFilters(); save(); }
const dexName = () => mode === "shiny" ? "shiny dex" : "dex";

document.getElementById("exportBtn").addEventListener("click", () => {
  const today = new Date().toISOString().slice(0, 10);
  const ordered = set => entries.filter(e => set.has(e.id)).map(e => e.id);
  const payload = { app: "living-dex-checker", version: 2, exported: new Date().toISOString(),
                    caught: ordered(sets.normal), shiny: ordered(sets.shiny),
                    ot: ordered(otSets.normal), shinyOt: ordered(otSets.shiny) };
  const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 1)], { type: "application/json" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: `living-dex-backup-${today}.json` });
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  menu.open = false;
  toast("Backup exported (regular + shiny)");
});

const fileInput = document.getElementById("importFile");
document.getElementById("importBtn").addEventListener("click", () => { menu.open = false; fileInput.click(); });
fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  fileInput.value = "";
  if (!file) return;
  try {
    const data = JSON.parse(await file.text());
    const clean = list => (list || []).map(String).filter(id => byId.has(id));
    const normal = clean(Array.isArray(data) ? data : data.caught);
    const shiny = Array.isArray(data) || !("shiny" in data) ? null : clean(data.shiny);
    if (!normal.length && !(shiny && shiny.length)) throw new Error("no Pokémon found in file");
    const what = shiny ? `${normal.length} regular and ${shiny.length} shiny caught` : `${normal.length} caught, regular dex only`;
    if (!confirm(`Replace your checklist with this backup (${what})?`)) return;
    sets.normal.clear(); normal.forEach(id => sets.normal.add(id));
    if (shiny) { sets.shiny.clear(); shiny.forEach(id => sets.shiny.add(id)); }
    for (const [key, m] of [["ot", "normal"], ["shinyOt", "shiny"]]) {
      if (!Array.isArray(data) && key in data) { otSets[m].clear(); clean(data[key]).forEach(id => otSets[m].add(id)); }
      for (const id of [...otSets[m]]) if (!sets[m].has(id)) otSets[m].delete(id); // OT only for caught Pokémon
    }
    saveOt();
    // save both lists, then repaint the one on screen
    const current = mode;
    for (const m of ["normal", "shiny"]) { mode = m; caught = sets[m]; save(); }
    mode = current; caught = sets[mode];
    repaintAll();
    toast("Backup imported");
  } catch (err) {
    alert(`Couldn't import that file: ${err.message}`);
  }
});

function markShown(value) {
  const shown = entries.filter(e => !e.el.hidden);
  menu.open = false;
  if (!shown.length) return;
  if (!confirm(`Mark ${shown.length} shown Pokémon as ${value ? "caught" : "missing"} in the ${dexName()}?`)) return;
  shown.forEach(e => value ? caught.add(e.id) : caught.delete(e.id));
  repaintAll();
  toast(`${shown.length} marked ${value ? "caught" : "missing"}`);
}
document.getElementById("markVisible").addEventListener("click", () => markShown(true));
document.getElementById("unmarkVisible").addEventListener("click", () => markShown(false));

document.getElementById("resetBtn").addEventListener("click", () => {
  menu.open = false;
  const msg = mode === "shiny"
    ? "Clear the shiny dex? Every shiny becomes missing."
    : "Clear the regular dex? Every Pokémon becomes missing.";
  if (!confirm(msg)) return;
  sets[mode] = defaults[mode]();
  caught = sets[mode];
  otSets[mode].clear();
  saveOt();
  repaintAll();
  toast(mode === "shiny" ? "Shiny dex cleared" : "Regular dex cleared");
});

// ---------- header that tucks away while scrolling down (small screens) ----------
const header = document.querySelector("header");
let autoHide = false, lastY = window.scrollY, scrollQueued = false;
function measureHeader() {
  // only when the header would take a big bite out of the screen (phones, short windows)
  autoHide = header.offsetHeight > window.innerHeight * 0.2;
  if (!autoHide) header.classList.remove("tucked");
}
function onScroll() {
  scrollQueued = false;
  const y = window.scrollY;
  if (!autoHide || y < header.offsetHeight || menu.open || document.activeElement === q) {
    header.classList.remove("tucked");
    lastY = y;
    return;
  }
  const dy = y - lastY;
  if (Math.abs(dy) < 8) return; // ignore small jitters, keep accumulating
  header.classList.toggle("tucked", dy > 0);
  lastY = y;
}
window.addEventListener("scroll", () => { if (!scrollQueued) { scrollQueued = true; requestAnimationFrame(onScroll); } }, { passive: true });
window.addEventListener("resize", measureHeader, { passive: true });
menu.addEventListener("toggle", () => { if (menu.open) header.classList.remove("tucked"); });
q.addEventListener("focus", () => header.classList.remove("tucked"));
