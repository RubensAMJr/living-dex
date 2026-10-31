// Game pages (#games, #game/<id>/<place>): picker, places, Pokémon per place.

const gameView = document.getElementById("gameView");
const ALL_GAMES = GAMES.flatMap(([gen, list]) => list.map(([id, abbr, name, color, ink]) => ({ id, abbr, name, color, ink: ink || "#fff", gen })));
const slugify = s => fold(s).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const catchableIn = id => { const gi = gameIndex(id); return entries.filter(e => ((DEX_INFO[e.id] || {}).f || []).includes(gi)); };
const TIME_ICON = { Morning: "🌅", Day: "☀️", Night: "🌙", Spring: "🌸", Summer: "🌻", Autumn: "🍂", Winter: "❄️" };
const gv = { onlyMissing: false, dexY: 0, token: 0 };
try { gv.onlyMissing = localStorage.getItem("living-dex-games-missing") === "1"; } catch (e) {}

const locLoading = {};
function loadLocations(id) {
  if (window.DEX_LOC && window.DEX_LOC[id]) return Promise.resolve(window.DEX_LOC[id]);
  if (!locLoading[id]) locLoading[id] = new Promise(resolve => {
    const s = document.createElement("script");
    s.src = `data/locations/${id}.js`;
    s.onload = s.onerror = () => resolve(window.DEX_LOC && window.DEX_LOC[id]);
    document.head.appendChild(s);
  });
  return locLoading[id];
}

// Each game's icon from Bulbagarden Archives (Category:Game icons): the DS/3DS/Switch home-menu icons, and the
// 3DS Virtual Console ones for the Game Boy games. The GBA games never had one: theirs are Viator_'s custom HD
// icons from SteamGridDB (based on EuroBeat's), kept in icons/.
const ICON_BASE = "https://archives.bulbagarden.net/media/upload/";
const iconUrl = path => path.startsWith("icons/") ? path : ICON_BASE + path;
const GAME_ICON = {
  ruby: "icons/ruby.png", sapphire: "icons/sapphire.png", emerald: "icons/emerald.png",
  firered: "icons/firered.png", leafgreen: "icons/leafgreen.png",
  red: "8/87/Red_VC_icon.png", blue: "9/90/Blue_VC_icon.png", yellow: "4/44/Yellow_VC_icon.png",
  gold: "1/13/Gold_VC_icon.png", silver: "c/c1/Silver_VC_icon.png", crystal: "6/64/Crystal_VC_icon.png",
  diamond: "5/5c/Diamond_icon.png", pearl: "f/fb/Pearl_icon.png", platinum: "4/49/Platinum_icon.png",
  heartgold: "c/c9/HeartGold_Icon.png", soulsilver: "2/2e/SoulSilver_Icon.png",
  black: "e/e4/Black_Icon.png", white: "4/4e/White_Icon.png", "black-2": "b/b0/Black_2_Icon.png", "white-2": "1/17/White_2_Icon.png",
  x: "4/43/X_icon.png", y: "2/2f/Y_icon.png", "omega-ruby": "0/0f/Omega_Ruby_icon.png", "alpha-sapphire": "3/3b/Alpha_Sapphire_icon.png",
  sun: "d/d5/Sun_icon.png", moon: "e/ed/Moon_icon.png", "ultra-sun": "b/b5/Ultra_Sun_icon.png", "ultra-moon": "e/e9/Ultra_Moon_icon.png",
  "lets-go-pikachu": "thumb/c/c2/Let%27s_Go_Pikachu_Icon.jpg/120px-Let%27s_Go_Pikachu_Icon.jpg",
  "lets-go-eevee": "thumb/8/83/Let%27s_Go_Eevee_Icon.jpg/120px-Let%27s_Go_Eevee_Icon.jpg",
  sword: "thumb/a/ac/Sword_Icon.jpg/120px-Sword_Icon.jpg", shield: "thumb/f/f1/Shield_Icon.jpg/120px-Shield_Icon.jpg",
  "brilliant-diamond": "thumb/2/2f/Brilliant_Diamond_Icon.jpg/120px-Brilliant_Diamond_Icon.jpg",
  "shining-pearl": "thumb/3/3b/Shining_Pearl_Icon.jpg/120px-Shining_Pearl_Icon.jpg",
  "legends-arceus": "thumb/7/70/Legends_Arceus_Icon.jpg/120px-Legends_Arceus_Icon.jpg",
  scarlet: "thumb/f/f3/Scarlet_Icon.jpg/120px-Scarlet_Icon.jpg", violet: "thumb/5/53/Violet_Icon.jpg/120px-Violet_Icon.jpg",
  "legends-za": "thumb/b/be/Legends_Z-A_Icon.jpg/120px-Legends_Z-A_Icon.jpg",
};
// the coloured letters, with the icon on top (see iconFailed below if it can't load)
function gameBadge(id, abbr, ink) {
  const icon = GAME_ICON[id];
  return `<span class="gv-abbr${icon ? " icon" : ""}" style="--gi:${ink}">${esc(abbr)}` +
    (icon ? `<img src="${iconUrl(icon)}" alt="" class="${icon.endsWith(".png") && !icon.startsWith("icons/") ? "px" : ""}" ` +
            `referrerpolicy="no-referrer">` : "") + `</span>`;
}
// Bulbagarden sometimes fails a request (its bot check): try the icon once more a few seconds later, often from
// the image cache by then; if that fails too, the letters underneath show instead
function iconFailed(img) {
  if (!img.dataset.retried) {
    const url = img.src;
    img.dataset.retried = "1";
    img.removeAttribute("src");
    setTimeout(() => { if (img.isConnected) img.src = url; }, 3000);
    return;
  }
  img.parentNode.classList.remove("icon");
  img.remove();
}

