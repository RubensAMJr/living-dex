"""Evolution data for the detail panel: how each checklist entry evolves, and from what.

Used by tools/fetch_info.py. Reads PokéAPI's evolution rows (one per method per game group) and turns
them into short English text such as "Level 16", "Thunder Stone", "Trade holding Metal Coat" or
"Level up with high friendship at night". Regional forms get their own evolutions where PokéAPI says
a rule needs or produces a regional form (Galarian Linoone -> Obstagoon, Pikachu -> Alolan Raichu).
"""
import re

REGION_NAME = {1: "Kanto", 2: "Johto", 3: "Hoenn", 4: "Sinnoh", 5: "Unova", 6: "Kalos", 7: "Alola", 8: "Galar", 9: "Hisui", 10: "Paldea"}
REGION_SUFFIX = {"alola": "Alolan", "galar": "Galarian", "hisui": "Hisuian", "paldea": "Paldean"}
TRIGGER_TEXT = {
    "shed": "Level 20 with an empty party slot and a spare Poké Ball",
    "spin": "Spin around while holding a Sweet",
    "tower-of-darkness": "Clear the Tower of Darkness",
    "tower-of-waters": "Clear the Tower of Waters",
    "three-critical-hits": "Land 3 critical hits in one battle",
    "take-damage": "Lose 49+ HP, then walk under the Dusty Bowl rock arch",
    "recoil-damage": "Lose 294+ HP from recoil without fainting",
    "gimmighoul-coins": "Collect 999 Gimmighoul Coins",
    "agile-style-move": "Use {move} 20 times in Agile Style",
    "strong-style-move": "Use {move} 20 times in Strong Style",
    "use-move": "Use {move} {count} times",
    "other": "Special condition",
}


def region_of(form_name):
    """'linoone-galar' -> 'Galarian', 'raichu-alola' -> 'Alolan', anything else -> ''"""
    if not form_name:
        return ""
    for suffix, region in REGION_SUFFIX.items():
        if re.search(rf"-{suffix}(-|$)", form_name):
            return region
    return ""


def fetch(gql):
    rows = gql("""{ pokemonevolution { evolved_species_id min_level min_happiness min_affection min_beauty time_of_day
        needs_overworld_rain turn_upside_down relative_physical_stats gender_id held_item_id evolution_item_id known_move_id
        known_move_type_id party_species_id party_type_id trade_species_id min_steps min_move_count min_damage_taken
        needs_multiplayer region_id used_move_id evolutiontrigger { name } location_id
        required_pokemon_form { name } evolved_pokemon_form { name } } }""")["pokemonevolution"]
    species = gql("{ pokemonspecies(where:{id:{_lte:1025}}) { id evolves_from_species_id } }")["pokemonspecies"]
    ids = lambda key: sorted({r[key] for r in rows if r[key]})
    items = {i["item_id"]: i["name"] for i in gql("{ itemname(where:{language_id:{_eq:9}, item_id:{_in:%s}}) { item_id name } }"
                                                  % (ids("held_item_id") + ids("evolution_item_id")))["itemname"]}
    moves = {m["move_id"]: m["name"] for m in gql("{ movename(where:{language_id:{_eq:9}, move_id:{_in:%s}}) { move_id name } }"
                                                 % (ids("known_move_id") + ids("used_move_id")))["movename"]}
    types = {t["type_id"]: t["name"] for t in gql("{ typename(where:{language_id:{_eq:9}, type_id:{_in:%s}}) { type_id name } }"
                                                 % (ids("known_move_type_id") + ids("party_type_id")))["typename"]}
    places = {p["location_id"]: p["name"] for p in gql("{ locationname(where:{language_id:{_eq:9}, location_id:{_in:%s}}) { location_id name } }"
                                                      % ids("location_id"))["locationname"]}
    parent = {s["id"]: s["evolves_from_species_id"] for s in species}
    return rows, parent, {"item": items, "move": moves, "type": types, "place": places}


