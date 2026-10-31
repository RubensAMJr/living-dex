"""One-off patch: game pages. Menu → Games opens a picker; each game has a page listing its regions and places, and
for the selected place every Pokémon you can catch there, grouped by area and method (walking, surfing, fishing, ...).

Addresses: #games, #game/<game id>, #game/<game id>/<place>, plus ?p=<entry id> to highlight one Pokémon.
The back button works, and the main dex keeps its scroll position.
For the design review only Bulbasaur's game badges get the "Open <game> map" link.
"""
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "index.template.html"
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


# ---------------------------------------------------------------- CSS
rep("""</style>
</head>""", """
  /* ---------- game pages ---------- */
  .gv { padding-top: 14px; padding-bottom: 40px; }
  body.in-games #main, body.in-games #empty, body.in-games footer,
  body.in-games header .gens, body.in-games header .progress,
  body.in-games header .controls > :not(.menu):not(.shiny-btn) { display: none !important; }
  body.in-games header .controls { justify-content: flex-end; }
  .gv-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; font-size: 12px; }
  .gv-back { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px; background: var(--panel-hi);
             color: var(--text); text-decoration: none; font-weight: bold; }
  .gv-back:hover { background: #575757; }
  .gv-crumbs { color: var(--dim); display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
  .gv-crumbs a { color: var(--muted); text-decoration: none; }
  .gv-crumbs a:hover { color: #fff; text-decoration: underline; }
  .gv-crumbs span::before { content: "›"; margin-right: 6px; color: #666; }
  .gv-lead { color: var(--muted); margin: 0 0 14px; }

  /* picker: one coloured tile per game, grouped by generation */
  .gv-gen h3 { margin: 18px 0 8px; font-size: 13px; color: var(--accent-soft); letter-spacing: .3px; }
  .gv-games { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px; }
  .gv-game { display: grid; grid-template-columns: 44px 1fr; grid-template-rows: auto auto; column-gap: 10px; align-items: center;
             padding: 10px; border-radius: 8px; background: var(--panel); border: 1px solid var(--edge); color: var(--text);
             text-decoration: none; transition: transform .15s ease, background .15s ease; }
  .gv-game:hover { background: var(--panel-hi); transform: translateY(-1px); }
  .gv-abbr { grid-row: span 2; display: grid; place-items: center; width: 44px; height: 44px; border-radius: 8px;
             background: var(--gc); color: var(--gi); font-weight: bold; font-size: 14px; box-shadow: inset 0 -3px 0 rgba(0,0,0,.25); }
  .gv-name { font-weight: bold; }
  .gv-meta { font-size: 11px; color: var(--dim); }
  .gv-meta b { color: var(--gold); }

  /* one game */
  .gv-head { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 14px; padding: 12px 14px; border-radius: 10px;
             background: linear-gradient(90deg, color-mix(in srgb, var(--gc) 35%, var(--panel)) 0%, var(--panel) 70%);
             border: 1px solid var(--edge); margin-bottom: 12px; }
  .gv-head h2 { margin: 0; font-size: 18px; }
  .gv-head .gv-abbr { grid-row: auto; }
  .gv-head .gv-meta { font-size: 12px; color: var(--muted); }
  .gv-head .toggle { margin-left: auto; }
  .gv-focus { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0 0 12px; padding: 8px 12px; border-radius: 8px;
              background: rgba(255,213,74,.1); border: 1px solid rgba(255,213,74,.35); color: #ffe9a8; font-size: 12px; }
  .gv-focus a { color: #fff; margin-left: auto; }
  .gv-body { display: grid; grid-template-columns: 270px minmax(0, 1fr); gap: 16px; align-items: start; }
  .gv-side { position: sticky; top: calc(var(--hh, 70px) + 10px); max-height: calc(100vh - var(--hh, 70px) - 20px);
             display: flex; flex-direction: column; background: var(--panel); border: 1px solid var(--edge); border-radius: 10px; overflow: hidden; }
  .gv-side-btn { display: none; }
  .gv-find { margin: 8px; padding: 7px 10px; border-radius: 6px; border: 1px solid var(--edge); background: var(--bg); }
  .gv-places { overflow: auto; padding: 0 6px 8px; }
  .gv-region { position: sticky; top: 0; z-index: 1; margin: 0; padding: 8px 6px 4px; font-size: 11px; text-transform: uppercase;
               letter-spacing: .6px; color: var(--accent-soft); background: var(--panel); }
  .gv-pl { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 6px 8px; border-radius: 6px;
           color: var(--muted); text-decoration: none; font-size: 12px; }
  .gv-pl:hover { background: var(--panel-hi); color: #fff; }
  .gv-pl[aria-current="page"] { background: color-mix(in srgb, var(--gc) 40%, var(--panel-hi)); color: #fff; font-weight: bold; }
  .gv-pl small { flex: none; min-width: 22px; text-align: center; padding: 1px 6px; border-radius: 999px; background: #2c2c2c; color: var(--dim); font-size: 10px; }
  .gv-pl small.miss { background: rgba(255,213,74,.16); color: var(--gold); }
  .gv-pl.dim { opacity: .45; }
  .gv-place h3 { margin: 0 0 2px; font-size: 17px; }
  .gv-place .gv-sub { margin: 0 0 12px; color: var(--dim); font-size: 12px; }
  .gv-group { margin-bottom: 14px; background: var(--panel); border: 1px solid var(--edge); border-radius: 10px; overflow: hidden; }
  .gv-group h4 { margin: 0; padding: 8px 12px; font-size: 12px; background: var(--panel-hi); display: flex; gap: 8px; align-items: center; }
  .gv-group h4 small { color: var(--dim); font-weight: normal; }
  .gv-mons { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 6px; padding: 8px; }
  .gv-mon { display: grid; grid-template-columns: 56px minmax(0, 1fr); column-gap: 8px; align-items: center; text-align: left; padding: 6px;
            border-radius: 8px; border: 1px solid transparent; background: #3a3a3a; cursor: pointer; }
  .gv-mon:hover { background: #454545; }
  .gv-mon img { grid-row: span 3; width: 56px; height: 56px; object-fit: contain; filter: grayscale(1) brightness(.75); opacity: .7;
                transition: filter .25s ease, opacity .25s ease; }
  .gv-mon.have img { filter: none; opacity: 1; }
  .gv-mon.have { border-color: color-mix(in srgb, var(--accent) 60%, transparent); }
  .gv-mon b { font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .gv-mon b i { font-style: normal; font-weight: normal; color: var(--accent-hi); margin-left: 4px; font-size: 11px; }
  .gv-mon span { font-size: 11px; color: var(--muted); }
  .gv-mon .gv-note { color: var(--dim); font-size: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .gv-mon.hl { border-color: var(--gold); box-shadow: 0 0 0 1px var(--gold), 0 0 14px rgba(255,213,74,.35); }
  .gv-empty { padding: 20px; color: var(--dim); text-align: center; }
  .gv.only-missing .gv-mon.have { display: none; }
  .gv.only-missing .gv-group.all-have { display: none; }
  .game-open { display: inline-block; margin-top: 6px; color: var(--gold); font-weight: bold; text-decoration: none; }
  .game-open:hover { text-decoration: underline; }
  @media (max-width: 760px) {
    .gv-body { grid-template-columns: minmax(0, 1fr); }
    .gv-side { position: static; max-height: none; }
    .gv-side-btn { display: flex; justify-content: space-between; align-items: center; width: 100%; padding: 10px 12px; border: 0;
                   background: var(--panel-hi); font-weight: bold; text-align: left; }
    .gv-side:not(.open) .gv-find, .gv-side:not(.open) .gv-places { display: none; }
    .gv-side.open .gv-places { max-height: 55vh; }
    .gv-mons { grid-template-columns: minmax(0, 1fr); }
    .gv-head .toggle { margin-left: 0; }
  }
</style>
</head>""")

