"""Build info-data.js: types and where-to-find data for every checklist entry (species + regional forms).

Usage:  python tools/fetch_info.py            (all 1,082 entries)
        python tools/fetch_info.py --refresh  (ignore the Serebii page cache)

Sources
- PokéAPI GraphQL (graphql.pokeapi.co/v1beta2): types for every entry, and wild/gift encounters for
  Red/Blue ... Sword/Shield + DLC (it has no usable data for the newer games, and ORAS is incomplete).
- Serebii Pokédex pages, for Omega Ruby/Alpha Sapphire (pokedex-xy), Brilliant Diamond/Shining Pearl and
  Legends: Arceus (pokedex-swsh), Scarlet/Violet + DLC and Legends: Z-A (pokedex-sv). Pages are cached in
  tools/cache/ so a re-run only downloads what is missing.
- pokemondb.net "Where to find" tables, only for games where the two above found nothing (White Forest,
  swarms, fossils, in-game trades, ...). Cached in tools/cache/pdb/.
- tools/data/overrides.json: hand corrections, applied last.

"Found" means obtainable in that game itself in the wild, as an in-game gift or fossil, or by in-game
trade (incl. raids/static encounters). Trading with other games, events, breeding and evolving don't count.

Output (window.DEX_INFO):
  { "<entry id>": { "t": [types], "g": { game: [[method, place, level], ...] }, "n": { game: "why not found" } } }
"""
import concurrent.futures as cf
import csv
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-data.js"
CACHE = ROOT / "tools" / "cache"
OVERRIDES = ROOT / "tools" / "data" / "overrides.json"
NAMES_CSV = ROOT / "tools" / "data" / "species_names_en.csv"
API = "https://graphql.pokeapi.co/v1beta2"
UA = "living-dex-checker (personal project; github.com/RubensAMJr/living-dex)"
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
REFRESH = "--refresh" in sys.argv

# ---------------------------------------------------------------- checklist entries (same as tools/build.py)
REGION_FORMS = {
    "Alolan": ("alola", "-a", (19, 20, 26, 27, 28, 37, 38, 50, 51, 52, 53, 74, 75, 76, 88, 89, 103, 105)),
    "Galarian": ("galar", "-g", (52, 77, 78, 79, 80, 83, 110, 122, 144, 145, 146, 199, 222, 263, 264, 554, 555, 562, 618)),
    "Hisuian": ("hisui", "-h", (58, 59, 100, 101, 157, 211, 215, 503, 549, 570, 571, 628, 705, 706, 713, 724)),
}


def entries():
    """[(entry id, species id, region or '', pokeapi form suffix or None)] in checklist order"""
    out = []
    for d in range(1, 1026):
        out.append((str(d), d, "", None))
        for region, (suffix, sid, dexes) in REGION_FORMS.items():
            if d in dexes:
                out.append((f"{d}{sid}", d, region, suffix))
        if d == 128:
            for breed, code in (("combat", "c"), ("blaze", "b"), ("aqua", "a")):
                out.append((f"128{code}", 128, "Paldean", f"paldea-{breed}-breed"))
        if d == 194:
            out.append(("194-p", 194, "Paldean", "paldea"))
    return out


