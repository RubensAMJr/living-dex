// Constants, helpers and the list of checklist entries (from data/pokemon.js).

const GENS = [
  { n: 1, roman: "I",    region: "Kanto",  from: 1,   to: 151 },
  { n: 2, roman: "II",   region: "Johto",  from: 152, to: 251 },
  { n: 3, roman: "III",  region: "Hoenn",  from: 252, to: 386 },
  { n: 4, roman: "IV",   region: "Sinnoh", from: 387, to: 493 },
  { n: 5, roman: "V",    region: "Unova",  from: 494, to: 649 },
  { n: 6, roman: "VI",   region: "Kalos",  from: 650, to: 721 },
  { n: 7, roman: "VII",  region: "Alola",  from: 722, to: 809 },
  { n: 8, roman: "VIII", region: "Galar",  from: 810, to: 905 },
  { n: 9, roman: "IX",   region: "Paldea", from: 906, to: 1025 },
];
// Regional forms get their own categories after the national dex
const FORM_REGIONS = [
  { region: "Alolan",   place: "Alola",  home: "A" },
  { region: "Galarian", place: "Galar",  home: "G" },
  { region: "Hisuian",  place: "Hisui",  home: "H" },
  { region: "Paldean",  place: "Paldea", home: "P" },
];
const pad = n => String(n).padStart(4, "0");
const GROUPS = [
  ...GENS.map(g => ({ key: `g${g.n}`, title: `Generation ${g.roman}`, sub: `${g.region} · #${pad(g.from)}–${pad(g.to)}`,
                      chip: `Gen ${g.roman}`, chipTitle: `Generation ${g.roman} – ${g.region}`, form: false })),
  ...FORM_REGIONS.map(f => ({ key: f.region, title: `${f.region} Forms`, sub: `${f.place} regional variants`,
                              chip: f.region, chipTitle: `${f.region} regional forms`, form: true })),
];
const groupByKey = new Map(GROUPS.map(g => [g.key, g]));

// v2: fresh start with #1–721 caught (v1 may hold an empty list saved by a page with no data)
// shiny-v2: starts from the shinies found in the PKHeX living dex exports (the ★ files)
const KEYS = { normal: "living-dex-checker-v2", shiny: "living-dex-checker-shiny-v2" };
// OT (original trainer) marks: separate lists for the regular and the shiny dex
const OT_KEYS = { normal: "living-dex-checker-ot-v1", shiny: "living-dex-checker-shiny-ot-v1" };
const MODE_KEY = "living-dex-checker-mode";
const BULB = "https://archives.bulbagarden.net/media/upload/thumb/";
const SEREBII = "https://www.serebii.net/";
const IMGBB = "https://i.ibb.co/";

const fold = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const homeLetter = Object.fromEntries(FORM_REGIONS.map(f => [f.region, f.home]));

function thumb(dirs, file, width = 120) {
  const f = encodeURIComponent(file);
  return `${BULB}${dirs}/${f}/${width}px-${f}`;
}

const entries = DATA.map(([id, dex, name, region, note, b, s, sh, ib]) => {
  const gen = GENS.find(g => dex >= g.from && dex <= g.to);
  const label = region ? `${region} ${name}` : name;
  const group = groupByKey.get(region || `g${gen.n}`);
  // Shiny art: Sugimori-style shinies from the imgbb gallery (180px thumbnails), then the
  // Pokémon HOME renders on Bulbapedia (e.g. HOME0019A_s.png, HOME0128PC_s.png), then Serebii
  const homeSuffix = !region ? "" : dex === 128 ? "P" + id.slice(-1).toUpperCase() : homeLetter[region];
  const [bDir1, bDir2, bFile] = b.split("/");
  const bDirs = `${bDir1}/${bDir2}`;
  const srcs = {
    normal: [thumb(bDirs, bFile), `${SEREBII}pokemon/art/${s}.png`],
    shiny: [`${IMGBB}${ib}/${s}.png`, thumb(sh, `HOME${pad(dex)}${homeSuffix}_s.png`),
            `${SEREBII}Shiny/SV/new/${s}.png`, `${SEREBII}Shiny/SWSH/${s}.png`],
  };
  // high-density screens (phones) get Bulbapedia's 240px thumbnail of the regular art
  const srcset = `${srcs.normal[0]} 1x, ${thumb(bDirs, bFile, 240)} 2x`;
  return { id, dex, name, region, note, gen, group, label, srcs, srcset,
           text: fold(`${label} ${note} ${name} ${region} form`) };
});
const byId = new Map(entries.map(e => [e.id, e]));
