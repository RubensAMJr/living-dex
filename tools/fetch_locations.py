"""Build the per-game location data: every region, route and area of a game with the Pokémon you can catch there.

Usage:  python tools/fetch_locations.py

Source: pokemondb.net location pages (pokemondb.net/location), cached in tools/cache/pdbloc/. Each page lists, per
generation and sub-area, the encounter methods (walking, surfing, fishing, gifts, ...) and for every Pokémon the games,
time of day, season, rarity and levels. What those pages miss (Legends: Z-A entirely, Friend Safari, Max Raids, the
Scarlet/Violet DLC, ...) comes from the per-Pokémon finds that tools/fetch_info.py saves in tools/cache/finds.json.

Output: locations/<game>.js, one per game, loaded by the page only when that game is opened:
  window.DEX_LOC["<game>"] = {
    "regions": [ [region name, [ [location name, [ [area, method, [ [entry id, levels, rarity, times, note], ... ]], ...]], ...]], ...]
  }
"""
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from fetch_info import REGION_FORMS
from pokemondb import EVENT_FINDS, EVENT_PLACES

ROOT = Path(__file__).resolve().parents[1]
HISUIAN = set(REGION_FORMS["Hisuian"][2])
# games where those islands only need another game's save data, not an event
SAVE_BONUS_GAMES = {"brilliant-diamond", "shining-pearl", "omega-ruby", "alpha-sapphire"}
CACHE = ROOT / "tools" / "cache" / "pdbloc"
OUT = ROOT / "locations"
UA = "living-dex-checklist (personal project; github.com/RubensAMJr/living-dex)"

# pokemondb's game codes (cell-loc-game-XX) -> our game ids
CODES = {"R1": "red", "B1": "blue", "Y1": "yellow", "G2": "gold", "S2": "silver", "C2": "crystal",
         "R3": "ruby", "S3": "sapphire", "E3": "emerald", "FR3": "firered", "LG3": "leafgreen",
         "D4": "diamond", "P4": "pearl", "Pt4": "platinum", "HG4": "heartgold", "SS4": "soulsilver",
         "B5": "black", "W5": "white", "B25": "black-2", "W25": "white-2",
         "X6": "x", "Y6": "y", "OR6": "omega-ruby", "AS6": "alpha-sapphire",
         "S7": "sun", "M7": "moon", "US7": "ultra-sun", "UM7": "ultra-moon", "LGP7": "lets-go-pikachu", "LGE7": "lets-go-eevee",
         "Sw8": "sword", "Sh8": "shield", "BD8": "brilliant-diamond", "SP8": "shining-pearl", "LA8": "legends-arceus",
         "S9": "scarlet", "V9": "violet"}
REGIONS = {"kanto": "Kanto", "johto": "Johto", "hoenn": "Hoenn", "sinnoh": "Sinnoh", "unova": "Unova", "kalos": "Kalos",
           "alola": "Alola", "galar": "Galar", "hisui": "Hisui", "paldea": "Paldea"}
FORM_SUFFIX = {"Alolan": "-a", "Galarian": "-g", "Hisuian": "-h"}
# sections that aren't catching: in-game trades (you give a Pokémon away)
SKIP_METHODS = {"Trade"}
RARITY_ICONS = {"Common", "Uncommon", "Rare", "Very rare", "Limited", "One", "Rare (5%)"}


