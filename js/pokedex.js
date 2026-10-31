// The Pokédex tile opened from a card: weaknesses, games, evolutions, stats, abilities.

// The ⓘ button turns the card into a wide tile (card + info panel); the cards around it slide
// out of the way. Data comes from data/info-data.js (types + where each Pokémon is found per game).
const TYPES = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", "poison", "ground",
               "flying", "psychic", "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"];
const TYPE_COLOR = { normal: "#9fa19f", fire: "#e62829", water: "#2980ef", electric: "#d9b100", grass: "#3fa129",
  ice: "#3dcef3", fighting: "#ff8000", poison: "#9141cb", ground: "#915121", flying: "#81b9ef", psychic: "#ef4179",
  bug: "#91a119", rock: "#afa981", ghost: "#704170", dragon: "#5060e1", dark: "#624d4e", steel: "#60a1b8", fairy: "#ef70ef" };
// attacking type -> [super effective against, not very effective against, no effect on]
const CHART = {
  normal: [[], ["rock", "steel"], ["ghost"]],
  fire: [["grass", "ice", "bug", "steel"], ["fire", "water", "rock", "dragon"], []],
  water: [["fire", "ground", "rock"], ["water", "grass", "dragon"], []],
  electric: [["water", "flying"], ["electric", "grass", "dragon"], ["ground"]],
  grass: [["water", "ground", "rock"], ["fire", "grass", "poison", "flying", "bug", "dragon", "steel"], []],
  ice: [["grass", "ground", "flying", "dragon"], ["fire", "water", "ice", "steel"], []],
  fighting: [["normal", "ice", "rock", "dark", "steel"], ["poison", "flying", "psychic", "bug", "fairy"], ["ghost"]],
  poison: [["grass", "fairy"], ["poison", "ground", "rock", "ghost"], ["steel"]],
  ground: [["fire", "electric", "poison", "rock", "steel"], ["grass", "bug"], ["flying"]],
  flying: [["grass", "fighting", "bug"], ["electric", "rock", "steel"], []],
  psychic: [["fighting", "poison"], ["psychic", "steel"], ["dark"]],
  bug: [["grass", "psychic", "dark"], ["fire", "fighting", "poison", "flying", "ghost", "steel", "fairy"], []],
  rock: [["fire", "ice", "flying", "bug"], ["fighting", "ground", "steel"], []],
  ghost: [["psychic", "ghost"], ["dark"], ["normal"]],
  dragon: [["dragon"], ["steel"], ["fairy"]],
  dark: [["psychic", "ghost"], ["fighting", "dark", "fairy"], []],
  steel: [["ice", "rock", "fairy"], ["fire", "water", "electric", "steel"], []],
  fairy: [["fighting", "dragon", "dark"], ["fire", "poison", "steel"], []],
};
function damageTaken(types) {
  return TYPES.map(att => {
    const [se, nve, none] = CHART[att];
    return types.reduce((m, def) => m * (none.includes(def) ? 0 : se.includes(def) ? 2 : nve.includes(def) ? 0.5 : 1), 1);
  });
}
// every mainline game, one badge per version: [id, badge text, full name, colour, text colour]
const GAMES = [
  ["I", [["red", "R", "Red", "#d8352a"], ["blue", "B", "Blue", "#2d5fc4"], ["yellow", "Y", "Yellow", "#f2c518", "#2a2200"]]],
  ["II", [["gold", "G", "Gold", "#c9a227", "#2a2000"], ["silver", "S", "Silver", "#aab4bf", "#1d2228"], ["crystal", "C", "Crystal", "#4fb3d9", "#0b2530"]]],
  ["III", [["ruby", "R", "Ruby", "#c4182f"], ["sapphire", "S", "Sapphire", "#2350b5"], ["emerald", "E", "Emerald", "#169a48"],
           ["firered", "FR", "FireRed", "#ee5a24"], ["leafgreen", "LG", "LeafGreen", "#5cb83f", "#102a08"]]],
  ["IV", [["diamond", "D", "Diamond", "#6f9fdd", "#0d1f38"], ["pearl", "P", "Pearl", "#d79ac0", "#3a1630"], ["platinum", "Pt", "Platinum", "#8c8c8c"],
          ["heartgold", "HG", "HeartGold", "#d3a82a", "#2a2000"], ["soulsilver", "SS", "SoulSilver", "#a7b6c6", "#1d2228"]]],
  ["V", [["black", "B", "Black", "#202020"], ["white", "W", "White", "#e6e6e6", "#202020"],
         ["black-2", "B2", "Black 2", "#2b3540"], ["white-2", "W2", "White 2", "#d9e2ea", "#202020"]]],
  ["VI", [["x", "X", "X", "#2058c9"], ["y", "Y", "Y", "#cf2b2b"], ["omega-ruby", "OR", "Omega Ruby", "#b3132a"], ["alpha-sapphire", "AS", "Alpha Sapphire", "#1c4aa8"]]],
  ["VII", [["sun", "S", "Sun", "#f29a1d", "#2a1600"], ["moon", "M", "Moon", "#6a4fb5"], ["ultra-sun", "US", "Ultra Sun", "#e8701a"],
           ["ultra-moon", "UM", "Ultra Moon", "#7b3fb0"], ["lets-go-pikachu", "LGP", "Let's Go, Pikachu!", "#f3cf2a", "#2a2200"],
           ["lets-go-eevee", "LGE", "Let's Go, Eevee!", "#a86a3a"]]],
  ["VIII", [["sword", "Sw", "Sword", "#139bd8"], ["shield", "Sh", "Shield", "#d4127a"], ["brilliant-diamond", "BD", "Brilliant Diamond", "#3f7bc4"],
            ["shining-pearl", "SP", "Shining Pearl", "#cf78ad"], ["legends-arceus", "LA", "Legends: Arceus", "#5f7f69"]]],
  ["IX", [["scarlet", "S", "Scarlet", "#d3221c"], ["violet", "V", "Violet", "#7a37a3"], ["legends-za", "Z-A", "Legends: Z-A", "#2fae9c", "#06241f"]]],
];
const GAME_BY_ID = new Map(GAMES.flatMap(([, list]) => list.map(g => [g[0], g])));
const typePill = t => `<span class="type" style="--tc:${TYPE_COLOR[t]}">${t[0].toUpperCase() + t.slice(1)}</span>`;

