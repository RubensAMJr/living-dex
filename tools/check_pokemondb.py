"""Accuracy check: compares info-data.js with the "Where to find" tables on pokemondb.net.

For every species (regional forms are skipped, pokemondb lists them on the base page) and every game it reports
where the two disagree:  found / evolve / miss.  Pages are cached in tools/cache/pdb/.

    py tools/check_pokemondb.py report.tsv
"""
import csv
import json
import re
import sys
from pathlib import Path

from pokemondb import page, where

ROOT = Path(__file__).resolve().parents[1]


def main(report):
    data = (ROOT / "info-data.js").read_text(encoding="utf-8")
    games = json.loads(re.search(r"window.DEX_GAMES = (.*?);\n", data).group(1))
    info = json.loads(re.search(r"window.DEX_INFO = (.*?);\n", data).group(1))
    names = {r["pokemon_species_id"]: r["name"] for r in csv.DictReader(open(ROOT / "tools/data/species_names_en.csv", encoding="utf-8"))
             if r["local_language_id"] == "9"}
    rows = []
    for eid, v in info.items():
        if not eid.isdigit():
            continue
        name = names[eid]
        try:
            theirs = where(page(name))
        except Exception as err:  # noqa: BLE001
            rows.append([eid, name, "", "fetch error", str(err), ""])
            continue
        for gi, g in enumerate(games):
            mine = "found" if gi in v.get("f", []) else "evolve" if gi in v.get("v", []) else "miss"
            state, text = theirs.get(g, ("absent", ""))
            if state in ("absent", "unknown") or state == mine or (state == "breed" and mine == "miss"):
                continue
            rows.append([eid, name, g, mine, state, text])
    with open(report, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["id", "name", "game", "mine", "pokemondb", "pokemondb text"])
        w.writerows(rows)
    print(len(rows), "disagreements")


if __name__ == "__main__":
    main(sys.argv[1])
