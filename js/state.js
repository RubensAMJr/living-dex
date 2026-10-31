// Saved progress: caught / shiny / OT marks in localStorage, current dex mode and filters.

// Nothing is marked at the start; saved marks are always kept exactly as saved.
const defaults = { normal: () => new Set(), shiny: () => new Set() };
let storageOk = true;
function load(mode) {
  try {
    const raw = localStorage.getItem(KEYS[mode]);
    if (raw) {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) {
        return new Set(arr.filter(id => byId.has(id)));
      }
    }
  } catch (e) { storageOk = false; }
  return defaults[mode]();
}
function save() {
  if (!entries.length) return; // never overwrite saved marks from a page without data
  try {
    localStorage.setItem(KEYS[mode], JSON.stringify([...caught]));
    localStorage.setItem(MODE_KEY, mode);
  } catch (e) { storageOk = false; }
  document.getElementById("warn").classList.toggle("show", !storageOk);
}
const sets = { normal: load("normal"), shiny: load("shiny") };
function loadOt(m) {
  try {
    const arr = JSON.parse(localStorage.getItem(OT_KEYS[m]) || "[]");
    if (Array.isArray(arr)) return new Set(arr.filter(id => byId.has(id)));
  } catch (e) { storageOk = false; }
  return new Set();
}
const otSets = { normal: loadOt("normal"), shiny: loadOt("shiny") };
// an OT Pokémon is always a caught one: drop OT marks left over on missing Pokémon
for (const m of ["normal", "shiny"]) for (const id of [...otSets[m]]) if (!sets[m].has(id)) otSets[m].delete(id);
function saveOt() {
  try { for (const m of ["normal", "shiny"]) localStorage.setItem(OT_KEYS[m], JSON.stringify([...otSets[m]])); }
  catch (e) { storageOk = false; }
}
let mode = "normal";
try { if (localStorage.getItem(MODE_KEY) === "shiny") mode = "shiny"; } catch (e) {}
let caught = sets[mode];

const view = { q: "", words: [], num: null, status: "all", group: "", forms: true };