function gvBar(crumbs) {
  return `<div class="gv-bar"><a class="gv-back" href="#">← Dex</a><nav class="gv-crumbs" aria-label="You are here">` +
    crumbs.map(([label, href], i) => i ? `<span>${href ? `<a href="${href}">${esc(label)}</a>` : esc(label)}</span>`
                                       : (href ? `<a href="${href}">${esc(label)}</a>` : esc(label))).join("") + `</nav></div>`;
}

function renderPicker() {
  gameView.style.removeProperty("--gc");
  gameView.innerHTML = gvBar([["Games"]]) +
    `<p class="gv-lead">Pick a game to see its regions and places, and every Pokémon you can catch in each one.</p>` +
    GAMES.map(([gen, list]) => `<section class="gv-gen"><h3>Generation ${gen}</h3><div class="gv-games">` +
      list.map(([id, abbr, name, color, ink]) => {
        const all = catchableIn(id), miss = all.filter(e => !caught.has(e.id)).length;
        return `<a class="gv-game" href="#game/${id}" style="--gc:${color};--gi:${ink || "#fff"}">${gameBadge(id, abbr, ink || "#fff")}` +
               `<span class="gv-name">${esc(name)}</span><span class="gv-meta">${all.length} catchable · <b>${miss}</b> missing</span></a>`;
      }).join("") + `</div></section>`).join("");
}

// one Pokémon per method group: rows for the same Pokémon (day/night, swarm, ...) are merged
function mergeRows(rows) {
  const by = new Map();
  for (const [eid, lv, rarity, times, note] of rows) {
    if (!byId.has(eid)) continue;
    const m = by.get(eid) || { eid, lv: [], rarity: [], times: new Set(), notes: new Set() };
    for (const n of String(lv).match(/\d+/g) || []) m.lv.push(+n);
    if (rarity && !m.rarity.includes(rarity)) m.rarity.push(rarity);
    times.forEach(t => m.times.add(t));
    if (note) m.notes.add(note);
    by.set(eid, m);
  }
  return [...by.values()];
}

function monHtml(m, focus) {
  const e = byId.get(m.eid);
  const lv = m.lv.length ? (Math.min(...m.lv) === Math.max(...m.lv) ? `Lv ${m.lv[0]}` : `Lv ${Math.min(...m.lv)}–${Math.max(...m.lv)}`) : "";
  const times = [...m.times].map(t => TIME_ICON[t] ? `<span title="${esc(t)}">${TIME_ICON[t]}</span>` : esc(t)).join(" ");
  const src = e.srcs[mode][0];
  return `<button type="button" class="gv-mon${caught.has(e.id) ? " have" : ""}${focus === e.id ? " hl" : ""}" data-id="${esc(e.id)}" ` +
    `title="${esc(e.label)}: click to mark ${caught.has(e.id) ? "missing" : "caught"}">` +
    `<img src="${esc(src)}" data-i="0" alt="" loading="lazy" referrerpolicy="no-referrer" width="56" height="56">` +
    `<b>${esc(e.label)}<i>#${pad(e.dex)}</i></b><span>${[lv, m.rarity.join(" / ")].filter(Boolean).join(" · ")} ${times}</span>` +
    `<span class="gv-note">${esc([...m.notes].join(" · "))}</span></button>`;
}

