// Card clicks and keyboard, and the search box.

main.addEventListener("click", ev => {
  const otBtn = ev.target.closest(".ot-btn");
  if (otBtn) { ev.stopPropagation(); toggleOt(byId.get(otBtn.closest(".card").dataset.id), ev); return; }
  const infoBtn = ev.target.closest(".info-btn");
  if (infoBtn) { ev.stopPropagation(); toggleInfo(byId.get(infoBtn.closest(".card").dataset.id)); return; }
  if (ev.target.closest(".info")) return;
  const card = ev.target.closest(".card");
  if (!card) return;
  const e = byId.get(card.dataset.id);
  if (selecting) { setSel(e, !selected.has(e.id)); updateSelbar(); }
  else toggle(e, ev);
});
main.addEventListener("keydown", ev => {
  const card = ev.target.closest(".card");
  if (card && (ev.key === " " || ev.key === "Enter")) {
    ev.preventDefault();
    const e = byId.get(card.dataset.id);
    if (selecting) { setSel(e, !selected.has(e.id)); updateSelbar(); } else toggle(e);
  }
});

const q = document.getElementById("q");
let qTimer;
function setQuery(value) {
  view.q = fold(value.trim());
  const num = view.q.replace(/^#/, "");
  view.num = /^\d+$/.test(num) ? Number(num) : null;
  view.words = view.q ? view.q.split(/\s+/) : [];
  applyFilters();
}
q.addEventListener("input", () => {
  clearTimeout(qTimer);
  qTimer = setTimeout(() => setQuery(q.value), 80);
});
q.addEventListener("keydown", ev => { if (ev.key === "Enter") q.blur(); }); // closes the phone keyboard
// a shorter hint where the full one would be cut off
const longHint = q.placeholder;
const narrow = window.matchMedia("(max-width: 700px)");
const setHint = () => { q.placeholder = narrow.matches ? "Name, number or region" : longHint; };
if (narrow.addEventListener) narrow.addEventListener("change", setHint);
setHint();
document.addEventListener("keydown", ev => {
  if (ev.key === "/" && document.activeElement !== q) { ev.preventDefault(); q.focus(); q.select(); }
  else if (ev.key === "Escape" && document.activeElement === q) { q.value = ""; setQuery(""); q.blur(); }
  else if (ev.key === "Escape" && openInfo) closeInfo();
  else if (ev.key === "Escape" && selecting) setSelecting(false);
});
