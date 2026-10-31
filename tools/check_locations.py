"""Coverage check: for each game, Pokémon the dex data says are found there but that no location lists (and the reverse).

    py tools/check_locations.py report.txt
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(report):
    data = (ROOT / "info-data.js").read_text(encoding="utf-8")
    games = json.loads(re.search(r"window.DEX_GAMES = (.*?);\n", data).group(1))
    info = json.loads(re.search(r"window.DEX_INFO = (.*?);\n", data).group(1))
    lines, summary = [], []
    for gi, game in enumerate(games):
        path = ROOT / "locations" / f"{game}.js"
        if not path.exists():
            summary.append(f"{game:18} NO FILE")
            continue
        loc = json.loads(re.search(r'= (\{.*\});\n$', path.read_text(encoding="utf-8"), re.S).group(1))
        listed = {row[0] for _, places in loc["regions"] for _, groups in places for _, _, rows in groups for row in rows}
        found = {eid for eid, v in info.items() if gi in v.get("f", [])}
        missing, extra = sorted(found - listed), sorted(listed - found)
        n_places = sum(len(places) for _, places in loc["regions"])
        summary.append(f"{game:18} {n_places:4} places  {len(listed):4} Pokémon  dex says {len(found):4}  "
                       f"missing from routes {len(missing):4}  only in routes {len(extra):4}")
        lines.append(f"== {game}\n  missing: {' '.join(missing)}\n  only in routes: {' '.join(extra)}")
    Path(report).write_text("\n".join(summary) + "\n\n" + "\n".join(lines), encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main(sys.argv[1])