def get(url, path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        time.sleep(0.8)
    return path.read_text(encoding="utf-8")


def text(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def index():
    """[(region slug, location slug, location name)] in pokemondb's order"""
    page = get("https://pokemondb.net/location", CACHE / "_index.html")
    out = []
    for region, body in re.findall(r'<div class="sv-tabs-panel[^"]*" id="loc-([a-z]+)">(.*?)</div>\s*</div>\s*</div>', page, re.S):
        for slug, name in re.findall(r'<a href="/location/([a-z0-9-]+)">(.*?)</a>', body):
            out.append((region, slug, text(name)))
    return out


def entry_id(dex, form):
    if form:
        for word, suffix in FORM_SUFFIX.items():
            if form.startswith(word):
                return f"{dex}{suffix}"
        if form.startswith("Paldean"):
            if dex == 194:
                return "194-p"
            if dex == 128:
                breed = re.search(r"(Combat|Blaze|Aqua)", form)
                return f"128{breed.group(1)[0].lower()}" if breed else "128c"
    return str(dex)


def parse(page):
    """[(area, game, method, [eid, levels, rarity, times, note])] for one location page"""
    rows = []
    # walk the page in order: <h2> = generation (+ sub-area), <h3> = method, then the rows of its table
    tokens = re.finditer(r"<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>|(<tbody>)|<tr>(.*?)</tr>", page, re.S)
    area, method, note = "", "", ""
    for m in tokens:
        h2, h3, tbody, tr = m.groups()
        if h2 is not None:
            title = text(h2)
            area = title.split(" - ", 1)[1] if " - " in title else ""
            continue
        if h3 is not None:
            method, note = text(h3), ""
            continue
        if tbody:
            note = ""                # each group of rows starts without a condition
            continue
        if not method:
            continue
        status = re.search(r'<th[^>]*class="cell-loc-status"[^>]*>(.*?)</th>', tr, re.S)
        if status:
            note = text(status.group(1))   # a condition for the rows below, e.g. "Swarm", "Hoenn Sound", "Post-National Dex"
            continue
        name = re.search(r'title="View Pokedex for #(\d+) [^"]*"', tr)
        if not name:
            continue
        if method in SKIP_METHODS:
            continue
        form = re.search(r'<small class="text-muted">([^<]+)</small>', tr)
        dex = int(name.group(1))
        eid = entry_id(dex, form.group(1) if form else "")
        games = [CODES[c] for c in re.findall(r'cell-loc-game cell-loc-game-([A-Za-z0-9]+)"', tr) if c in CODES]
        games = [g for g in games if (dex, g) not in EVENT_FINDS]
        cells = re.findall(r"<td([^>]*)>(.*?)</td>", tr, re.S)
        icons = re.findall(r'<img class="icon-loc"[^>]*title="([^"]+)"', tr)   # times/seasons, and the rarity icon in older gens
        rarity = re.search(r'<span class="icon-rarity[^"]*">([^<]*)</span>', tr)
        rarity = rarity.group(1) if rarity else next((t for t in icons if t in RARITY_ICONS), "")
        times = [t for t in icons if t not in RARITY_ICONS]
        nums = [text(b) for a, b in cells if "cell-num" in a]
        levels = nums[-1] if nums else ""
        detail = text(cells[-1][1]) if cells else ""
        why = "; ".join(x for x in (note, detail) if x)
        for g in games:
            # Legends: Arceus has only the Hisuian form of these, but pokemondb doesn't label it there
            e = f"{dex}-h" if g == "legends-arceus" and dex in HISUIAN and not form else eid
            rows.append((area, g, method, [e, levels, rarity, times, why]))
    return rows


def main():
    locs = index()
    print(f"{len(locs)} locations")
    per_game = {}          # game -> region -> location -> [(area, method, row)]
    for n, (region, slug, name) in enumerate(locs, 1):
        page = get(f"https://pokemondb.net/location/{slug}", CACHE / f"{slug}.html")
        for area, game, method, row in parse(page):
            if EVENT_PLACES.search(name) and game not in SAVE_BONUS_GAMES:
                continue      # distribution-only islands (Faraway Island, Navel Rock, Newmoon Island, ...)
            per_game.setdefault(game, {}).setdefault(REGIONS.get(region, region.title()), {}).setdefault(name, []).append((area, method, row))
        if n % 50 == 0:
            print(f"  {n}/{len(locs)}", file=sys.stderr)

    finds = ROOT / "tools" / "cache" / "finds.json"
    if finds.exists():
        add_from_finds(per_game, json.loads(finds.read_text(encoding="utf-8")))

    OUT.mkdir(exist_ok=True)
    report = {}
    for game, regions in per_game.items():
        out = []
        for region, places in regions.items():
            loc_list = []
            for place, items in places.items():
                groups = {}
                for area, method, row in items:
                    groups.setdefault((area, method), []).append(row)
                loc_list.append([place, [[a, m, rows] for (a, m), rows in groups.items()]])
            out.append([region, loc_list])
        body = json.dumps({"regions": out}, ensure_ascii=False, separators=(",", ":"))
        (OUT / f"{game}.js").write_text(f'window.DEX_LOC = window.DEX_LOC || {{}};\nwindow.DEX_LOC["{game}"] = {body};\n', encoding="utf-8")
        report[game] = {"locations": sum(len(p) for p in regions.values()),
                        "species": len({row[0] for p in regions.values() for items in p.values() for _, _, row in items})}
    print(json.dumps(report, indent=1))


# the main region of each game, for places the per-Pokémon finds name without one
HOME = {**dict.fromkeys(["red", "blue", "yellow", "firered", "leafgreen", "lets-go-pikachu", "lets-go-eevee"], "Kanto"),
        **dict.fromkeys(["gold", "silver", "crystal", "heartgold", "soulsilver"], "Johto"),
        **dict.fromkeys(["ruby", "sapphire", "emerald", "omega-ruby", "alpha-sapphire"], "Hoenn"),
        **dict.fromkeys(["diamond", "pearl", "platinum", "brilliant-diamond", "shining-pearl"], "Sinnoh"),
        **dict.fromkeys(["black", "white", "black-2", "white-2"], "Unova"), **dict.fromkeys(["x", "y"], "Kalos"),
        **dict.fromkeys(["sun", "moon", "ultra-sun", "ultra-moon"], "Alola"), **dict.fromkeys(["sword", "shield"], "Galar"),
        "legends-arceus": "Hisui", "scarlet": "Paldea", "violet": "Paldea", "legends-za": "Lumiose City"}
# DLC prefixes in the finds ("Teal Mask: Kitakami Road") and the region they become
DLC_REGION = {"Isle of Armor": "Isle of Armor", "Crown Tundra": "Crown Tundra", "Teal Mask": "Kitakami",
              "Indigo Disk": "Blueberry Academy", "Mega Dimension": "Mega Dimension"}


def split_place(text):
    """'Crown Tundra: Ballimere Lake, Frigid Sea' -> [(dlc, place, area)];  'Tera Raid Battles: 5 Star ...' keeps its detail as the area"""
    dlc = ""
    m = re.match(r"^(%s): (.*)$" % "|".join(map(re.escape, DLC_REGION)), text)
    if m:
        dlc, text = m.group(1), m.group(2)
    if ": " in text:                       # "Crimson Mirelands: Massive Mass Outbreak", "Tera Raid Battles: 5 Star Raid Battles, ..."
        place, area = text.split(": ", 1)
        return [(dlc, place.strip(), area.strip())]
    out = []
    for part in re.split(r",\s*(?![^()]*\))", text):
        part = part.strip()
        note = re.search(r"\s*\(([^)]*)\)$", part)
        if note:
            part = part[:note.start()]
        if part:
            out.append((dlc, part, note.group(1) if note else ""))
    return out


def add_from_finds(per_game, finds, games=None):
    """Fill what pokemondb's location pages miss (Friend Safari, Max Raids, DLC areas, Legends: Z-A, ...) from the
    per-Pokémon finds ([[method, place, level], ...]): for each game, every Pokémon the dex data has but no place lists.
    A find goes into the place of the same name when that place exists, otherwise into a new one."""
    for game in games or HOME:
        regions = per_game.setdefault(game, {})
        listed = {row[0] for places in regions.values() for items in places.values() for _, _, row in items}
        where = {fold(name): (region, name) for region, places in regions.items() for name in places}
        for eid, by_game in finds.items():
            if eid in listed:
                continue
            for method, place, lv in by_game.get(game, []):
                for dlc, name, area in split_place(place):
                    key = fold(re.sub(r" or nearby$", "", area)) if area and fold(re.sub(r" or nearby$", "", area)) in where else fold(name)
                    if key in where:
                        region, name = where[key]
                        area = "" if key != fold(name) else area
                    else:
                        region = DLC_REGION.get(dlc) or HOME[game]
                        where[fold(name)] = (region, name)
                    regions.setdefault(region, {}).setdefault(name, []).append((area, method, [eid, lv, "", [], ""]))


def fold(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower().replace("é", "e")).strip()


if __name__ == "__main__":
    main()
