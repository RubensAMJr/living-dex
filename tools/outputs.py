"""Writes the two data files used by the detail panel.

info-data.js   (loads with the page, small): types, base stats, abilities, evolutions, the games each entry
               is found in, the games it can be obtained in by evolving, and why it isn't found elsewhere.
info-places.js (loads the first time you hover/tap a game badge): where exactly, per game, grouped by
               method, at most 8 places per method, each distinct text stored once.
"""
import json
import re

GAMES = ["red", "blue", "yellow", "gold", "silver", "crystal", "ruby", "sapphire", "emerald", "firered", "leafgreen",
         "diamond", "pearl", "platinum", "heartgold", "soulsilver", "black", "white", "black-2", "white-2", "x", "y",
         "omega-ruby", "alpha-sapphire", "sun", "moon", "ultra-sun", "ultra-moon", "lets-go-pikachu", "lets-go-eevee",
         "sword", "shield", "brilliant-diamond", "shining-pearl", "legends-arceus", "scarlet", "violet", "legends-za"]
GI = {g: i for i, g in enumerate(GAMES)}

# highest National Dex number that exists in each game (games with a limited Pokédex use regional dex lists)
MAX_DEX = {**dict.fromkeys(["red", "blue", "yellow"], 151), **dict.fromkeys(["gold", "silver", "crystal"], 251),
           **dict.fromkeys(["ruby", "sapphire", "emerald", "firered", "leafgreen"], 386),
           **dict.fromkeys(["diamond", "pearl", "platinum", "heartgold", "soulsilver", "brilliant-diamond", "shining-pearl"], 493),
           **dict.fromkeys(["black", "white", "black-2", "white-2"], 649),
           **dict.fromkeys(["x", "y", "omega-ruby", "alpha-sapphire"], 721),
           **dict.fromkeys(["sun", "moon", "ultra-sun", "ultra-moon"], 807)}
LIMITED = {"lets-go-pikachu": ["letsgo-kanto"], "lets-go-eevee": ["letsgo-kanto"],
           "sword": ["galar", "isle-of-armor", "crown-tundra"], "shield": ["galar", "isle-of-armor", "crown-tundra"],
           "legends-arceus": ["hisui"], "scarlet": ["paldea", "kitakami", "blueberry"],
           "violet": ["paldea", "kitakami", "blueberry"], "legends-za": ["lumiose-city"]}


def dex_of(eid):
    return int(re.match(r"\d+", eid).group())


def in_game(eid, game, regional):
    d = dex_of(eid)
    if game in LIMITED:
        return any(d in regional.get(dex, set()) for dex in LIMITED[game])
    return d <= MAX_DEX[game]


def evolve_games(info, regional):
    """Games where an entry isn't found but a pre-evolution is, and the entry exists in that game."""
    out = {}
    for eid, v in info.items():
        games = []
        for game in GAMES:
            if game in v["g"] or not in_game(eid, game, regional):
                continue
            seen, todo = set(), [p for p, _ in v.get("e", {}).get("f", [])]
            while todo:
                p = todo.pop()
                if p in seen or p not in info:
                    continue
                seen.add(p)
                if game in info[p]["g"]:
                    games.append(GI[game])
                    break
                todo += [pp for pp, _ in info[p].get("e", {}).get("f", [])]
        if games:
            out[eid] = games
    return out


def place_text(finds):
    """[[method, place, level], ...] -> 'Wild: Route 1, Route 2 (Lv 2–5) · Gift: Pallet Town (Lv 5)'"""
    by_method = {}
    for method, place, lv in finds:
        m = by_method.setdefault(method, {"places": [], "lv": []})
        for p in [x.strip() for x in place.split(",")] if len(place) > 60 else [place]:
            if p and p not in m["places"]:
                m["places"].append(p)
        nums = [int(n) for n in re.findall(r"\d+", lv or "")]
        m["lv"] += nums
    parts = []
    for method, m in by_method.items():
        shown = m["places"][:8]
        more = len(m["places"]) - len(shown)
        text = ", ".join(shown) + (f" +{more} more" if more > 0 else "")
        if m["lv"]:
            lo, hi = min(m["lv"]), max(m["lv"])
            text += f" (Lv {lo})" if lo == hi else f" (Lv {lo}–{hi})"
        parts.append(text if method == "Other" else f"{method}: {text}")  # pokemondb doesn't say how
    return " · ".join(parts)


def write(root, info, abilities, regional):
    evo = evolve_games(info, regional)
    core, strings, index, places = {}, [], {}, {}
    for eid, v in info.items():
        c = {k: v[k] for k in ("t", "s", "a", "e", "n") if v.get(k)}
        if c.get("n"):
            c["n"] = {GI[g]: why for g, why in c["n"].items() if g in GI}
        found = [GI[g] for g in GAMES if g in v["g"]]
        if found:
            c["f"] = found
        if eid in evo:
            c["v"] = evo[eid]
        core[eid] = c
        rows = []
        for g in GAMES:
            if g in v["g"]:
                text = place_text(v["g"][g])
                if text not in index:
                    index[text] = len(strings)
                    strings.append(text)
                rows.append([GI[g], index[text]])
        if rows:
            places[eid] = rows
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    head = "// Generated by tools/fetch_info.py - do not edit by hand\n"
    (root / "info-data.js").write_text(
        head + f"window.DEX_GAMES = {dump(GAMES)};\nwindow.DEX_INFO = {dump(core)};\nwindow.DEX_ABILITIES = {dump(abilities)};\n", encoding="utf-8")
    (root / "info-places.js").write_text(
        head + f"window.DEX_PLACES = {{s:{dump(strings)},d:{dump(places)}}};\n", encoding="utf-8")
    return evo
