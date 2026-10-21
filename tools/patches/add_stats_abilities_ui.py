"""One-off patch: Base stats (bars) and Abilities (with descriptions) in the detail panel."""
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "index.template.html"
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


rep("""  /* evolution: "from" and "into" lines with the method */""",
    """  /* base stats and abilities side by side (stacked when the panel is narrow) */
  .duo { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 12px 20px; }
  .tile.stack .duo { grid-template-columns: minmax(0, 1fr); }
  .stats { display: grid; grid-template-columns: 34px 30px minmax(0, 1fr); gap: 3px 8px; align-items: center; font-size: 12px; }
  .stats .k { color: var(--dim); }
  .stats .v { text-align: right; font-variant-numeric: tabular-nums; color: var(--text); }
  .stats .bar { height: 8px; border-radius: 4px; background: #262626; overflow: hidden; }
  .stats .bar i { display: block; height: 100%; border-radius: 4px; background: var(--sc); }
  .stats .total .k, .stats .total .v { font-weight: bold; color: var(--text); }
  .abilities { display: flex; flex-direction: column; gap: 8px; margin: 0; font-size: 12px; line-height: 1.45; }
  .abilities dt { font-weight: bold; color: var(--text); }
  .abilities dt .hid { margin-left: 6px; font-weight: normal; font-size: 10px; padding: 1px 6px; border-radius: 999px;
                       background: #3a3a3a; color: var(--muted); text-transform: uppercase; letter-spacing: .4px; }
  .abilities dd { margin: 1px 0 0; color: var(--muted); }

  /* evolution: "from" and "into" lines with the method */""")

rep("""    evolutionHtml(info) +""", """    evolutionHtml(info) + statsAbilitiesHtml(info) +""")

rep("""// "Evolves from" / "Evolves into" lines; each Pokémon name opens its own panel""",
    """// Base stats as bars (scaled to 255, coloured by value like Serebii/PokémonDB) and the abilities
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

// "Evolves from" / "Evolves into" lines; each Pokémon name opens its own panel""")

SRC.write_text(src, encoding="utf-8")
print("ok")
