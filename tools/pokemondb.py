"""pokemondb.net "Where to find" tables: a third source, used where PokéAPI and Serebii found nothing.

They list things the other two miss: White Forest, Black/White swarms, fossil revivals, in-game trades,
the Bug-Catching Contest, and some legendaries (Giratina in Diamond/Pearl, the Regis in Platinum).
Pages are cached in tools/cache/pdb/.
"""
import re
import time
import unicodedata
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "cache" / "pdb"
UA = "living-dex-checklist accuracy check (personal project; github.com/RubensAMJr/living-dex)"

# places that only ever had event Pokémon (distributions, tickets, Mystery Gift)
EVENT_PLACES = re.compile(r"Pok[eé] ?mart|Pok[eé] ?center|Navel Rock|Birth Island|Faraway Island|Southern Island|"
                          r"Liberty Garden|Newmoon Island|Flower Paradise|Hall of Origin", re.I)
# event-only finds pokemondb lists as ordinary places: (species id, game)
EVENT_FINDS = {(172, "heartgold"), (172, "soulsilver"),                 # Spiky-eared Pichu
               (380, "heartgold"), (380, "soulsilver"), (381, "heartgold"), (381, "soulsilver")}  # Enigma Stone


def slug(name):
    name = name.replace("♀", "-f").replace("♂", "-m")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[.':]", "", name.lower())
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def page(name):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{slug(name)}.html"
    if not path.exists():
        req = urllib.request.Request(f"https://pokemondb.net/pokedex/{slug(name)}", headers={"User-Agent": UA})
        path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        time.sleep(0.8)
    return path.read_text(encoding="utf-8")


def where(html):
    """{game id: ("found" | "breed" | "evolve" | "miss" | "unknown", text)}"""
    i = html.find("Where to find")
    j = html.find("</table>", i)
    out = {}
    for th, td in re.findall(r"<th>(.*?)</th>\s*<td>(.*?)</td>", html[i:j], re.S):
        text = " ".join(re.sub(r"<[^>]+>", " ", td).split()).replace(" ,", ",")
        state = ("evolve" if text.startswith("Evolve") else
                 "breed" if text.startswith("Breed") else
                 "miss" if text.startswith(("Trade/migrate", "Not available")) else
                 "unknown" if "not yet available" in text else "found")
        for g in re.findall(r'class="igame ([a-z0-9-]+)"', th):
            out[g] = (state, text)
    return out


def apply(info, names):
    """Adds pokemondb finds for games where an entry has none. Returns [(entry id, game, text)] added."""
    added = []
    for eid, v in info.items():
        if not eid.isdigit():
            continue          # pokemondb lists regional forms on the base species' page
        d = int(eid)
        forms = [x for k, x in info.items() if k != eid and re.match(r"\d+", k).group() == eid]
        for game, (state, text) in where(page(names[d])).items():
            if state != "found" or game in v["g"] or (d, game) in EVENT_FINDS or EVENT_PLACES.search(text):
                continue
            if any(game in x["g"] for x in forms):
                continue      # the find is probably the regional form's
            v["g"][game] = [["Other", text, ""]]
            v["n"].pop(game, None)
            added.append((eid, game, text))
    return added