async function renderGame(id, placeSlug, pick) {
  const g = ALL_GAMES.find(x => x.id === id);
  if (!g) { location.replace("#games"); return; }
  const token = ++gv.token;
  gameView.style.setProperty("--gc", g.color);
  gameView.innerHTML = gvBar([["Games", "#games"], [g.name]]) + `<p class="gv-lead">Loading ${esc(g.name)}…</p>`;
  const data = await loadLocations(id);
  if (token !== gv.token) return; // another page was opened meanwhile
  if (!data) { gameView.innerHTML = gvBar([["Games", "#games"], [g.name]]) + `<p class="gv-empty">No route data for ${esc(g.name)} yet.</p>`; return; }
  if (!data.places) {
    data.places = data.regions.flatMap(([region, list]) => list.map(([name, groups]) => ({
      region, name, slug: slugify(`${region} ${name}`),
      groups: groups.map(([area, method, rows]) => ({ area, method, mons: mergeRows(rows) })).filter(x => x.mons.length) })))
      .filter(p => p.groups.length);
    data.places.forEach(p => { p.ids = new Set(p.groups.flatMap(x => x.mons.map(m => m.eid))); });
  }
  const focus = pick && byId.has(pick) ? pick : "";
  const focusPlaces = focus ? data.places.filter(p => p.ids.has(focus)) : [];
  const place = data.places.find(p => p.slug === placeSlug) || focusPlaces[0] || data.places[0];
  const q = focus ? `?p=${encodeURIComponent(focus)}` : "";
  const all = catchableIn(id), miss = all.filter(e => !caught.has(e.id)).length;
  const missIn = p => [...p.ids].filter(eid => !caught.has(eid)).length;

  let side = "", region = "";
  for (const p of data.places) {
    if (p.region !== region) { region = p.region; side += `<h5 class="gv-region">${esc(region)}</h5>`; }
    const n = missIn(p);
    side += `<a class="gv-pl${focus && !p.ids.has(focus) ? " dim" : ""}" href="#game/${id}/${p.slug}${q}" data-name="${esc(fold(p.name))}"` +
            `${p === place ? ` aria-current="page"` : ""}>${esc(p.name)}<small class="${n ? "miss" : ""}" title="${n} missing">${n || "✓"}</small></a>`;
  }
  const groups = place.groups.map(x => {
    const have = x.mons.every(m => caught.has(m.eid));
    return `<div class="gv-group${have ? " all-have" : ""}"><h4>${esc(x.method)}${x.area ? `<small>${esc(x.area)}</small>` : ""}</h4>` +
           `<div class="gv-mons">${x.mons.map(m => monHtml(m, focus)).join("")}</div></div>`;
  }).join("");
  const focusE = focus && byId.get(focus);

  gameView.innerHTML = gvBar([["Games", "#games"], [g.name, `#game/${id}`], [place.region], [place.name]]) +
    `<div class="gv-head">${gameBadge(id, g.abbr, g.ink)}<div><h2>${esc(g.name)}</h2>` +
    `<span class="gv-meta">${data.places.length} places · ${all.length} catchable · <b>${miss}</b> missing in your ${dexName()}</span></div>` +
    `<label class="toggle"><input type="checkbox" id="gvMissing"${gv.onlyMissing ? " checked" : ""}> Only missing</label></div>` +
    (focusE ? `<div class="gv-focus">Showing where <b>${esc(focusE.label)}</b> is: ${focusPlaces.length} place${focusPlaces.length === 1 ? "" : "s"} in ${esc(g.name)}` +
              `<a href="#game/${id}/${place.slug}">Clear highlight</a></div>` : "") +
    `<div class="gv-body"><aside class="gv-side"><button type="button" class="gv-side-btn" aria-expanded="false">${esc(place.name)}<span>Places ▾</span></button>` +
    `<input class="gv-find" type="search" placeholder="Find a place" aria-label="Find a place"><nav class="gv-places">${side}</nav></aside>` +
    `<section class="gv-place"><h3>${esc(place.name)}</h3><p class="gv-sub">${esc(place.region)} · ${place.ids.size} Pokémon · ${missIn(place)} missing</p>` +
    `${groups || `<p class="gv-empty">Nothing to catch here.</p>`}</section></div>`;
  gameView.classList.toggle("only-missing", gv.onlyMissing);
  const cur = gameView.querySelector('.gv-pl[aria-current="page"]');
  if (cur) cur.scrollIntoView({ block: "nearest" });
  const hl = gameView.querySelector(".gv-mon.hl");
  if (hl && placeSlug) hl.scrollIntoView({ block: "center" });
}