// Base stats as bars (scaled to 255, coloured by value like Serebii/PokémonDB) and the abilities
const STAT_NAMES = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"];
const statColor = v => v < 50 ? "#e0533e" : v < 70 ? "#f08a3c" : v < 90 ? "#f2c23a" : v < 110 ? "#a6d14a" : v < 130 ? "#4fbf5f" : "#2fb3a3";
function statsAbilitiesHtml(info) {
  const abilities = window.DEX_ABILITIES || {};
  const s = info.s || [];
  const total = s.reduce((a, b) => a + b, 0);
  const stats = s.length ? STAT_NAMES.map((k, i) =>
      `<span class="k">${k}</span><span class="v">${s[i]}</span><span class="bar"><i style="width:${Math.min(100, s[i] / 2.55).toFixed(1)}%;--sc:${statColor(s[i])}"></i></span>`).join("") +
      `<span class="k total">Total</span><span class="v total">${total}</span><span></span>`
    : "";
  const abil = (info.a || []).map(([id, hidden]) => {
    const [name, text] = abilities[id] || [`Ability ${id}`, ""];
    return `<div><dt>${esc(name)}${hidden ? `<span class="hid">Hidden</span>` : ""}</dt><dd>${esc(text)}</dd></div>`;
  }).join("");
  return `<div class="duo"><section><h4>Base stats</h4><div class="stats">${stats}</div></section>` +
         `<section><h4>Abilities</h4><dl class="abilities">${abil || "<dd>Unknown</dd>"}</dl></section></div>`;
}