# ---------------------------------------------------------------- PokéAPI
VERSION_MAP = {
    "red": ("red", ""), "blue": ("blue", ""), "yellow": ("yellow", ""),
    "gold": ("gold", ""), "silver": ("silver", ""), "crystal": ("crystal", ""),
    "ruby": ("ruby", ""), "sapphire": ("sapphire", ""), "emerald": ("emerald", ""),
    "firered": ("firered", ""), "leafgreen": ("leafgreen", ""),
    "diamond": ("diamond", ""), "pearl": ("pearl", ""), "platinum": ("platinum", ""),
    "heartgold": ("heartgold", ""), "soulsilver": ("soulsilver", ""),
    "black": ("black", ""), "white": ("white", ""), "black-2": ("black-2", ""), "white-2": ("white-2", ""),
    "x": ("x", ""), "y": ("y", ""),
    "sun": ("sun", ""), "moon": ("moon", ""), "ultra-sun": ("ultra-sun", ""), "ultra-moon": ("ultra-moon", ""),
    "lets-go-pikachu": ("lets-go-pikachu", ""), "lets-go-eevee": ("lets-go-eevee", ""),
    "sword": ("sword", ""), "shield": ("shield", ""),
    "the-isle-of-armor-sword": ("sword", "Isle of Armor: "), "the-isle-of-armor-shield": ("shield", "Isle of Armor: "),
    "the-crown-tundra-sword": ("sword", "Crown Tundra: "), "the-crown-tundra-shield": ("shield", "Crown Tundra: "),
}
METHOD_LABEL = {
    "walk": "Wild", "surf": "Surfing", "old-rod": "Fishing", "good-rod": "Fishing", "super-rod": "Fishing",
    "rock-smash": "Rock Smash", "headbutt": "Headbutt", "dark-grass": "Wild", "grass-spots": "Wild",
    "cave-spots": "Wild", "bridge-spots": "Wild", "super-rod-spots": "Fishing", "surf-spots": "Surfing",
    "yellow-flowers": "Wild", "purple-flowers": "Wild", "red-flowers": "Wild", "rough-terrain": "Wild",
    "gift": "Gift", "gift-egg": "Gift (Egg)", "only-one": "Static", "pokeflute": "Static",
    "squirt-bottle": "Static", "wailmer-pail": "Static", "devon-scope": "Static", "island-scan": "Island Scan",
    "sos-encounter": "SOS", "bubbling-spots": "Fishing", "berry-piles": "Wild", "npc-trade": None,
    "sos-from-bubbling-spot": "SOS", "roaming-grass": "Roaming", "roaming-water": "Roaming",
    "overworld": "Wild", "overworld-special": "Wild", "overworld-flying": "Wild", "overworld-water": "Wild",
    "wanderer": "Wild", "max-raid": "Max Raid", "seaweed": "Wild", "feebas-tile-fishing": "Fishing",
}


