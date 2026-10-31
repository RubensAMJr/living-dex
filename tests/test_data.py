"""Data and file checks that need no browser.

    python -m unittest discover -s tests -v
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def js_value(path, name):
    """The JSON value assigned to `name` in a generated data file (const NAME = ...; or window.NAME = ...;)"""
    text = (ROOT / path).read_text(encoding="utf-8")
    m = re.search(r"(?:const|window\.)\s*" + re.escape(name) + r"\s*=\s*(.*?);\r?\n", text, re.S)
    if not m:
        raise AssertionError(f"{name} not found in {path}")
    return json.loads(m.group(1))


DATA = js_value("data/pokemon.js", "DATA")
GAMES = js_value("data/info-data.js", "DEX_GAMES")
INFO = js_value("data/info-data.js", "DEX_INFO")
ABILITIES = js_value("data/info-data.js", "DEX_ABILITIES")


def locations(game):
    text = (ROOT / "data" / "locations" / f"{game}.js").read_text(encoding="utf-8")
    return json.loads(re.search(r'= (\{.*\});\r?\n?$', text, re.S).group(1))


class PokemonList(unittest.TestCase):
    def test_count_and_unique_ids(self):
        ids = [row[0] for row in DATA]
        self.assertEqual(len(ids), 1082)               # 1,025 species + 57 regional forms
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({row[1] for row in DATA}, set(range(1, 1026)))

    def test_every_entry_has_artwork_names(self):
        for row in DATA:
            self.assertEqual(len(row), 9, row[0])
            self.assertTrue(row[5].endswith(".png"), row[0])   # Bulbapedia file
            self.assertTrue(row[6], row[0])                    # Serebii code
            self.assertTrue(row[8], row[0])                    # imgbb shiny id


class PokedexData(unittest.TestCase):
    def test_same_entries_as_the_list(self):
        self.assertEqual(set(INFO), {row[0] for row in DATA})

    def test_types_stats_abilities(self):
        for eid, v in INFO.items():
            self.assertTrue(1 <= len(v.get("t", [])) <= 2, eid)
            self.assertEqual(len(v.get("s", [])), 6, eid)
            for ability in v.get("a", []):
                self.assertIn(str(ability[0]), ABILITIES, eid)

    def test_game_indexes(self):
        self.assertEqual(len(GAMES), 38)
        for eid, v in INFO.items():
            found, evolve = set(v.get("f", [])), set(v.get("v", []))
            self.assertTrue(found <= set(range(38)) and evolve <= set(range(38)), eid)
            self.assertFalse(found & evolve, f"{eid}: a game is both 'found' and 'by evolving'")

    def test_known_cases(self):
        gi = GAMES.index
        # Camerupt in Ruby: only by evolving Numel (the bug that started the evolve-only badges)
        self.assertIn(gi("ruby"), INFO["323"].get("v", []))
        # event-only Pokémon are not listed as found (Mew on Faraway Island, Celebi in Ruby)
        self.assertNotIn(gi("emerald"), INFO["151"].get("f", []))
        self.assertNotIn(gi("ruby"), INFO["251"].get("f", []))


class GameRoutes(unittest.TestCase):
    def test_every_catchable_pokemon_is_on_a_route(self):
        for gi, game in enumerate(GAMES):
            with self.subTest(game=game):
                loc = locations(game)
                listed = {row[0] for _, places in loc["regions"] for _, groups in places for _, _, rows in groups for row in rows}
                found = {eid for eid, v in INFO.items() if gi in v.get("f", [])}
                self.assertEqual(sorted(found - listed), [], "catchable but on no route")
                self.assertEqual(sorted(listed - found), [], "on a route but not catchable")


class SiteFiles(unittest.TestCase):
    def test_everything_index_html_loads_exists(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        refs = re.findall(r'(?:src|href)="([^":#]+)"', html)
        self.assertGreater(len(refs), 20)
        for ref in refs:
            self.assertTrue((ROOT / ref).is_file(), ref)

    def test_files_loaded_later_exist(self):
        js = "".join(p.read_text(encoding="utf-8") for p in (ROOT / "js").glob("*.js"))
        self.assertIn('"data/info-places.js"', js)
        self.assertTrue((ROOT / "data" / "info-places.js").is_file())
        for game in GAMES:
            self.assertTrue((ROOT / "data" / "locations" / f"{game}.js").is_file(), game)
        for icon in re.findall(r'"(icons/[^"]+)"', js):
            self.assertTrue((ROOT / icon).is_file(), icon)
        self.assertTrue((ROOT / "sw.js").is_file())

    def test_published_folders_not_ignored(self):
        ignored = [l.strip() for l in (ROOT / ".assetsignore").read_text(encoding="utf-8").splitlines()
                   if l.strip() and not l.startswith("#")]
        for folder in ("css/", "js/", "data/", "icons/", "index.html", "sw.js"):
            self.assertNotIn(folder, ignored)
        for private in ("tools/", "tests/"):
            self.assertIn(private, ignored)


if __name__ == "__main__":
    unittest.main()
