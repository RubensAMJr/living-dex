// Selection mode: select button, drag box, long-press, bottom bar, OT marks.

// Drag a box with the mouse (like selecting files in Windows), long-press on touch screens, or
// use the select button; then mark everything selected at once from the bar at the bottom.
const selectBtn = document.getElementById("selectBtn");
const selbar = document.getElementById("selbar");
const selCount = document.getElementById("selCount");
const marquee = document.getElementById("marquee");
const selected = new Set();
let selecting = false, suppressClick = false;

function setSel(e, on) {
  if (on === selected.has(e.id)) return;
  if (on) selected.add(e.id); else selected.delete(e.id);
  e.el.classList.toggle("sel", on);
}
function clearSelection() {
  for (const id of selected) byId.get(id).el.classList.remove("sel");
  selected.clear();
}
function updateSelbar() {
  selCount.textContent = `${selected.size.toLocaleString()} selected`;
  document.getElementById("selMark").disabled = document.getElementById("selUnmark").disabled = !selected.size;
}
function setSelecting(on) {
  if (on === selecting) return;
  selecting = on;
  if (!on) clearSelection();
  document.body.classList.toggle("selecting", on);
  selectBtn.setAttribute("aria-pressed", on ? "true" : "false");
  selbar.hidden = !on;
  updateSelbar();
}
selectBtn.addEventListener("click", () => setSelecting(!selecting));
document.getElementById("selDone").addEventListener("click", () => setSelecting(false));
document.getElementById("selAll").addEventListener("click", () => {
  for (const e of entries) if (!e.el.hidden) setSel(e, true);
  updateSelbar();
});
function markSelected(value, quiet = false) {
  const n = selected.size;
  const list = [...selected].map(id => byId.get(id)).filter(e => caught.has(e.id) !== value);
  // the paint-bucket fill plays on the ones you can see
  const paints = list.filter(e => onScreen.has(e.el)).map(e => preparePaint(e, null, value)).filter(Boolean);
  for (const e of list) { if (value) caught.add(e.id); else caught.delete(e.id); paintCard(e); }
  if (!value) dropOt(list.map(e => e.id));
  paints.forEach(p => p());
  updateCounts();
  save();
  // stay in selection mode with the same Pokémon selected (easy to undo or mark again)
  if (!quiet) toast(`${n.toLocaleString()} Pokémon marked ${value ? "caught" : "missing"}`);
}
document.getElementById("selMark").addEventListener("click", () => markSelected(true));
document.getElementById("selUnmark").addEventListener("click", () => markSelected(false));
function markSelectedOt(value) {
  if (value) markSelected(true, true); // an OT Pokémon is always a caught one
  const set = otSets[mode];
  for (const id of selected) { if (value) set.add(id); else set.delete(id); paintCard(byId.get(id)); }
  saveOt();
  toast(`${selected.size.toLocaleString()} Pokémon ${value ? "marked" : "unmarked"} as OT`);
}
document.getElementById("selOt").addEventListener("click", () => markSelectedOt(true));
document.getElementById("selUnOt").addEventListener("click", () => markSelectedOt(false));

// removes OT marks (current dex) for Pokémon that are no longer caught
function dropOt(ids) {
  let changed = false;
  for (const id of ids) if (otSets[mode].delete(id)) { changed = true; const x = byId.get(id); if (x && x.el) paintCard(x); }
  if (changed) saveOt();
}

function toggleOt(e, ev) {
  const set = otSets[mode];
  if (!set.has(e.id) && !caught.has(e.id)) toggle(e, ev); // an OT Pokémon is always a caught one
  if (set.has(e.id)) set.delete(e.id); else set.add(e.id);
  paintCard(e);
  saveOt();
  const btn = e.el.querySelector(".ot-btn");
  btn.classList.remove("pop"); void btn.offsetWidth; btn.classList.add("pop");
}

