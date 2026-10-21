"""One-off patch: tools/fetch_info.py also collects base stats and abilities (with in-game descriptions)."""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "fetch_info.py"
s = P.read_text(encoding="utf-8")


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old))
    s = s.replace(old, new)


rep('''{ pokemon(where:{id:{_in:%s}}) { id pokemontypes(order_by:{slot:asc}) { type { name } } }''',
    '''{ pokemon(where:{id:{_in:%s}}) { id pokemontypes(order_by:{slot:asc}) { type { name } }
            pokemonstats(order_by:{stat_id:asc}) { base_stat } pokemonabilities(order_by:{slot:asc}) { is_hidden ability_id } }''')
rep('''            info[eid_for[p["id"]]]["t"] = [t["type"]["name"] for t in p["pokemontypes"]]''',
    '''            x = info[eid_for[p["id"]]]
            x["t"] = [t["type"]["name"] for t in p["pokemontypes"]]
            x["s"] = [st["base_stat"] for st in p["pokemonstats"]]  # HP, Atk, Def, SpA, SpD, Spe
            x["a"] = [[ab["ability_id"], 1] if ab["is_hidden"] else [ab["ability_id"]] for ab in p["pokemonabilities"]]''')
rep('''    return info, regional''', '''    # ability names + in-game descriptions, shared by every Pokémon (kept once in DEX_ABILITIES)
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
    return info, regional, abilities''')
rep('''    info, regional = pokeapi(ents)''', '''    info, regional, abilities = pokeapi(ents)''')
rep('''json.dumps(info, ensure_ascii=False, separators=(",", ":")) + ";\\n"''',
    '''json.dumps(info, ensure_ascii=False, separators=(",", ":")) + ";\\nwindow.DEX_ABILITIES = " + \\
         json.dumps(abilities, ensure_ascii=False, separators=(",", ":")) + ";\\n"''')
P.write_text(s, encoding="utf-8")
print("ok")