def describe(r, names, species_name):
    """One evolution row -> (text, location or None). Locations are returned separately so
    'level up at a special place' rules from different games can be merged into one line."""
    trig = r["evolutiontrigger"]["name"]
    item = names["item"].get(r["evolution_item_id"]) if r["evolution_item_id"] else None
    held = names["item"].get(r["held_item_id"]) if r["held_item_id"] else None
    move = names["move"].get(r["known_move_id"]) if r["known_move_id"] else None
    used = names["move"].get(r["used_move_id"]) if r["used_move_id"] else None
    if trig == "use-item":
        text = item or "Use an item"
    elif trig == "trade":
        text = "Trade"
        if r["trade_species_id"]:
            text += f" for {species_name(r['trade_species_id'])}"
    elif trig == "level-up":
        text = f"Level {r['min_level']}" if r["min_level"] else "Level up"
    else:
        text = TRIGGER_TEXT.get(trig, trig.replace("-", " ").capitalize()).format(move=used or move or "a move", count=r["min_move_count"] or 20)
    extra = []
    if held:
        extra.append(f"holding {held}")
    if r["min_happiness"]:
        extra.append("with high friendship")
    if r["min_affection"]:
        extra.append("with high affection")
    if r["min_beauty"]:
        extra.append("with high Beauty")
    if move and trig in ("level-up", "use-item", "trade"):
        extra.append(f"knowing {move}")
    if r["known_move_type_id"]:
        extra.append(f"knowing a {names['type'].get(r['known_move_type_id'], '?')}-type move")
    if r["party_species_id"]:
        extra.append(f"with {species_name(r['party_species_id'])} in the party")
    if r["party_type_id"]:
        extra.append(f"with a {names['type'].get(r['party_type_id'], '?')}-type Pokémon in the party")
    if r["relative_physical_stats"] is not None:
        extra.append({1: "if Attack > Defense", -1: "if Attack < Defense", 0: "if Attack = Defense"}[r["relative_physical_stats"]])
    if r["needs_overworld_rain"]:
        extra.append("while it's raining")
    if r["turn_upside_down"]:
        extra.append("with the console held upside down")
    if r["time_of_day"]:
        extra.append({"day": "during the day", "night": "at night", "dusk": "at dusk"}.get(r["time_of_day"], f"({r['time_of_day']})"))
    if r["gender_id"]:
        extra.append({1: "(female only)", 2: "(male only)"}.get(r["gender_id"], ""))
    if r["min_steps"]:
        extra.append(f"after walking {r['min_steps']} steps with it following you")
    if r["min_damage_taken"] and trig != "take-damage":
        extra.append(f"after taking {r['min_damage_taken']}+ damage")
    if r["region_id"] in REGION_NAME:
        extra.append(f"in {REGION_NAME[r['region_id']]}")
    if r["needs_multiplayer"]:
        extra.append("in a Union Circle")
    place = names["place"].get(r["location_id"]) if r["location_id"] else None
    return " ".join([text] + [e for e in extra if e]), place


def build(gql, ents, species_names):
    """-> { entry id: {"f": [[parent entry id, text]], "i": [[child entry id, text]]} }"""
    rows, parent, names = fetch(gql)
    by_species_region = {(d, region): eid for eid, d, region, _ in ents}
    # PokéAPI's three Paldean Tauros breeds don't evolve, so the plain "Paldean" key can stay ambiguous
    dex_name = species_names

    def entry(d, region):
        return by_species_region.get((d, region)) or by_species_region.get((d, ""))

    def label_of(d):
        return dex_name.get(d) or f"#{d}"

    methods = {}   # (parent entry, child entry) -> {"texts": [...], "places": [...]}
    for r in rows:
        child = r["evolved_species_id"]
        par = parent.get(child)
        if not par or child > 1025:
            continue
        req_region = region_of(r["required_pokemon_form"]["name"] if r["required_pokemon_form"] else "")
        out_region = region_of(r["evolved_pokemon_form"]["name"] if r["evolved_pokemon_form"] else "")
        # e.g. Pikachu -> Alolan Raichu: plain parent, regional child; Galarian Linoone -> Obstagoon: regional parent
        p_entry = entry(par, req_region)
        c_entry = entry(child, out_region) if out_region else (entry(child, req_region) if req_region else entry(child, ""))
        if not p_entry or not c_entry:
            continue
        text, place = describe(r, names, label_of)
        m = methods.setdefault((p_entry, c_entry), {"texts": [], "places": []})
        if place and text == "Level up":
            m["places"].append(place)           # merged below into one "Level up at A, B, C"
        else:
            m["texts"].append(f"{text} at {place}" if place else text)
    evo = {}
    for (p_entry, c_entry), m in methods.items():
        parts = list(dict.fromkeys(m["texts"]))
        if m["places"]:
            parts.append("Level up at " + ", ".join(dict.fromkeys(m["places"])))
        how = " or ".join(parts[:4]) + (f" (+{len(parts) - 4} more)" if len(parts) > 4 else "")
        evo.setdefault(p_entry, {"f": [], "i": []})["i"].append([c_entry, how])
        evo.setdefault(c_entry, {"f": [], "i": []})["f"].append([p_entry, how])
    return evo
