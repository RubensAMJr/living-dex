"""One-off patch: the page reads the new split data files and shows "obtainable by evolving" badges.

- info-data.js now has game indexes (DEX_GAMES) instead of full location lists: f = found, v = by evolving,
  n = why not found (keyed by game index).
- Location details come from info-places.js, loaded the first time a game badge is hovered or tapped.
- Games where the Pokémon can only be obtained by evolving get a dashed, half-tinted badge and a detail
  like "Evolve Numel (Level 33)".
"""
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "index.template.html"
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


rep("""  .game.miss { background: transparent; color: #707070; border-color: #4a4a4a; font-weight: normal; }""",
    """  .game.miss { background: transparent; color: #707070; border-color: #4a4a4a; font-weight: normal; }
  /* obtainable only by evolving a Pokémon found in that game */
  .game.evo { background: color-mix(in srgb, var(--gc) 28%, transparent); border: 1px dashed var(--gc); color: #f2f2f2; }
  .games-legend { display: flex; flex-wrap: wrap; gap: 4px 14px; margin-top: 8px; font-size: 11px; color: var(--dim); }
  .games-legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: 5px; vertical-align: -1px; border-radius: 2px; }
  .games-legend .l-found::before { background: #7a8a96; }
  .games-legend .l-evo::before { background: rgba(122,138,150,.3); border: 1px dashed #9aaab6; }
  .games-legend .l-miss::before { border: 1px solid #4a4a4a; }""")

rep("""  const found = GAMES.reduce((n, [, list]) => n + list.filter(g => info.g[g[0]]).length, 0);
  const total = GAMES.reduce((n, [, list]) => n + list.length, 0);""",
    """  const found = (info.f || []).length, byEvo = (info.v || []).length;
  const total = GAMES.reduce((n, [, list]) => n + list.length, 0);""")
rep("""    `<section><h4>Where to find it <small>found in ${found} of ${total} games</small></h4><div class="games">` +
    GAMES.map(([gen, list]) => `<div class="gen"><span class="gen-label">Gen ${gen}</span><div class="gen-games">` + list.map(([id, abbr, name, color, ink]) =>
      `<button type="button" class="game${info.g[id] ? "" : " miss"}" data-game="${id}" aria-pressed="false" title="${esc(name)}"` +
      (info.g[id] ? ` style="--gc:${color};--gi:${ink || "#fff"}"` : "") + `>${abbr}</button>`).join("") + `</div></div>`).join("") +
    `</div><p class="game-detail" aria-live="polite">Hover or tap a game to see where to find ${esc(e.label)}.</p></section>`;""",
    """    `<section><h4>Where to find it <small>found in ${found} of ${total} games${byEvo ? ` · ${byEvo} more by evolving` : ""}</small></h4><div class="games">` +
    GAMES.map(([gen, list]) => `<div class="gen"><span class="gen-label">Gen ${gen}</span><div class="gen-games">` + list.map(([id, abbr, name, color, ink]) => {
      const state = gameState(info, id);
      return `<button type="button" class="game${state === "found" ? "" : state === "evolve" ? " evo" : " miss"}" data-game="${id}" aria-pressed="false" title="${esc(name)}"` +
        (state !== "miss" ? ` style="--gc:${color};--gi:${ink || "#fff"}"` : "") + `>${abbr}</button>`;
    }).join("") + `</div></div>`).join("") +
    `</div><div class="games-legend"><span class="l-found">Found (wild or gift)</span><span class="l-evo">By evolving</span><span class="l-miss">Not obtainable</span></div>` +
    `<p class="game-detail" aria-live="polite">Hover or tap a game to see where to find ${esc(e.label)}.</p></section>`;""")

rep("""function gameDetail(e, info, id) {
  const [, , name] = GAME_BY_ID.get(id);
  const finds = info.g[id];
  if (!finds) {
    // Serebii's own wording when it gave one (e.g. "Trade from X & Y", "Evolve Ivysaur")
    const why = info.n && info.n[id];
    return `<b>${esc(name)}</b>: not found in the wild or as a gift` + (why ? ` (${esc(why)}).` : " (trade or transfer only, or not in this game).");
  }
  return `<b>${esc(name)}</b>: ` + finds.map(([method, place, lv]) => `${esc(method)} · ${esc(place)}${lv ? ` (${esc(lv)})` : ""}`).join("; ");
}""", """const DEX_GAMES = window.DEX_GAMES || [];
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
// location details live in info-places.js, loaded the first time you look at a game
let placesLoading = null;
function loadPlaces() {
  if (window.DEX_PLACES) return Promise.resolve();
  if (!placesLoading) placesLoading = new Promise(resolve => {
    const s = document.createElement("script");
    s.src = "info-places.js";
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
    return `<b>${esc(name)}</b>: ` + (row ? esc(window.DEX_PLACES.s[row[1]]) : "found in this game.");
  }
  if (state === "evolve") {
    const steps = evolveSteps(e.id, gi) || [];
    const chain = steps.map(([pid, how], i) => {
      const x = byId.get(pid);
      return (i === 0 ? `Evolve ${esc(x ? x.label : pid)}` : `then ${esc(x ? x.label : pid)}`) + ` (${esc(how)})`;
    }).join(", ");
    return `<b>${esc(name)}</b>: not found in the wild or as a gift. ${chain || "Obtainable by evolving."}`;
  }
  // Serebii's own wording when it gave one (e.g. "Trade from X & Y")
  const why = info.n && info.n[gi];
  return `<b>${esc(name)}</b>: not obtainable in this game` + (why ? ` (${esc(why)}).` : " (trade or transfer only, or not in this game).");
}""")

rep("""  const show = btn => {
    panel.querySelectorAll('.game[aria-pressed="true"]').forEach(b => b.setAttribute("aria-pressed", "false"));
    btn.setAttribute("aria-pressed", "true");
    panel.querySelector(".game-detail").innerHTML = gameDetail(e, info, btn.dataset.game);
  };""", """  const show = btn => {
    panel.querySelectorAll('.game[aria-pressed="true"]').forEach(b => b.setAttribute("aria-pressed", "false"));
    btn.setAttribute("aria-pressed", "true");
    const detail = panel.querySelector(".game-detail");
    detail.innerHTML = gameDetail(e, info, btn.dataset.game);
    if (!window.DEX_PLACES) loadPlaces().then(() => {
      if (btn.getAttribute("aria-pressed") === "true") detail.innerHTML = gameDetail(e, info, btn.dataset.game);
    });
  };""")

SRC.write_text(src, encoding="utf-8")
print("ok")