let inGames = false;
const pageTitle = document.getElementById("title");
pageTitle.addEventListener("click", () => { if (inGames) location.hash = ""; });
pageTitle.addEventListener("keydown", ev => { if (inGames && (ev.key === "Enter" || ev.key === " ")) { ev.preventDefault(); location.hash = ""; } });
function route(keepScroll = false) {
  const m = location.hash.match(/^#(games|game\/([a-z0-9-]+)(?:\/([a-z0-9-]+))?)(?:\?p=([^&]+))?$/);
  const on = !!m;
  if (on && !inGames) { gv.dexY = window.scrollY; if (openInfo) closeInfo(false); setSelecting(false); }
  document.body.classList.toggle("in-games", on);
  gameView.hidden = !on;
  header.classList.remove("tucked");
  // on the game pages the title is a way back to the dex
  if (on) { pageTitle.setAttribute("role", "link"); pageTitle.tabIndex = 0; pageTitle.title = "Back to the dex"; }
  else { pageTitle.removeAttribute("role"); pageTitle.removeAttribute("tabindex"); pageTitle.removeAttribute("title"); }
  if (!on) {
    gameView.innerHTML = "";
    if (inGames) { inGames = false; requestAnimationFrame(() => window.scrollTo(0, gv.dexY)); }
    return;
  }
  inGames = true;
  gameView.style.setProperty("--hh", `${header.offsetHeight}px`);
  const y = window.scrollY;
  const done = m[1] === "games" ? Promise.resolve(renderPicker())
                                : renderGame(m[2], m[3] || "", m[4] ? decodeURIComponent(m[4]) : "");
  if (keepScroll) done.then(() => window.scrollTo(0, y)); else window.scrollTo(0, 0);
}
window.addEventListener("hashchange", () => route());
// the ✨ switch on a game page: redraw it for the other dex (art, caught marks, missing counts), same scroll
function refreshGames() { if (inGames) route(true); }
document.getElementById("gamesBtn").addEventListener("click", () => { menu.open = false; location.hash = "#games"; });

gameView.addEventListener("click", ev => {
  const btn = ev.target.closest(".gv-side-btn");
  if (btn) { const side = btn.parentNode; side.classList.toggle("open"); btn.setAttribute("aria-expanded", side.classList.contains("open")); return; }
  const mon = ev.target.closest(".gv-mon");
  if (!mon) return;
  const e = byId.get(mon.dataset.id);
  if (caught.has(e.id)) { caught.delete(e.id); dropOt([e.id]); } else caught.add(e.id);
  paintCard(e); updateCounts(); save();
  const have = caught.has(e.id);
  gameView.querySelectorAll(`.gv-mon[data-id="${CSS.escape(e.id)}"]`).forEach(x => x.classList.toggle("have", have));
  toast(`${e.label} marked ${have ? "caught" : "missing"}`);
});
gameView.addEventListener("change", ev => {
  if (ev.target.id !== "gvMissing") return;
  gv.onlyMissing = ev.target.checked;
  try { localStorage.setItem("living-dex-games-missing", gv.onlyMissing ? "1" : "0"); } catch (e) {}
  gameView.classList.toggle("only-missing", gv.onlyMissing);
  gameView.querySelectorAll(".gv-group").forEach(gr => gr.classList.toggle("all-have", [...gr.querySelectorAll(".gv-mon")].every(x => x.classList.contains("have"))));
});
gameView.addEventListener("input", ev => {
  if (!ev.target.classList.contains("gv-find")) return;
  const words = fold(ev.target.value.trim()).split(/\s+/).filter(Boolean);
  gameView.querySelectorAll(".gv-pl").forEach(a => { a.hidden = !words.every(w => a.dataset.name.includes(w)); });
});
// failed images: game icons get a retry, Pokémon art walks the same fallback list as the dex cards
gameView.addEventListener("error", ev => {
  const img = ev.target;
  if (img.tagName !== "IMG" || !img.getAttribute("src")) return;
  if (img.closest(".gv-abbr")) { iconFailed(img); return; }
  const mon = img.closest(".gv-mon");
  if (!mon) return;
  const e = byId.get(mon.dataset.id);
  const i = +img.dataset.i + 1, list = e.srcs[mode];
  if (i < list.length) { img.dataset.i = i; img.src = list[i]; }
}, true);