// --- drag box (mouse) ---
let drag = null;
main.addEventListener("dragstart", ev => ev.preventDefault());
// a drag can start anywhere on the page, including the empty margins beside the grid,
// but not on the header, the bars or any control
const NO_DRAG = "header, .selbar, .toast, .info, a, button, input, label, summary, select, textarea";
document.addEventListener("pointerdown", ev => {
  if (ev.pointerType === "mouse" && ev.button !== 0) return;
  if (ev.target.closest(NO_DRAG) || inGames) return; // no selecting on the game pages
  if (ev.pointerType === "mouse") drag = { x0: ev.pageX, y0: ev.pageY, cx: ev.clientX, cy: ev.clientY, active: false };
  startLongPress(ev); // holding still on a card (mouse or finger) also starts selecting
});
// no text highlighting while a drag box might be starting
document.addEventListener("selectstart", ev => { if (drag) ev.preventDefault(); });
function startDrag() {
  drag.active = true;
  setSelecting(true);
  drag.base = new Set(selected); // a new drag adds to what is already selected
  drag.boxes = [];
  for (const e of entries) {
    if (e.el.hidden) continue;
    const r = e.el.getBoundingClientRect();
    drag.boxes.push({ e, l: r.left + scrollX, t: r.top + scrollY, r: r.right + scrollX, b: r.bottom + scrollY });
  }
  document.body.classList.add("dragging");
  const s = window.getSelection && window.getSelection();
  if (s) s.removeAllRanges();
  marquee.classList.add("on");
  requestAnimationFrame(autoScroll);
}
function updateDrag() {
  const x1 = drag.cx + scrollX, y1 = drag.cy + scrollY;
  const l = Math.min(drag.x0, x1), t = Math.min(drag.y0, y1), r = Math.max(drag.x0, x1), b = Math.max(drag.y0, y1);
  marquee.style.left = `${l}px`; marquee.style.top = `${t}px`;
  marquee.style.width = `${r - l}px`; marquee.style.height = `${b - t}px`;
  for (const box of drag.boxes) {
    const inside = box.l < r && box.r > l && box.t < b && box.b > t;
    setSel(box.e, inside || drag.base.has(box.e.id));
  }
  updateSelbar();
}
// scroll the page while the pointer is held near the top or bottom edge
function autoScroll() {
  if (!drag || !drag.active) return;
  const top = header.classList.contains("tucked") ? 0 : header.getBoundingClientRect().bottom;
  const edge = 56;
  let dy = 0;
  if (drag.cy < top + edge) dy = -Math.ceil((top + edge - drag.cy) / 3);
  else if (drag.cy > window.innerHeight - edge) dy = Math.ceil((drag.cy - (window.innerHeight - edge)) / 3);
  if (dy) { window.scrollBy(0, dy); updateDrag(); }
  requestAnimationFrame(autoScroll);
}
window.addEventListener("pointermove", ev => {
  if (!drag) return;
  drag.cx = ev.clientX; drag.cy = ev.clientY;
  if (!drag.active) {
    if (Math.hypot(ev.pageX - drag.x0, ev.pageY - drag.y0) < 8) return; // still a plain click
    startDrag();
  }
  ev.preventDefault();
  updateDrag();
});
function endDrag() {
  if (drag && drag.active) {
    marquee.classList.remove("on");
    document.body.classList.remove("dragging");
    suppressClick = true;
    setTimeout(() => { suppressClick = false; }, 0);
  }
  drag = null;
}
window.addEventListener("pointerup", endDrag);
window.addEventListener("pointercancel", endDrag);

// --- long-press (touch) ---
let press = null;
function startLongPress(ev) {
  const card = ev.target.closest(".card");
  if (!card) return;
  const x = ev.clientX, y = ev.clientY;
  const cancel = () => { if (press) clearTimeout(press.timer); press = null; };
  const move = e => { if (press && Math.hypot(e.clientX - x, e.clientY - y) > 10) cancel(); };
  const up = () => {
    cancel();
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", up);
    window.removeEventListener("pointercancel", up);
  };
  press = { timer: setTimeout(() => {
    press = null;
    setSelecting(true);
    setSel(byId.get(card.dataset.id), true);
    updateSelbar();
    suppressClick = true;
    setTimeout(() => { suppressClick = false; }, 600);
    if (navigator.vibrate) navigator.vibrate(15);
  }, 450) };
  window.addEventListener("pointermove", move, { passive: true });
  window.addEventListener("pointerup", up);
  window.addEventListener("pointercancel", up);
}
// the click that ends a drag box or long-press is swallowed before anything else sees it
document.addEventListener("click", ev => {
  if (!suppressClick) return;
  suppressClick = false;
  ev.stopPropagation();
  ev.preventDefault();
}, true);
// clicking empty space (anything that isn't a Pokémon or a control) leaves selection mode
document.addEventListener("click", ev => {
  if (selecting && !ev.target.closest(".card, " + NO_DRAG + ", .menu")) setSelecting(false);
});
main.addEventListener("contextmenu", ev => { if (selecting && ev.target.closest(".card")) ev.preventDefault(); });


// Where the paint-bucket fill of a filter button starts: the click point, or the centre for
// keyboard presses and for buttons being deselected
function setFillOrigin(btn, ev) {
  const r = btn.getBoundingClientRect();
  const inside = ev && ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom;
  const x = inside ? ev.clientX - r.left : r.width / 2;
  const y = inside ? ev.clientY - r.top : r.height / 2;
  btn.style.setProperty("--x", `${x}px`);
  btn.style.setProperty("--y", `${y}px`);
  btn.style.setProperty("--reach", `${Math.ceil(Math.hypot(Math.max(x, r.width - x), Math.max(y, r.height - y))) + 24}px`); // slack for counts that widen the chip
}
function pressOne(buttons, chosen, ev) {
  for (const x of buttons) {
    const on = x === chosen;
    if ((x.getAttribute("aria-pressed") === "true") === on) continue;
    setFillOrigin(x, on ? ev : null);
    x.setAttribute("aria-pressed", on ? "true" : "false");
  }
}

const segButtons = [...document.querySelectorAll(".seg button")];
segButtons.forEach(b => b.addEventListener("click", ev => {
  pressOne(segButtons, b, ev);
  view.status = b.dataset.status;
  applyFilters();
}));

// on phones the category row scrolls sideways: bring the chosen chip to the middle
function revealChip(b) {
  if (gensNav.scrollWidth <= gensNav.clientWidth) return;
  const nr = gensNav.getBoundingClientRect(), br = b.getBoundingClientRect();
  gensNav.scrollBy({ left: (br.left + br.width / 2) - (nr.left + nr.width / 2), behavior: reducedMotion ? "auto" : "smooth" });
}
function selectGroup(key, ev) {
  const chosen = chips.find(x => x.dataset.group === key);
  pressOne(chips, chosen, ev);
  view.group = key;
  applyFilters();
  revealChip(chosen);
}
chips.forEach(b => b.addEventListener("click", ev => {
  selectGroup(b.dataset.group, ev);
  window.scrollTo({ top: 0 });
}));

document.getElementById("forms").addEventListener("change", ev => {
  view.forms = ev.target.checked;
  updateCounts();
  if (!view.forms && groupByKey.get(view.group)?.form) selectGroup("");
  else applyFilters();
});