# ---------------------------------------------------------------- HTML
rep("""        <div class="items">
          <div class="head">Animations</div>""", """        <div class="items">
          <button type="button" id="gamesBtn">🎮 Games: routes &amp; places</button>
          <hr>
          <div class="head">Animations</div>""")
rep("""<div class="empty wrap" id="empty">No Pokémon match these filters.</div>""",
    """<div class="empty wrap" id="empty">No Pokémon match these filters.</div>
<div class="wrap gv" id="gameView" hidden></div>""")

# ---------------------------------------------------------------- badge link (Bulbasaur only for the review)
rep("""    const row = (window.DEX_PLACES.d[e.id] || []).find(r => r[0] === gi);
    return `<b>${esc(name)}</b>: ` + (row ? esc(window.DEX_PLACES.s[row[1]]) : "found in this game.");""",
    """    const row = (window.DEX_PLACES.d[e.id] || []).find(r => r[0] === gi);
    return `<b>${esc(name)}</b>: ` + (row ? esc(window.DEX_PLACES.s[row[1]]) : "found in this game.") +
      (MAP_PREVIEW.has(e.id) ? `<br><a class="game-open" href="#game/${id}?p=${encodeURIComponent(e.id)}">Open ${esc(name)} map →</a>` : "");""")
rep("""const DEX_GAMES = window.DEX_GAMES || [];""", """const DEX_GAMES = window.DEX_GAMES || [];
const MAP_PREVIEW = new Set(["1"]); // Pokémon whose badges link to the game pages (design review: Bulbasaur only)""")

