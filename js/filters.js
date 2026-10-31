// Category chips, counts, search/filter logic, and marking a card (with the paint fill).

const gensNav = document.getElementById("gens");
const chips = [{ key: "", chip: "All", form: false }, ...GROUPS].map(c => {
  if (c.form && c === GROUPS.find(x => x.form)) {
    gensNav.insertAdjacentHTML("beforeend", `<span class="chip-sep form-chip" aria-hidden="true"></span>`);
  }
  const b = document.createElement("button");
  b.type = "button";
  b.className = "gen-chip" + (c.form ? " form-chip" : "");
  b.dataset.group = c.key;
  b.setAttribute("aria-pressed", c.key === "" ? "true" : "false");
  if (c.chipTitle) b.title = c.chipTitle;
  b.innerHTML = `${c.chip}<small></small>`;
  b.small = b.querySelector("small");
  gensNav.appendChild(b);
  return b;
});
const formChips = [...gensNav.querySelectorAll(".form-chip")];
const els = {
  caughtCount: document.getElementById("caughtCount"), totalCount: document.getElementById("totalCount"),
  pct: document.getElementById("pct"), fill: document.getElementById("fill"),
  formsDivider: document.getElementById("formsDivider"), empty: document.getElementById("empty"),
};

// ---------- rendering ----------
function inScope(e) { return view.forms || !e.region; }

function paintCard(e) {
  e.el.classList.toggle("cn", sets.normal.has(e.id));
  e.el.classList.toggle("cs", sets.shiny.has(e.id));
  e.el.classList.toggle("on", otSets.normal.has(e.id));
  e.el.classList.toggle("os", otSets.shiny.has(e.id));
  e.el.setAttribute("aria-checked", caught.has(e.id) ? "true" : "false");
}

function updateCounts() {
  let total = 0, have = 0;
  const per = new Map(GROUPS.map(g => [g.key, [0, 0]]));
  for (const e of entries) {
    if (!inScope(e)) continue;
    const c = per.get(e.group.key);
    c[1]++; total++;
    if (caught.has(e.id)) { c[0]++; have++; }
  }
  els.caughtCount.textContent = have.toLocaleString();
  els.totalCount.textContent = total.toLocaleString();
  const pct = total ? have / total : 0;
  els.pct.textContent = `${(pct * 100).toFixed(1)}%`;
  els.fill.style.transform = `scaleX(${pct})`;
  for (const s of sections.values()) {
    const [h, t] = per.get(s.g.key);
    s.count.textContent = `${h} / ${t}${h === t ? " ✓" : ""}`;
  }
  chips.forEach(b => {
    const key = b.dataset.group;
    const [h, t] = key ? per.get(key) : [have, total];
    b.small.textContent = `${h}/${t}`;
    b.classList.toggle("done", h === t);
  });
}

function matches(e) {
  if (!inScope(e)) return false;
  if (view.group && e.group.key !== view.group) return false;
  const on = caught.has(e.id);
  if (view.status === "caught" && !on) return false;
  if (view.status === "missing" && on) return false;
  if (view.status === "notot" && (!on || otSets[mode].has(e.id))) return false; // caught but not OT-marked
  if (view.num !== null) return e.dex === view.num;
  return view.words.every(w => e.text.includes(w));
}

function applyFilters() {
  let shown = 0;
  const perSec = new Set();
  for (const e of entries) {
    const ok = matches(e);
    if (e.el.hidden === ok) e.el.hidden = !ok;
    if (ok) { shown++; perSec.add(e.group.key); }
  }
  let anyForms = false;
  for (const s of sections.values()) {
    const hide = !perSec.has(s.g.key);
    if (s.sec.hidden !== hide) s.sec.hidden = hide;
    if (s.g.form && !hide) anyForms = true;
  }
  els.formsDivider.hidden = !anyForms;
  formChips.forEach(c => { c.hidden = !view.forms; });
  els.empty.classList.toggle("show", shown === 0);
  if (openInfo && openInfo.e.el.hidden) closeInfo(false); // its Pokémon was filtered out
}

// Paint-bucket effect: marking caught fills the colour in as a circle growing from where you
// clicked; unmarking drains it back to that point. Runs on a copy of the art, so the real
// image just snaps to its new look underneath once the circle is done.
function preparePaint(e, ev, nowCaught) {
  if (reducedMotion || !settings.paintFx) return null;
  const box = e.el.querySelector(mode === "shiny" ? ".v.s" : ".v.n");
  const base = box && box.querySelector("img:not(.paint)");
  if (!base || box.classList.contains("noimg") || !base.complete || !base.naturalWidth) return null;
  box.querySelectorAll("img.paint").forEach(p => p.remove());
  // freeze the real image before its caught state changes: no fade of its own, and while
  // filling it keeps its old grey look under the growing colour
  const before = getComputedStyle(base);
  base.style.transition = "none";
  if (nowCaught) { base.style.filter = before.filter; base.style.opacity = before.opacity; }
  return () => {
    const r = base.getBoundingClientRect();
    const inside = ev && ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom;
    const x = inside ? ev.clientX - r.left : r.width / 2;
    const y = inside ? ev.clientY - r.top : r.height / 2;
    const reach = Math.hypot(Math.max(x, r.width - x), Math.max(y, r.height - y)) + 2;
    const paint = base.cloneNode();
    paint.className = "paint";
    paint.alt = "";
    paint.removeAttribute("loading");
    box.appendChild(paint);
    const small = `circle(0px at ${x}px ${y}px)`, full = `circle(${reach}px at ${x}px ${y}px)`;
    const anim = paint.animate({ clipPath: nowCaught ? [small, full] : [full, small] },
      { duration: nowCaught ? 420 : 300, easing: nowCaught ? "cubic-bezier(.22,.7,.3,1)" : "cubic-bezier(.55,0,.8,.45)", fill: "forwards" });
    let finished = false;
    const done = () => {
      if (finished) return;
      finished = true;
      base.style.filter = ""; base.style.opacity = "";
      void getComputedStyle(base).filter; // apply the new look while transitions are still off
      base.style.transition = "";
      paint.remove();
    };
    anim.finished.then(done, done);
    setTimeout(done, (nowCaught ? 420 : 300) + 250); // backstop if the browser pauses frames
  };
}

function toggle(e, ev) {
  const nowCaught = !caught.has(e.id);
  const paint = preparePaint(e, ev, nowCaught); // reads the current look before it changes
  if (nowCaught) caught.add(e.id); else { caught.delete(e.id); dropOt([e.id]); }
  paintCard(e);
  if (paint) paint();
  if (nowCaught) {
    e.el.classList.remove("pop");
    void e.el.offsetWidth;
    e.el.classList.add("pop");
  }
  updateCounts();
  save();
  // Cards stay in place until the next filter change so a mis-click is easy to undo.
}
