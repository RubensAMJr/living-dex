"""Build index.html from src/index.template.html.

Usage (from anywhere):  python tools/build.py

Fills the template's  /*__DATA__*/[]  placeholder with one row per checklist entry:
species 1-1025 plus the Alolan, Galarian, Hisuian and Paldean forms.
"""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "src" / "index.template.html"
OUTPUT = ROOT / "index.html"
NAMES_CSV = ROOT / "tools" / "data" / "species_names_en.csv"   # English names from PokéAPI's CSV dump
IMGBB_IDS = ROOT / "tools" / "data" / "imgbb_ids.txt"          # shiny art thumbnails, one per entry, in order

names = {}
with open(NAMES_CSV, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        names[int(row["pokemon_species_id"])] = row["name"]
assert len(names) == 1025

# Bulbapedia artwork file name tweaks (curly apostrophe -> straight, no colon)
BULB_OVERRIDE = {29: "Nidoran", 32: "Nidoran", 439: "Mime Jr", 978: "Tatsugiri-Curly"}


def bulb_name(name, dex=None):
    if dex in BULB_OVERRIDE:
        return BULB_OVERRIDE[dex]
    return name.replace("’", "'").replace(":", "")


# (dex, region label, bulbapedia suffix, serebii suffix)
REGIONAL = []
for d in (19, 20, 26, 27, 28, 37, 38, 50, 51, 52, 53, 74, 75, 76, 88, 89, 103, 105):
    REGIONAL.append((d, "Alolan", "-Alola", "-a"))
for d in (52, 77, 78, 79, 80, 83, 110, 122, 144, 145, 146, 199, 222, 263, 264, 554, 555, 562, 618):
    REGIONAL.append((d, "Galarian", "-Galar", "-g"))
for d in (58, 59, 100, 101, 157, 211, 215, 503, 549, 570, 571, 628, 705, 706, 713, 724):
    REGIONAL.append((d, "Hisuian", "-Hisui", "-h"))
REGIONAL += [
    (128, "Paldean", "-Paldea Combat", "-p"),
    (128, "Paldean", "-Paldea Blaze", "-b"),
    (128, "Paldean", "-Paldea Aqua", "-a"),
    (194, "Paldean", "-Paldea", "-p"),
]
TAUROS_NOTE = {"-Paldea Combat": "Combat Breed", "-Paldea Blaze": "Blaze Breed", "-Paldea Aqua": "Aqua Breed"}


def bulb_path(fname):
    """Bulbapedia (MediaWiki) stores files under md5-based folders: f/fb/0001Bulbasaur.png"""
    fname = fname.replace(" ", "_")
    h = hashlib.md5(fname.encode("utf-8")).hexdigest()
    return f"{h[0]}/{h[:2]}/{fname}"


forms_by_dex = {}
for d, region, bsuf, ssuf in REGIONAL:
    forms_by_dex.setdefault(d, []).append((region, bsuf, ssuf))

# Shiny art on Bulbapedia = Pokémon HOME renders: HOME0019_s.png, HOME0019A_s.png, HOME0128PC_s.png
HOME_REGION = {"Alolan": "A", "Galarian": "G", "Hisuian": "H", "Paldean": "P"}


def home_suffix(d, region, bsuf):
    if not region:
        return ""
    if d == 128:
        return "P" + bsuf.split()[-1][0]  # PC / PB / PA
    return HOME_REGION[region]


entries = []
for d in range(1, 1026):
    n = names[d]
    entries.append({"id": f"{d}", "dex": d, "name": n, "region": "", "note": "",
                    "b": bulb_path(f"{d:04d}{bulb_name(n, d)}.png"), "s": f"{d:03d}",
                    "sh": bulb_path(f"HOME{d:04d}_s.png")})
    for region, bsuf, ssuf in forms_by_dex.get(d, []):
        entries.append({"id": f"{d}{ssuf}" if d != 128 else f"{d}{bsuf.split()[-1][0].lower()}",
                        "dex": d, "name": n, "region": region, "note": TAUROS_NOTE.get(bsuf, ""),
                        "b": bulb_path(f"{d:04d}{bulb_name(n)}{bsuf}.png"), "s": f"{d:03d}{ssuf}",
                        "sh": bulb_path(f"HOME{d:04d}{home_suffix(d, region, bsuf)}_s.png")})

ids = [e["id"] for e in entries]
assert len(ids) == len(set(ids)), "duplicate ids"
imgbb = IMGBB_IDS.read_text(encoding="utf-8").strip().split(",")
assert len(imgbb) == len(entries), (len(imgbb), len(entries))

# Compact rows: [id, dex, name, region, note, bulbapedia path, serebii code, bulbapedia shiny hash dir, imgbb shiny id]
rows = [[e["id"], e["dex"], e["name"], e["region"], e["note"], e["b"], e["s"], e["sh"][:4], ib]
        for e, ib in zip(entries, imgbb)]
template = TEMPLATE.read_text(encoding="utf-8")
assert template.count("/*__DATA__*/[]") == 1
OUTPUT.write_text(template.replace("/*__DATA__*/[]", json.dumps(rows, ensure_ascii=False, separators=(",", ":"))),
                  encoding="utf-8")  # platform line endings (CRLF on Windows), as the committed file has
print(f"{OUTPUT.name}: {len(entries)} entries ({len(entries) - 1025} regional forms)")
