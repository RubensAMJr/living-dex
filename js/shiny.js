// Regular / shiny dex switch and its transition.

const shinyBtn = document.getElementById("shinyBtn");
// Which cards are on (or near) the screen: those switch in the same frame as the click
const onScreen = new Set();
const io = new IntersectionObserver(list => {
  for (const it of list) { if (it.isIntersecting) onScreen.add(it.target); else onScreen.delete(it.target); }
}, { rootMargin: "300px 0px" });
entries.forEach(e => io.observe(e.el));
const themedRoots = [document.querySelector("header"), ...document.querySelectorAll(".sec-head"),
                     document.getElementById("formsDivider"), document.getElementById("toast"),
                     document.getElementById("selbar"), document.getElementById("marquee")];
const idle = window.requestIdleCallback || (cb => setTimeout(() => cb({ timeRemaining: () => 8 }), 16));

function themeCards(all) {
  const shiny = mode === "shiny";
  const later = [];
  for (const e of entries) {
    if (all || onScreen.has(e.el)) e.el.classList.toggle("t-shiny", shiny);
    else later.push(e.el);
  }
  // the off-screen rest follow in small batches while the browser is idle
  let i = 0;
  const step = deadline => {
    const want = mode === "shiny";
    while (i < later.length && deadline.timeRemaining() > 2) later[i++].classList.toggle("t-shiny", want);
    if (i < later.length) idle(step, { timeout: 500 });
  };
  if (later.length) idle(step, { timeout: 500 });
}

function applyMode(all = false) {
  const shiny = mode === "shiny";
  themedRoots.forEach(el => el.classList.toggle("t-shiny", shiny));
  themeCards(all);
  shinyBtn.setAttribute("aria-pressed", shiny ? "true" : "false");
  shinyBtn.title = shiny ? "Back to the regular dex" : "Switch to the shiny dex";
  document.getElementById("title").innerHTML = shiny ? "Shiny <span>Living Dex</span>" : "Living Dex <span>Checklist</span>";
  document.title = shiny ? "Shiny Living Dex" : "Living Dex Checklist";
  document.getElementById("resetBtn").textContent = shiny ? "Clear shiny dex (nothing caught)" : "Clear regular dex (nothing caught)";
  caught = sets[mode];
  entries.forEach(paintCard);
  updateCounts();
  applyFilters();
  if (openInfo) openInfo.tile.classList.toggle("t-shiny", shiny);
  updateShinyNote();
  refreshGames();
}
// the note about slow shiny art: shiny mode only, and gone for good once closed with ×
const SHINY_NOTE_KEY = "living-dex-shiny-note-hidden";
const shinyNote = document.getElementById("shinyNote");
function updateShinyNote() {
  let closed = false;
  try { closed = localStorage.getItem(SHINY_NOTE_KEY) === "1"; } catch (e) {}
  shinyNote.hidden = mode !== "shiny" || closed;
}
shinyNote.querySelector("button").addEventListener("click", () => {
  try { localStorage.setItem(SHINY_NOTE_KEY, "1"); } catch (e) {}
  shinyNote.hidden = true;
});

// ---------- shiny transition ----------
// Snappy: the dex crossfades at once (both artworks are already loaded), a light sweep crosses
// the screen and a burst of ✨ flies out from the centre (about 0.7 s in total).
let animating = false;
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

// Draw the ✨ (with its glow) into an image once, ahead of the first click
function prepareSpark() {
  const size = 128;
  const c = document.createElement("canvas");
  c.width = c.height = size;
  const g = c.getContext("2d");
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.font = `${Math.round(size * 0.6)}px "Segoe UI Emoji", "Apple Color Emoji", "Noto Color Emoji", sans-serif`;
  g.shadowColor = "rgba(255,230,140,.95)";
  g.shadowBlur = 16;
  g.fillText("✨", size / 2, size / 2 + size * 0.04);
  const url = c.toDataURL("image/png");
  const warm = new Image();
  warm.src = url;
  (warm.decode ? warm.decode() : Promise.resolve()).catch(() => {}).then(() => {
    document.documentElement.style.setProperty("--spark", `url("${url}")`);
  });
}

function burst(fx, x, y, count, reach, sizeMin, sizeMax) {
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2 + (Math.random() - .5) * .5;
    const d = reach * (0.55 + Math.random() * 0.45);
    const s = document.createElement("span");
    s.className = "spark";
    s.style.cssText = `--x:${x}px;--y:${y}px;--dx:${(Math.cos(a) * d).toFixed(1)}px;--dy:${(Math.sin(a) * d).toFixed(1)}px;` +
      `--size:${(sizeMin + Math.random() * (sizeMax - sizeMin)).toFixed(1)}px;--s:${(0.7 + Math.random() * 0.6).toFixed(2)};` +
      `--rot:${((Math.random() - .5) * 160).toFixed(0)}deg;--dur:${(520 + Math.random() * 240).toFixed(0)}ms;--delay:${(Math.random() * 90).toFixed(0)}ms`;
    fx.appendChild(s);
  }
}

function playTransition(toShiny, swap) {
  if (animating) return;
  animating = true;
  swap();
  if (reducedMotion || !settings.shinyFx) { animating = false; return; }

  shinyBtn.classList.remove("pop");
  void shinyBtn.offsetWidth;
  shinyBtn.classList.add("pop");

  const fx = document.createElement("div");
  fx.className = "fx";
  fx.style.setProperty("--glow", toShiny ? "79,180,255" : "121,176,82");
  fx.innerHTML = '<div class="flash"></div><div class="sweep"></div>';
  if (toShiny) {
    const W = window.innerWidth, H = window.innerHeight;
    const phone = W < 600; // fewer, smaller sparks on small screens
    burst(fx, W / 2, H / 2, phone ? 14 : 22, Math.hypot(W, H) * 0.42, phone ? 14 : 18, phone ? 30 : 40);
    const r = shinyBtn.getBoundingClientRect();
    burst(fx, r.left + r.width / 2, r.top + r.height / 2, phone ? 6 : 8, phone ? 50 : 70, 12, 20);
  }
  document.body.appendChild(fx);
  setTimeout(() => { fx.remove(); animating = false; }, 900);
}

shinyBtn.addEventListener("click", () => {
  if (animating) return;
  const next = mode === "shiny" ? "normal" : "shiny";
  playTransition(next === "shiny", () => {
    mode = next;
    applyMode();
    save();
    // stay where you are: the Pokémon on screen just turn shiny (or back) in place
  });
});
