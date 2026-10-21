"""One-off patch: Evolution section in the detail panel (evolves from / evolves into, with the method)."""
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src" / "index.template.html"
src = SRC.read_text(encoding="utf-8")


def rep(old, new):
    global src
    assert src.count(old) == 1, (old[:80], src.count(old))
    src = src.replace(old, new)


rep("""  /* where to find it: one row per generation, one badge per version */""",
    """  /* evolution: "from" and "into" lines with the method */
  .evo { display: grid; grid-template-columns: auto 1fr; gap: 4px 10px; font-size: 12px; line-height: 1.45; }
  .evo dt { color: var(--dim); }
  .evo dd { margin: 0; color: var(--muted); }
  .evo .evo-link {
    border: 0; padding: 0; background: none; cursor: pointer; font: inherit; font-weight: bold; color: var(--text);
    text-decoration: underline; text-decoration-color: var(--accent-hi); text-underline-offset: 2px;
  }
  .evo .evo-link:focus-visible { outline: 2px solid var(--accent-hi); outline-offset: 2px; }
  .evo .how { color: var(--muted); }

  /* where to find it: one row per generation, one badge per version */""")

rep("""    `<section><h4>Weaknesses</h4><p class="weak-sum">${sum}</p><div class="dmg">` +""",
    """    evolutionHtml(info) +
    `<section><h4>Weaknesses</h4><p class="weak-sum">${sum}</p><div class="dmg">` +""")

rep("""function infoHtml(e, info) {""", """// "Evolves from" / "Evolves into" lines; each Pokémon name opens its own panel
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

function infoHtml(e, info) {""")

# clicking a Pokémon name in the Evolution section opens that Pokémon's panel
rep("""    const g = ev.target.closest(".game");
    if (g) show(g);""", """    const g = ev.target.closest(".game");
    if (g) show(g);
    const link = ev.target.closest(".evo-link");
    if (link) {
      const target = byId.get(link.dataset.id);
      if (target && target.el && !target.el.hidden) {
        toggleInfo(target);
        target.el.scrollIntoView({ block: "center", behavior: reducedMotion ? "auto" : "smooth" });
      } else toast(`${target ? target.label : "That Pokémon"} is hidden by the current filters`);
    }""")

SRC.write_text(src, encoding="utf-8")
print("ok")