def gql(query):
    for attempt in range(4):
        try:
            req = urllib.request.Request(API, data=json.dumps({"query": query}).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": UA})
            data = json.load(urllib.request.urlopen(req, timeout=180))
            if "errors" in data:
                raise SystemExit(data["errors"])
            return data["data"]
        except (urllib.error.URLError, TimeoutError) as err:
            print(f"  PokéAPI retry {attempt + 1}: {err}")
            time.sleep(3 * (attempt + 1))
    raise SystemExit("PokéAPI unreachable")


def pokeapi(ents):
    print("PokéAPI: species and forms ...")
    species = gql("{ pokemonspecies(where:{id:{_lte:1025}}) { id name } }")["pokemonspecies"]
    slug = {s["id"]: s["name"] for s in species}
    defaults = gql("{ pokemon(where:{is_default:{_eq:true}, pokemon_species_id:{_lte:1025}}) { id name pokemon_species_id } }")["pokemon"]
    by_species = {p["pokemon_species_id"]: p for p in defaults}
    form_names = {}
    for eid, d, region, suffix in ents:
        if suffix:
            form_names[f"{slug[d]}-{suffix}"] = eid
    form_names["darmanitan-galar-standard"] = "555-g"      # PokéAPI splits Galarian Darmanitan into standard/zen
    forms = gql('{ pokemon(where:{name:{_in:%s}}) { id name } }' % json.dumps(list(form_names)))["pokemon"]
    pid_for = {eid: by_species[d]["id"] for eid, d, region, suffix in ents if not suffix}
    for p in forms:
        pid_for[form_names[p["name"]]] = p["id"]
    missing = [eid for eid, *_ in ents if eid not in pid_for]
    if missing:
        print("  warning: no PokéAPI form for", missing)
    eid_for = {pid: eid for eid, pid in pid_for.items()}
    ids = sorted(eid_for)

    info = {eid: {"t": [], "g": {}, "n": {}} for eid, *_ in ents}
    levels = {}
    for i in range(0, len(ids), 120):
        chunk = ids[i:i + 120]
        d = gql("""{ pokemon(where:{id:{_in:%s}}) { id pokemontypes(order_by:{slot:asc}) { type { name } }
            pokemonstats(order_by:{stat_id:asc}) { base_stat } pokemonabilities(order_by:{slot:asc}) { is_hidden ability_id } }
          encounter(where:{pokemon_id:{_in:%s}}) { pokemon_id version { name } min_level max_level
            encounterslot { encountermethod { name } }
            locationarea { location { name locationnames(where:{language_id:{_eq:9}}) { name } } } } }""" % (chunk, chunk))
        for p in d["pokemon"]:
            x = info[eid_for[p["id"]]]
            x["t"] = [t["type"]["name"] for t in p["pokemontypes"]]
            x["s"] = [st["base_stat"] for st in p["pokemonstats"]]  # HP, Atk, Def, SpA, SpD, Spe
            x["a"] = [[ab["ability_id"], 1] if ab["is_hidden"] else [ab["ability_id"]] for ab in p["pokemonabilities"]]
        for e in d["encounter"]:
            mapped = VERSION_MAP.get(e["version"]["name"])
            method = METHOD_LABEL.get(e["encounterslot"]["encountermethod"]["name"], "Wild")
            if not mapped or method is None:
                continue
            game, prefix = mapped
            loc = e["locationarea"]["location"]
            place = prefix + (loc["locationnames"][0]["name"] if loc["locationnames"] else loc["name"].replace("-", " ").title())
            eid = eid_for[e["pokemon_id"]]
            if event_only(eid, game, place):
                continue
            key = (eid, game, method, place)
            lo, hi = levels.get(key, (999, 0))
            levels[key] = (min(lo, e["min_level"]), max(hi, e["max_level"]))
        print(f"  {min(i + 120, len(ids))}/{len(ids)} Pokémon")
    for (eid, game, method, place), (lo, hi) in sorted(levels.items(), key=lambda kv: kv[0]):
        lv = f"Lv {lo}" if lo == hi else f"Lv {lo}–{hi}"
        info[eid]["g"].setdefault(game, []).append([method, place, lv])

    dexes = gql("""{ pokedex(where:{name:{_in:["hisui","paldea","kitakami","blueberry","lumiose-city","original-sinnoh","extended-sinnoh","letsgo-kanto","galar","isle-of-armor","crown-tundra"]}}) {
        name pokemondexnumbers { pokemon_species_id } } }""")["pokedex"]
    regional = {x["name"]: {n["pokemon_species_id"] for n in x["pokemondexnumbers"]} for x in dexes}
    # ability names + in-game descriptions, shared by every Pokémon (kept once in DEX_ABILITIES)
    ability_ids = sorted({a[0] for v in info.values() for a in v.get("a", [])})
    rows = gql("""{ ability(where:{id:{_in:%s}}) { id abilitynames(where:{language_id:{_eq:9}}) { name }
        abilityflavortexts(where:{language_id:{_eq:9}}, order_by:{version_group_id:desc}, limit:1) { flavor_text }
        abilityeffecttexts(where:{language_id:{_eq:9}}) { short_effect } } }""" % ability_ids)["ability"]
    abilities = {}
    for a in rows:
        name = a["abilitynames"][0]["name"] if a["abilitynames"] else f"Ability {a['id']}"
        text = (a["abilityflavortexts"][0]["flavor_text"] if a["abilityflavortexts"] else
                a["abilityeffecttexts"][0]["short_effect"] if a["abilityeffecttexts"] else "")
        abilities[a["id"]] = [name, " ".join(text.split())]
    return info, regional, abilities


def event_only(eid, game, place):
    """PokéAPI encounters that need an event: distribution places, Altering Cave's Mystery Gift Pokémon
    (only Zubat is there without one), and two plain mistakes in its data."""
    from pokemondb import EVENT_PLACES
    return bool(EVENT_PLACES.search(place) or (place == "Altering Cave" and eid != "41")
                or (game == "sun" and place == "New Mauville") or eid == "801")


# ---------------------------------------------------------------- Serebii
SEREBII_GAMES = {
    "Omega Ruby": "omega-ruby", "Alpha Sapphire": "alpha-sapphire",
    "Brilliant Diamond": "brilliant-diamond", "Shining Pearl": "shining-pearl",
    "Legends: Arceus": "legends-arceus", "Scarlet": "scarlet", "Violet": "violet",
    "Legends: Z-A": "legends-za", "Legends: Z-A Mega Dimension": "legends-za",
}
GAME_PREFIX = {"Legends: Z-A Mega Dimension": "Mega Dimension: "}
DLC_PREFIX = {"The Teal Mask": "Teal Mask: ", "The Indigo Disk": "Indigo Disk: ",
              "Isle of Armor": "Isle of Armor: ", "The Crown Tundra": "Crown Tundra: ", "Crown Tundra": "Crown Tundra: "}
FORM_PREFIX = re.compile(r"^\s*(Alolan|Galarian|Hisuian|Paldean|Kantonian|Johtonian|Hoennian|Sinnohan|Unovan|Kalosian|Normal|Regular|Standard)"
                         r"\s+Form\s*:\s*", re.I)
BREED_PREFIX = re.compile(r"^\s*(Combat|Blaze|Aqua)\s+Breed\s*:\s*", re.I)
NOT_FOUND = re.compile(r"^\s*(league club trade|in-game trade|trade|transfer|evolve|breed|hatch|not (available|in game|obtainable)|unobtainable|unavailable|"
                       r"event|distribution|mystery gift|pok[eé]mon home|only (via|through|obtainable)|n/?a\b|via (event|transfer|trade)|"
                       r"link|connect|receive (via|from) (event|home)|serial code|code)", re.I)


def get(url, path):
    if path.exists() and not REFRESH:
        return path.read_text(encoding="latin-1")
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("latin-1")
            path.write_text(text, encoding="latin-1")
            time.sleep(0.15)  # be gentle with Serebii
            return text
        except urllib.error.HTTPError as err:
            if err.code == 404:
                path.write_text("", encoding="latin-1")  # remember: page doesn't exist
                return ""
            print(f"  {url}: HTTP {err.code}, retry {attempt + 1}")
        except (urllib.error.URLError, TimeoutError) as err:
            print(f"  {url}: {err}, retry {attempt + 1}")
        time.sleep(2 * (attempt + 1))
    print(f"  giving up on {url}")
    return ""


def crawl(folder, numbers):
    (CACHE / folder).mkdir(parents=True, exist_ok=True)
    pages = {}

    def one(n):
        name = f"{n:03d}.shtml"
        return n, get(f"https://www.serebii.net/{folder}/{name}", CACHE / folder / name)

    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        for k, (n, text) in enumerate(pool.map(one, numbers), 1):
            pages[n] = text
            if k % 100 == 0 or k == len(numbers):
                print(f"  {folder}: {k}/{len(numbers)}")
    return pages


def clean(fragment):
    text = re.sub(r"<[^>]+>", "", fragment)
    return re.sub(r"\s+", " ", html.unescape(text)).strip(" ,;")


def location_rows(page):
    """[(serebii game label, dlc label or '', [text segments])] from a page's Locations table"""
    # the Locations table's header cell; the bare word also appears earlier in Serebii's menus
    m = re.search(r'<td class="fooevo"[^>]*>\s*(?:<h2>)?\s*Locations(?![A-Za-z])', page)
    if not m:
        return []
    i = m.start()
    j = page.find("</table>", i)
    rows, dlc, dlc_left = [], "", 0
    for tr in re.findall(r"<tr>(.*?)</tr>", page[i:j], re.S):
        cells = re.findall(r"<td([^>]*)>(.*?)</td>", tr, re.S)
        if dlc_left:
            dlc_left -= 1
        else:
            dlc = ""
        game, info = None, None
        for attrs, body in cells:
            text = clean(body)
            m = re.search(r'rowspan="?(\d+)', attrs)
            if m and text in DLC_PREFIX:
                dlc, dlc_left = text, int(m.group(1)) - 1  # the rowspan includes this row
            elif text in SEREBII_GAMES and game is None:
                game = text
            elif 'class="fooinfo"' in attrs and info is None:
                info = body
        if game and info is not None:
            segments = [clean(s) for s in re.split(r"<br\s*/?>", info)]
            rows.append((game, dlc, [s for s in segments if s]))
    return rows


def classify(text):
    t = text.lower()
    if "raid" in t:
        return "Raid"
    if re.search(r"\bgift\b|receive|given|from (professor|prof\.)|obtain from|get from", t):
        return "Gift"
    return "Wild"


def apply_serebii(info, pages_by_folder, ents, regional):
    by_species = {}
    for eid, d, region, suffix in ents:
        by_species.setdefault(d, []).append((eid, region))
    unknown = []
    for folder, pages in pages_by_folder.items():
        for d, page in pages.items():
            if not page:
                continue
            forms = dict((region, eid) for eid, region in by_species.get(d, []))
            for game_label, dlc, segments in location_rows(page):
                game = SEREBII_GAMES[game_label]
                prefix = DLC_PREFIX.get(dlc, "") + GAME_PREFIX.get(game_label, "")
                for seg in segments:
                    target, text = str(d), seg
                    m = FORM_PREFIX.match(seg)
                    if m:
                        form = m.group(1).title()
                        text = seg[m.end():]
                        target = forms.get(form, str(d)) if form in forms else str(d)
                    elif game == "legends-arceus" and "Hisuian" in forms:
                        target = forms["Hisuian"]        # Legends: Arceus only has the Hisuian form of these
                    b = BREED_PREFIX.match(text)
                    if b and d == 128:
                        target = f"128{b.group(1)[0].lower()}"
                        text = text[b.end():]
                    if target not in info:
                        continue
                    if NOT_FOUND.match(text) or not text:
                        info[target]["n"].setdefault(game, text or "Not obtainable")
                        continue
                    if re.search(r"trade|transfer|event", text, re.I) and not re.search(r"route|area|cave|forest|wild|raid|zone|island|city|town|lake|mountain|underground", text, re.I):
                        unknown.append((target, game, text))
                    info[target]["g"].setdefault(game, []).append([classify(text), prefix + text, ""])
    # a game shows as "found" only if at least one finding; drop notes for games that were found after all
    for v in info.values():
        for game in list(v["n"]):
            if game in v["g"]:
                del v["n"][game]
    return unknown


# ---------------------------------------------------------------- main
def main():
    ents = entries()
    assert len(ents) == 1082, len(ents)
    info, regional, abilities = pokeapi(ents)

    print("Serebii: downloading Pokédex pages (cached in tools/cache/) ...")
    pages = {
        "pokedex-xy": crawl("pokedex-xy", range(1, 722)),        # X/Y era pages also list Omega Ruby / Alpha Sapphire
        "pokedex-swsh": crawl("pokedex-swsh", range(1, 906)),    # Sword/Shield era pages also list BDSP and Legends: Arceus
        "pokedex-sv": crawl("pokedex-sv", range(1, 1026)),       # Scarlet/Violet era pages also list Legends: Z-A
    }
    unknown = apply_serebii(info, pages, ents, regional)

    print("pokemondb.net: filling games the other two found nothing in (cached in tools/cache/pdb/) ...")
    import pokemondb
    names = {int(r["pokemon_species_id"]): r["name"] for r in csv.DictReader(open(NAMES_CSV, encoding="utf-8"))}
    from_pdb = pokemondb.apply(info, names)
    print(f"  {len(from_pdb)} games added")

    print("PokéAPI: evolutions ...")
    import evolutions
    species_names = {int(r["pokemon_species_id"]): r["name"] for r in csv.DictReader(open(NAMES_CSV, encoding="utf-8"))}
    evo = evolutions.build(gql, ents, species_names)
    for eid, e in evo.items():
        if eid in info:
            info[eid]["e"] = {k: v for k, v in e.items() if v}

    overrides = json.loads(OVERRIDES.read_text(encoding="utf-8")) if OVERRIDES.exists() else {}
    for eid, games in overrides.items():
        if eid.startswith("_"):
            continue
        for game, finds in games.items():
            if game.startswith("_"):
                continue
            if finds:
                info[eid]["g"][game] = finds
                info[eid]["n"].pop(game, None)
            else:
                info[eid]["g"].pop(game, None)

    for v in info.values():
        if not v["n"]:
            del v["n"]
    import outputs
    evolve = outputs.write(ROOT, info, abilities, regional)
    print(f"evolve-only games added for {len(evolve)} entries")

    # ---- report
    report = {"entries": len(info), "bytes": OUT.stat().st_size}
    games = ["red", "blue", "yellow", "gold", "silver", "crystal", "ruby", "sapphire", "emerald", "firered", "leafgreen",
             "diamond", "pearl", "platinum", "heartgold", "soulsilver", "black", "white", "black-2", "white-2", "x", "y",
             "omega-ruby", "alpha-sapphire", "sun", "moon", "ultra-sun", "ultra-moon", "lets-go-pikachu", "lets-go-eevee",
             "sword", "shield", "brilliant-diamond", "shining-pearl", "legends-arceus", "scarlet", "violet", "legends-za"]
    report["found per game"] = {g: sum(1 for v in info.values() if g in v["g"]) for g in games}
    report["entries without types"] = [e for e, v in info.items() if not v["t"]]
    report["entries found in no game"] = sum(1 for v in info.values() if not v["g"])
    names = {int(r["pokemon_species_id"]): r["name"] for r in csv.DictReader(open(NAMES_CSV, encoding="utf-8"))}
    checks = {"legends-arceus": "hisui", "scarlet": "paldea", "legends-za": "lumiose-city"}
    for game, dex in checks.items():
        in_dex = regional.get(dex, set())
        has = {int(re.match(r"\d+", e).group()) for e, v in info.items() if game in v["g"] or game in v.get("n", {})}
        report[f"{dex} dex species with no {game} row"] = [f"{d} {names[d]}" for d in sorted(in_dex - has)]
    report["texts that mention trade/transfer but were counted as found"] = unknown[:40]
    (ROOT / "tools" / "cache" / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: (v if not isinstance(v, list) or len(v) < 15 else f"{len(v)} items (see tools/cache/report.json)")
                      for k, v in report.items()}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