// "Evolves from" / "Evolves into" lines; each Pokémon name opens its own panel
function evolutionHtml(info) {
  const ev = info.e || {};
  const name = id => {
    const x = byId.get(id);
    return x ? `<button type="button" class="evo-link" data-id="${esc(id)}">${esc(x.label)}</button>` : esc(id);
  };
  const line = list => list.map(([id, how]) => `${name(id)} <span class="how">— ${esc(how)}</span>`).join("<br>");
  const rows = [ev.f && ev.f.length && `<dt>From</dt><dd>${line(ev.f)}</dd>`,
                ev.i && ev.i.length && `<dt>Into</dt><dd>${line(ev.i)}</dd>`].filter(Boolean);
  return `<section><h4>Evolution</h4>` +
    (rows.length ? `<dl class="evo">${rows.join("")}</dl>` : `<p class="weak-sum">Does not evolve.</p>`) + `</section>`;
}

function infoHtml(e, info) {
  const dmg = damageTaken(info.t);
  const fmt = m => m === 0.5 ? "½" : m === 0.25 ? "¼" : String(m);
  const cls = m => ({ 0: "x0", 0.25: "xq", 0.5: "xh", 1: "x1", 2: "x2", 4: "x4" })[m];
  const named = list => list.map(i => TYPES[i][0].toUpperCase() + TYPES[i].slice(1)).join(", ");
  const idx = test => dmg.map((m, i) => test(m) ? i : -1).filter(i => i >= 0);
  const weak4 = idx(m => m === 4), weak2 = idx(m => m === 2), resist = idx(m => m > 0 && m < 1), immune = idx(m => m === 0);
  const sum = [weak4.length && `<b>4× weak</b> to ${named(weak4)}`, weak2.length && `<b>Weak</b> to ${named(weak2)}`,
               resist.length && `<b>Resists</b> ${named(resist)}`, immune.length && `<b>Immune</b> to ${named(immune)}`].filter(Boolean).join(" · ");
  const found = (info.f || []).length, byEvo = (info.v || []).length;
  const total = GAMES.reduce((n, [, list]) => n + list.length, 0);
  return `<div class="info-head"><span class="info-num">#${pad(e.dex)}</span><h3>${esc(e.label)}</h3>` +
    `<div class="types">${info.t.map(typePill).join("")}</div>` +
    `<button type="button" class="info-close" aria-label="Close">×</button></div>` +
    evolutionHtml(info) + statsAbilitiesHtml(info) +
    `<section><h4>Weaknesses</h4><p class="weak-sum">${sum}</p><div class="dmg">` +
    TYPES.map((t, i) => `<div class="dmg-cell ${cls(dmg[i])}" title="${t[0].toUpperCase() + t.slice(1)} moves: ×${fmt(dmg[i])}">${typePill(t)}<b>×${fmt(dmg[i])}</b></div>`).join("") +
    `</div></section>` +
    `<section><h4>Where to find it <small>found in ${found} of ${total} games${byEvo ? ` · ${byEvo} more by evolving` : ""}</small></h4><div class="games">` +
    GAMES.map(([gen, list]) => `<div class="gen"><span class="gen-label">Gen ${gen}</span><div class="gen-games">` + list.map(([id, abbr, name, color, ink]) => {
      const state = gameState(info, id);
      return `<button type="button" class="game${state === "found" ? "" : state === "evolve" ? " evo" : " miss"}" data-game="${id}" aria-pressed="false" title="${esc(name)}"` +
        (state !== "miss" ? ` style="--gc:${color};--gi:${ink || "#fff"}"` : "") + `>${abbr}</button>`;
    }).join("") + `</div></div>`).join("") +
    `</div><div class="games-legend"><span class="l-found">Found (wild or gift)</span><span class="l-evo">By evolving</span><span class="l-miss">Not obtainable</span></div>` +
    `<p class="game-detail" aria-live="polite">Hover or tap a game to see where to find ${esc(e.label)}.</p></section>`;
}
const DEX_GAMES = window.DEX_GAMES || [];
// "Open <game> map" under a badge's detail: the game page with that Pokémon highlighted
const mapLink = (id, name, eid, label) =>
  `<br><a class="game-open" href="#game/${id}?p=${encodeURIComponent(eid)}">Open ${esc(name)} map${label ? ` (${esc(label)})` : ""} →</a>`;
