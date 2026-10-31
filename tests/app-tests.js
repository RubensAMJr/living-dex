// In-browser tests for the Living Dex Checklist. Open tests/index.html through a local server
// (python -m http.server, then http://localhost:8000/tests/). Each test loads the real app in the frame with
// nothing marked, drives it like a user and checks the result. Your own marks and settings are saved before
// the run and put back afterwards. Results are also in window.testResults when it's done.

const frame = document.getElementById("app");
const list = document.getElementById("results");
const summary = document.getElementById("summary");
const tests = [];
const test = (name, fn, opts = {}) => tests.push({ name, fn, ...opts });

const wait = ms => new Promise(r => setTimeout(r, ms));
async function until(check, what, timeout = 8000) {
  const end = Date.now() + timeout;
  for (;;) {
    let ok = false;
    try { ok = await check(); } catch (e) { /* not ready yet */ }
    if (ok) return ok;
    if (Date.now() > end) throw new Error(`timed out waiting for ${what}`);
    await wait(50);
  }
}
function assert(cond, msg) { if (!cond) throw new Error(msg); }
function eq(actual, expected, msg) {
  if (JSON.stringify(actual) !== JSON.stringify(expected))
    throw new Error(`${msg}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

// the app's own variables (const/let in its classic scripts) are reachable through eval in its window
let W;
const $ = expr => W.eval(expr);
const q = sel => W.document.querySelector(sel);
const qa = sel => [...W.document.querySelectorAll(sel)];

const APP_KEYS = key => key.startsWith("living-dex");
async function load(hash = "", width = "100%") {
  frame.style.width = width;
  for (const key of Object.keys(localStorage)) if (APP_KEYS(key)) localStorage.removeItem(key);
  const loaded = new Promise(r => frame.addEventListener("load", r, { once: true }));
  frame.src = `../index.html?test=${Date.now()}${hash}`;
  await loaded;
  W = frame.contentWindow;
  W.__errors = [];
  W.addEventListener("error", e => W.__errors.push(e.message));
  await until(() => $("entries.length") === 1082 && q(".card"), "the dex to be built");
  if (hash) await until(() => $("inGames"), "a game page");
}
const card = id => $(`byId.get(${JSON.stringify(id)})`);
async function click(el) { el.click(); await wait(60); }

// ---------------------------------------------------------------- the dex
test("loads the dex: 1,082 cards, 14 chips, nothing marked", async () => {
  await load();
  eq(qa(".card").length, 1082, "cards");
  eq(qa("#gens button").length, 14, "category chips");
  eq(q("#caughtCount").textContent, "0", "caught count");
  eq($("mode"), "normal", "starts in the regular dex");
  eq(q("#title").textContent, "Living Dex Checklist", "title");
});

test("marks and unmarks a Pokémon, and saves it", async () => {
  await load();
  await click(card("1").el);
  assert($('caught.has("1")'), "Bulbasaur caught after a click");
  assert(card("1").el.classList.contains("cn"), "card painted caught");
  assert(JSON.parse(localStorage.getItem("living-dex-checker-v2")).includes("1"), "saved");
  eq(q("#caughtCount").textContent, "1", "count");
  await click(card("1").el);
  assert(!$('caught.has("1")'), "missing again after a second click");
});

test("search, status filter and regional forms toggle", async () => {
  await load();
  const shown = () => $("entries.filter(e => !e.el.hidden).map(e => e.label)");
  const search = async text => { const input = q("#q"); input.value = text; input.dispatchEvent(new W.Event("input", { bubbles: true })); await wait(300); };
  await search("pikachu");
  eq(shown(), ["Pikachu"], "search by name");
  await search("25");
  eq(shown(), ["Pikachu"], "search by number");
  await search("");
  await click(card("4").el);
  await click(q('.seg [data-status="caught"]'));
  eq(shown(), ["Charmander"], "Caught filter");
  await click(q('.seg [data-status="missing"]'));
  eq(shown().length, 1081, "Missing filter");
  await click(q('.seg [data-status="all"]'));
  await click(q("#forms"));
  eq(shown().length, 1025, "regional forms hidden");
});

// ---------------------------------------------------------------- Pokédex tile
test("Pokédex tile: badges, evolve-only detail, map link, stats, abilities", async () => {
  await load();
  $('toggleInfo(byId.get("323"))');                   // Camerupt
  await until(() => q(".tile .info"), "the tile");
  eq(qa(".info .game").length, 38, "game badges");
  assert(q('.info .game[data-game="ruby"]').classList.contains("evo"), "Ruby is an evolve-only badge");
  await click(q('.info .game[data-game="ruby"]'));
  await until(() => q(".game-detail").textContent.includes("Evolve Numel"), "the evolve detail");
  eq(q(".game-detail .game-open").getAttribute("href"), "#game/ruby?p=322", "map link highlights Numel");
  eq(qa(".info .stats .bar").length, 6, "base stats");
  assert(qa(".info .abilities dt").length >= 2, "abilities");
  await click(q('.info .game[data-game="diamond"]'));
  await until(() => /Route|Stark/.test(q(".game-detail").textContent), "places from data/info-places.js");
});

// ---------------------------------------------------------------- selection mode
test("selection mode: select two, mark caught, done", async () => {
  await load();
  await click(q("#selectBtn"));
  assert(!q("#selbar").hidden, "bar shown");
  await click(card("4").el);
  await click(card("7").el);
  eq(q("#selCount").textContent, "2 selected", "count");
  await click(q("#selMark"));
  assert($('caught.has("4") && caught.has("7")'), "both caught");
  assert($("selecting"), "still selecting after marking");
  await click(q("#selDone"));
  assert(q("#selbar").hidden && !$("selecting"), "left selection mode");
});

// ---------------------------------------------------------------- shiny dex
test("✨ switch: the first switch shows its whole animation", async () => {
  await load();
  // record the effect's state when the dex changes (applyMode) and when the layer is removed
  const removed = [], changed = [];
  const original = W.Element.prototype.remove, applyMode = W.applyMode;
  W.Element.prototype.remove = function () {
    if (this.classList && this.classList.contains("fx"))
      removed.push(this.getAnimations({ subtree: true }).map(a => a.playState));
    return original.call(this);
  };
  W.applyMode = function (...args) {
    const fx = W.document.querySelector(".fx");
    changed.push(fx ? fx.getAnimations({ subtree: true }).map(a => a.startTime !== null) : null);
    return applyMode.apply(this, args);
  };
  // animations only run while the page is drawn (not in a hidden window or a background tab)
  const drawn = await Promise.race([new Promise(r => W.requestAnimationFrame(() => r(true))), wait(300).then(() => false)]);
  try {
    await click(q("#shinyBtn"));
    assert(q(".fx"), "effect layer added");
    await until(() => $("mode") === "shiny", "the shiny dex");
    eq(q("#title").textContent, "Shiny Living Dex", "title");
    await until(() => removed.length, "the effect layer to be removed", 6000);
    if (drawn) {
      assert(changed[0] && changed[0].length > 0 && changed[0].every(Boolean),
             "the effect was already running when the dex changed");
      assert(removed[0].length > 0 && removed[0].every(s => s === "finished"),
             `all animations finished before removal (got ${removed[0].join(",")})`);
    }
  } finally { W.Element.prototype.remove = original; W.applyMode = applyMode; }
  await until(() => !$("animating"), "the switch to settle");
  await click(q("#shinyBtn"));
  await until(() => $("mode") === "normal", "back to the regular dex");
  if (!drawn) return "animation order not checked: the page isn't being drawn (window hidden?)";
});

test("shiny note: only in the shiny dex, × hides it for good", async () => {
  await load();
  assert(q("#shinyNote").hidden, "hidden in the regular dex");
  $('mode = "shiny"; applyMode(true)');
  assert(!q("#shinyNote").hidden, "shown in the shiny dex");
  await click(q("#shinyNote button"));
  assert(q("#shinyNote").hidden, "hidden after ×");
  eq(localStorage.getItem("living-dex-shiny-note-hidden"), "1", "remembered");
});

test("OT marks: setting shows caps, OT implies caught", async () => {
  await load();
  await click(q("#optShowOt"));
  assert(W.getComputedStyle(card("4").el.querySelector(".ot-btn")).display !== "none", "caps shown");
  await click(card("4").el.querySelector(".ot-btn"));
  assert($('otSets.normal.has("4") && caught.has("4")'), "OT and caught");
  await click(card("4").el);
  assert(!$('otSets.normal.has("4")'), "unmarking caught drops OT");
});

// ---------------------------------------------------------------- game pages
test("game picker: 38 games with icons, from the menu", async () => {
  await load();
  await click(q("#gamesBtn"));
  await until(() => qa(".gv-game").length === 38, "38 game tiles");
  eq(qa(".gv-abbr.icon img").length, 38, "an icon on every game");
  assert(W.document.body.classList.contains("in-games"), "dex hidden");
});

test("game page from a badge: highlights the Pokémon, dims other places", async () => {
  await load("#game/ruby?p=322");
  await until(() => q(".gv-mon.hl"), "the highlight");
  assert(q(".gv-mon.hl").dataset.id === "322", "Numel highlighted");
  assert(qa(".gv-pl.dim").length > 0 && qa(".gv-pl:not(.dim)").length > 0, "places without Numel dimmed");
  assert(q(".gv-focus").textContent.includes("Numel"), "focus banner");
});

test("game page: marking a Pokémon updates the dex, Only missing hides it", async () => {
  await load("#game/ultra-sun/alola-route-1");
  await until(() => q('.gv-mon[data-id="165"]'), "Ledyba on Route 1");
  await click(q('.gv-mon[data-id="165"]'));
  assert($('caught.has("165")') && q('.gv-mon[data-id="165"]').classList.contains("have"), "Ledyba caught");
  await click(q("#gvMissing"));
  eq(W.getComputedStyle(q('.gv-mon[data-id="165"]')).display, "none", "hidden by Only missing");
});

test("game page: ✨ redraws it for the other dex", async () => {
  await load("#game/ultra-sun/alola-route-1");
  await until(() => q('.gv-mon[data-id="165"]'), "Ledyba on Route 1");
  $('sets.normal.add("165")');
  $('mode = "shiny"; applyMode()');
  await until(() => q('.gv-mon[data-id="165"] img').getAttribute("src").includes("ibb.co"), "shiny art");
  assert(!q('.gv-mon[data-id="165"]').classList.contains("have"), "not caught in the shiny dex");
  $('mode = "normal"; applyMode()');
  await until(() => q('.gv-mon[data-id="165"]').classList.contains("have"), "caught again in the regular dex");
});

test("game pages: selection mode ends, title and back button return to the dex", async () => {
  await load();
  await click(q("#selectBtn"));
  W.location.hash = "#games";
  await until(() => $("inGames"), "the picker");
  assert(!$("selecting") && W.getComputedStyle(q("#selbar")).display === "none", "selection ended and bar hidden");
  W.location.hash = "#game/platinum";
  await until(() => q(".gv-place h3"), "Platinum");
  W.history.back();
  await until(() => qa(".gv-game").length === 38, "back to the picker");
  eq(q("#title").getAttribute("role"), "link", "title is a link on game pages");
  await click(q("#title"));
  await until(() => !$("inGames"), "the dex");
  eq(q("#title").getAttribute("role"), null, "title is a plain heading on the dex");
});

test("phone width: game page header doesn't overlap", async () => {
  await load("#games", "375px");
  const box = el => el.getBoundingClientRect();
  const range = W.document.createRange();
  range.selectNodeContents(q("#title"));
  const title = range.getBoundingClientRect(), shiny = box(q("#shinyBtn")), menu = box(q(".menu > summary"));
  assert(shiny.right <= title.left && title.right <= menu.left, `title ${title.left}-${title.right} between ✨ ${shiny.right} and ☰ ${menu.left}`);
});

// ---------------------------------------------------------------- runner
async function runAll() {
  const saved = Object.fromEntries(Object.entries(localStorage).filter(([k]) => APP_KEYS(k)));
  list.innerHTML = "";
  summary.className = "";
  const results = [];
  for (const t of tests) {
    const li = document.createElement("li");
    li.textContent = t.name;
    list.appendChild(li);
    const started = performance.now();
    try {
      const note = await t.fn();   // a test may return a note, e.g. a part it couldn't check
      if (W && W.__errors.length) throw new Error(`script errors: ${W.__errors.join(" | ")}`);
      li.className = "ok";
      if (note) { li.insertAdjacentHTML("beforeend", "<small></small>"); li.lastChild.textContent = note; }
      results.push({ name: t.name, ok: true, ...(note && { note }) });
    } catch (err) {
      li.className = "bad";
      li.insertAdjacentHTML("beforeend", `<small></small>`);
      li.lastChild.textContent = err.message;
      results.push({ name: t.name, ok: false, error: err.message });
    }
    li.title = `${Math.round(performance.now() - started)} ms`;
  }
  for (const key of Object.keys(localStorage)) if (APP_KEYS(key)) localStorage.removeItem(key);
  for (const [k, v] of Object.entries(saved)) localStorage.setItem(k, v);
  frame.style.width = "100%";
  const failed = results.filter(r => !r.ok).length;
  summary.textContent = failed ? `${failed} of ${results.length} failed` : `all ${results.length} passed`;
  summary.className = failed ? "bad" : "ok";
  window.testResults = results;
}
document.getElementById("run").addEventListener("click", runAll);
runAll();
