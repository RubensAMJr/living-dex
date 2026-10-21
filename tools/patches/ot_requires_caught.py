"""One-off patch: an OT mark always implies caught.
- Marking OT on a missing Pokémon also marks it caught (with the paint-bucket fill).
- Marking a Pokémon missing (card click, selection, Clear dex) also removes its OT mark.
- Imported backups drop OT marks for Pokémon that aren't caught.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "index.template.html"
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


# card click: going missing drops the OT mark
rep("""  if (nowCaught) caught.add(e.id); else caught.delete(e.id);
  paintCard(e);
  if (paint) paint();""", """  if (nowCaught) caught.add(e.id); else { caught.delete(e.id); dropOt([e.id]); }
  paintCard(e);
  if (paint) paint();""")

# selection: marking missing drops OT; marking OT marks caught first
rep("""  for (const e of list) { if (value) caught.add(e.id); else caught.delete(e.id); paintCard(e); }
  paints.forEach(p => p());
  updateCounts();
  save();
  // stay in selection mode with the same Pokémon selected (easy to undo or mark again)
  toast(`${n.toLocaleString()} Pokémon marked ${value ? "caught" : "missing"}`);
}""", """  for (const e of list) { if (value) caught.add(e.id); else caught.delete(e.id); paintCard(e); }
  if (!value) dropOt(list.map(e => e.id));
  paints.forEach(p => p());
  updateCounts();
  save();
  // stay in selection mode with the same Pokémon selected (easy to undo or mark again)
  if (!quiet) toast(`${n.toLocaleString()} Pokémon marked ${value ? "caught" : "missing"}`);
}""")
rep("""function markSelected(value) {""", """function markSelected(value, quiet = false) {""")
rep("""function markSelectedOt(value) {
  const set = otSets[mode];""", """function markSelectedOt(value) {
  if (value) markSelected(true, true); // an OT Pokémon is always a caught one
  const set = otSets[mode];""")

# cap click: OT on a missing Pokémon marks it caught too
rep("""function toggleOt(e) {
  const set = otSets[mode];
  if (set.has(e.id)) set.delete(e.id); else set.add(e.id);""", """// removes OT marks (current dex) for Pokémon that are no longer caught
function dropOt(ids) {
  let changed = false;
  for (const id of ids) if (otSets[mode].delete(id)) { changed = true; const x = byId.get(id); if (x && x.el) paintCard(x); }
  if (changed) saveOt();
}

function toggleOt(e, ev) {
  const set = otSets[mode];
  if (!set.has(e.id) && !caught.has(e.id)) toggle(e, ev); // an OT Pokémon is always a caught one
  if (set.has(e.id)) set.delete(e.id); else set.add(e.id);""")
rep("""toggleOt(byId.get(otBtn.closest(".card").dataset.id)); return; }""",
    """toggleOt(byId.get(otBtn.closest(".card").dataset.id), ev); return; }""")

# Clear dex: clears that dex's OT marks too
rep("""  sets[mode] = defaults[mode]();
  caught = sets[mode];
  repaintAll();""", """  sets[mode] = defaults[mode]();
  caught = sets[mode];
  otSets[mode].clear();
  saveOt();
  repaintAll();""")

# import: OT marks only for caught Pokémon
rep("""    for (const [key, m] of [["ot", "normal"], ["shinyOt", "shiny"]]) {
      if (!Array.isArray(data) && key in data) { otSets[m].clear(); clean(data[key]).forEach(id => otSets[m].add(id)); }
    }""", """    for (const [key, m] of [["ot", "normal"], ["shinyOt", "shiny"]]) {
      if (!Array.isArray(data) && key in data) { otSets[m].clear(); clean(data[key]).forEach(id => otSets[m].add(id)); }
      for (const id of [...otSets[m]]) if (!sets[m].has(id)) otSets[m].delete(id); // OT only for caught Pokémon
    }""")

SRC.write_text(src, encoding="utf-8")
print("ok")