const gameIndex = id => DEX_GAMES.indexOf(id);
function gameState(info, id) {
  const gi = gameIndex(id);
  return (info.f || []).includes(gi) ? "found" : (info.v || []).includes(gi) ? "evolve" : "miss";
}
// nearest pre-evolution found in that game, and the steps from it: [[id, method], ...]
function evolveSteps(eid, gi, seen = new Set()) {
  const ev = (DEX_INFO[eid] || {}).e;
  for (const [parent, how] of (ev && ev.f) || []) {
    if (seen.has(parent)) continue;
    seen.add(parent);
    if ((DEX_INFO[parent] && DEX_INFO[parent].f || []).includes(gi)) return [[parent, how]];
    const deeper = evolveSteps(parent, gi, seen);
    if (deeper) return [...deeper, [parent, how]];
  }
  return null;
}
// location details live in data/info-places.js, loaded the first time you look at a game
let placesLoading = null;
function loadPlaces() {
  if (window.DEX_PLACES) return Promise.resolve();
  if (!placesLoading) placesLoading = new Promise(resolve => {
    const s = document.createElement("script");
    s.src = "data/info-places.js";
    s.onload = s.onerror = () => resolve();
    document.head.appendChild(s);
  });
  return placesLoading;
}
function gameDetail(e, info, id) {
  const [, , name] = GAME_BY_ID.get(id);
  const gi = gameIndex(id);
  const state = gameState(info, id);
  if (state === "found") {
    if (!window.DEX_PLACES) return `<b>${esc(name)}</b>: loading…`;
    const row = (window.DEX_PLACES.d[e.id] || []).find(r => r[0] === gi);
    return `<b>${esc(name)}</b>: ` + (row ? esc(window.DEX_PLACES.s[row[1]]) : "found in this game.") + mapLink(id, name, e.id);
  }
  if (state === "evolve") {
    const steps = evolveSteps(e.id, gi) || [];
    const chain = steps.map(([pid, how], i) => {
      const x = byId.get(pid);
      return (i === 0 ? `Evolve ${esc(x ? x.label : pid)}` : `then ${esc(x ? x.label : pid)}`) + ` (${esc(how)})`;
    }).join(", ");
    const from = steps.length && byId.get(steps[0][0]);   // the map then highlights the Pokémon to evolve
    return `<b>${esc(name)}</b>: not found in the wild or as a gift. ${chain || "Obtainable by evolving."}` +
      (from ? mapLink(id, name, from.id, `where ${from.label} is`) : "");
  }
  // Serebii's own wording when it gave one (e.g. "Trade from X & Y")
  const why = info.n && info.n[gi];
  return `<b>${esc(name)}</b>: not obtainable in this game` + (why ? ` (${esc(why)}).` : " (trade or transfer only, or not in this game).");
}

let openInfo = null; // { e, tile, info, onResize }