# ---------------------------------------------------------------- JS: views
rep("""// ---------- go ----------""", r"""// ---------- game pages: #games, #game/<id>[/<place>][?p=<entry id>] ----------
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
    s.src = `locations/${id}.js`;
    s.onload = s.onerror = () => resolve(window.DEX_LOC && window.DEX_LOC[id]);
    document.head.appendChild(s);
  });
  return locLoading[id];
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
        return `<a class="gv-game" href="#game/${id}" style="--gc:${color};--gi:${ink || "#fff"}"><span class="gv-abbr">${abbr}</span>` +
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
    `<div class="gv-head"><span class="gv-abbr" style="--gi:${g.ink}">${esc(g.abbr)}</span><div><h2>${esc(g.name)}</h2>` +
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
function route() {
  const m = location.hash.match(/^#(games|game\/([a-z0-9-]+)(?:\/([a-z0-9-]+))?)(?:\?p=([^&]+))?$/);
  const on = !!m;
  if (on && !inGames) { gv.dexY = window.scrollY; if (openInfo) closeInfo(false); }
  document.body.classList.toggle("in-games", on);
  gameView.hidden = !on;
  header.classList.remove("tucked");
  if (!on) {
    gameView.innerHTML = "";
    if (inGames) { inGames = false; requestAnimationFrame(() => window.scrollTo(0, gv.dexY)); }
    return;
  }
  inGames = true;
  gameView.style.setProperty("--hh", `${header.offsetHeight}px`);
  if (m[1] === "games") renderPicker();
  else renderGame(m[2], m[3] || "", m[4] ? decodeURIComponent(m[4]) : "");
  window.scrollTo(0, 0);
}
window.addEventListener("hashchange", route);
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
// art fallbacks, same order as the dex cards
gameView.addEventListener("error", ev => {
  const img = ev.target;
  if (img.tagName !== "IMG") return;
  const e = byId.get(img.closest(".gv-mon").dataset.id);
  const i = +img.dataset.i + 1, list = e.srcs[mode];
  if (i < list.length) { img.dataset.i = i; img.src = list[i]; }
}, true);

// ---------- go ----------""")
rep("""idle(prepareSpark, { timeout: 1500 });
save();""", """idle(prepareSpark, { timeout: 1500 });
save();
route();""")

SRC.write_text(src, encoding="utf-8")
print("ok")