function gridColumns(grid) {
  return getComputedStyle(grid).gridTemplateColumns.split(" ").filter(Boolean).length;
}
// size the tile: card + panel across up to 6 columns, tall enough for the panel's content
function layoutTile() {
  if (!openInfo) return;
  const { tile, e, info } = openInfo;
  const grid = tile.parentNode;
  const cols = gridColumns(grid);
  const span = cols >= 6 ? 6 : cols;
  const colW = e.el.offsetWidth;
  tile.style.setProperty("--cw", `${colW}px`);
  tile.style.gridColumn = `span ${span}`;
  tile.classList.toggle("stack", span * (colW + 8) < 520); // narrow: panel goes under the card
  // measure the panel at its natural height (not stretched to fill the tile)
  tile.style.gridRow = "span 1";
  info.style.alignSelf = "start";
  const contentH = info.offsetHeight;
  info.style.alignSelf = "";
  const gap = parseFloat(getComputedStyle(grid).rowGap) || 8;
  const rowH = e.el.offsetHeight;
  const need = tile.classList.contains("stack") ? rowH + gap + contentH : Math.max(rowH, contentH);
  tile.style.gridRow = `span ${Math.max(1, Math.ceil((need + gap) / (rowH + gap)))}`;
}
// FLIP: remember where the nearby cards are, change the layout, then slide them from old to new spots
function animateLayout(grid, change) {
  const vh = window.innerHeight;
  const items = [...grid.children].filter(el => !el.hidden);
  const before = new Map();
  for (const el of items) {
    const r = el.getBoundingClientRect();
    if (r.bottom > -200 && r.top < vh + 200) before.set(el, r);
  }
  change();
  if (reducedMotion) return;
  for (const el of [...grid.children, ...grid.querySelectorAll(".tile > .card")]) {
    const a = before.get(el);
    if (!a || el.hidden) continue;
    const b = el.getBoundingClientRect();
    const dx = a.left - b.left, dy = a.top - b.top;
    if (Math.abs(dx) < 1 && Math.abs(dy) < 1) continue;
    el.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }],
               { duration: 320, easing: "cubic-bezier(.2,.75,.25,1)" });
  }
}
function openInfoFor(e) {
  const info = DEX_INFO[e.id];
  if (!info) return;
  const grid = e.el.parentNode;
  animateLayout(grid, () => {
    const tile = document.createElement("div");
    tile.className = "tile" + (mode === "shiny" ? " t-shiny" : "");
    const panel = document.createElement("div");
    panel.className = "info";
    panel.setAttribute("role", "region");
    panel.setAttribute("aria-label", `${e.label} details`);
    panel.innerHTML = infoHtml(e, info);
    e.el.replaceWith(tile);
    tile.append(e.el, panel);
    e.el.classList.add("open");
    openInfo = { e, tile, info: panel };
    layoutTile();
  });
  const { info: panel } = openInfo;
  if (!reducedMotion) panel.animate([{ opacity: 0, transform: "translateY(6px) scale(.98)" }, { opacity: 1, transform: "none" }],
                                    { duration: 260, easing: "ease-out" });
  const show = btn => {
    panel.querySelectorAll('.game[aria-pressed="true"]').forEach(b => b.setAttribute("aria-pressed", "false"));
    btn.setAttribute("aria-pressed", "true");
    const detail = panel.querySelector(".game-detail");
    detail.innerHTML = gameDetail(e, info, btn.dataset.game);
    if (!window.DEX_PLACES) loadPlaces().then(() => {
      if (btn.getAttribute("aria-pressed") === "true") detail.innerHTML = gameDetail(e, info, btn.dataset.game);
    });
  };
  panel.addEventListener("click", ev => {
    const g = ev.target.closest(".game");
    if (g) show(g);
    const link = ev.target.closest(".evo-link");
    if (link) {
      const target = byId.get(link.dataset.id);
      if (target && target.el && !target.el.hidden) {
        toggleInfo(target);
        target.el.scrollIntoView({ block: "center", behavior: reducedMotion ? "auto" : "smooth" });
      } else toast(`${target ? target.label : "That Pokémon"} is hidden by the current filters`);
    }
    if (ev.target.closest(".info-close")) closeInfo();
  });
  panel.addEventListener("pointerover", ev => { const g = ev.target.closest(".game"); if (g && ev.pointerType === "mouse") show(g); });
  panel.addEventListener("focusin", ev => { const g = ev.target.closest(".game"); if (g) show(g); });
  // keep the tile inside the screen if it opened near the bottom
  const r = openInfo.tile.getBoundingClientRect();
  if (r.bottom > window.innerHeight) window.scrollBy({ top: r.bottom - window.innerHeight + 16, behavior: reducedMotion ? "auto" : "smooth" });
}
function closeInfo(animate = true) {
  if (!openInfo) return;
  const { e, tile } = openInfo;
  const grid = tile.parentNode;
  const undo = () => { e.el.classList.remove("open"); tile.replaceWith(e.el); };
  openInfo = null;
  if (animate) animateLayout(grid, undo); else undo();
}
function toggleInfo(e) {
  const same = openInfo && openInfo.e === e;
  if (openInfo) closeInfo();
  if (!same) openInfoFor(e);
}
let tileResizeTimer;
window.addEventListener("resize", () => { clearTimeout(tileResizeTimer); tileResizeTimer = setTimeout(layoutTile, 120); });
// clicking empty space closes the tile
document.addEventListener("click", ev => {
  if (openInfo && !ev.target.closest(".tile, .card, header, .selbar, .menu")) closeInfo();
});
