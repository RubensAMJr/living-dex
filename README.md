# 📕 Living Dex Checklist

A one-page Pokémon **living dex** tracker: all 1,025 species in National Dex order, plus the Alolan, Galarian, Hisuian and Paldean forms, with a separate shiny dex.

🌐 **Open it:** https://living-dex.unova.workers.dev/

Everything runs in your browser. There's no account and no server code, and your progress never leaves your device unless you export it.

> **Moving from the old GitHub Pages address?** Progress is saved per address, so it doesn't carry over by itself. On the old site use **☰ → Export backup**, then **☰ → Import backup…** here.

---

## ✨ Features

### ✅ Tracking
- **Tap or click a Pokémon** to mark it caught 🟢 or missing ⚪, with a paint-bucket colour fill animation.
- **Separate shiny dex.** The ✨ button switches between the regular and shiny dex, with a sparkle animation. Each dex keeps its own progress.
- **Progress counters** for the whole dex and for each generation and region.
- **🧢 OT marks** (Menu → *Show OT marks*). Ash's cap on each card marks Pokémon caught by you as the Original Trainer: grey means not yours, coloured means yours. Marking OT also marks the Pokémon as caught.

### 🔍 Finding Pokémon
- **Search** by name, number or region (`25`, `eevee`, `alolan`). Press <kbd>/</kbd> to jump to the search box.
- **Filters:** All · Caught · Missing · *Not OT* (caught Pokémon without your OT mark, shown when OT marks are on).
- **Generation and region chips** (Gen I–IX, Alolan, Galarian, Hisuian, Paldean) to jump to or show one section.
- **Regional forms** get their own sections below the National Dex. You can hide them with the *Regional forms* toggle.

### 🖱️ Selection mode
- Click the **select button**, long-press a card on touch screens, or **drag a box** with the mouse to pick several Pokémon at once.
- The bottom bar lets you **mark caught / missing / OT** for the whole selection. You stay in selection mode afterwards. Click empty space to leave it.

### 📖 Pokédex panel
Hover over a card and tap the green strip with the ⌄ arrow. The card expands into a full Pokédex tile, and the other cards make room for it.
- 🛡️ **Weaknesses:** a full type-matchup table with ×4, ×2, ×½, ×¼ and ×0.
- 🗺️ **Where to find it** in all **38 mainline games**, from Red/Blue to Legends: Z-A:
  - **solid badge:** found in the wild, as a gift, a fossil or an in-game trade
  - **dashed badge:** obtainable **by evolving** a Pokémon found in that game (e.g. Camerupt in Ruby via Numel, Level 33)
  - **empty badge:** not obtainable in that game
  - Hover or tap a badge for the exact routes, methods and levels.
- 🔁 **Evolutions:** what it evolves from and into, and how (level, stone, trade, friendship…).
- 📊 **Base stats** as coloured bars, with the total.
- 💡 **Abilities** with in-game descriptions, including hidden abilities.

### 🎮 Game pages
Open them from **☰ → Games**, or from **"Open … map →"** under any game badge in the Pokédex panel.
- 🕹️ **Game picker:** every game as a tile in its own colour, grouped by generation, with how many Pokémon are catchable there and how many of those you're still missing.
- 🗺️ **Every region and place** of all **38 games** (including DLC areas like the Isle of Armor, Crown Tundra, Kitakami and Blueberry Academy). For each place, the Pokémon you can catch there, grouped by method (walking, surfing, fishing, gifts, raids, SOS…) with levels, rarity and 🌅/☀️/🌙 times.
- 🔢 Each place shows how many Pokémon you're still missing there, and **Find a place** searches the list.
- ⭐ Coming from a badge, that Pokémon is highlighted and the places without it are dimmed. For a game where it's only obtainable by evolving, the Pokémon you evolve it from is highlighted.
- ✅ Tap a Pokémon to mark it caught or missing. **Only missing** hides everything you already have (and is remembered). In ✨ shiny mode, it all works on your shiny dex.
- 🔗 Every page has its own address (`#game/ultra-sun/alola-route-1`), so the back button and bookmarks work.
- 📱 On phones the places list folds into a **Places ▾** button.

### ⚙️ Menu (☰)
- 🎞️ Animation toggles (shiny switch effect, colour fill on click). Both are on by default.
- 💾 **Export / import backup (.json)** to move your progress between devices or browsers.
- Mark all shown Pokémon as caught or missing, or clear the dex.

### 📱 Everywhere
- Mobile-friendly layout with large touch targets.
- Smooth on big lists: images load lazily and off-screen cards aren't rendered.
- Data loads only when needed: location details (≈600 KB) the first time you look at a game badge, and each game's places (≈30–200 KB) when you open that game.

### ⚡ Fast artwork
- 💾 **Image cache:** artwork is kept on your device after its first download, so the dex (and the shiny dex) shows up instantly on later visits, with no requests to the image sites. It works on the website, not when opening the page as a local file.
- 🚀 **Shiny art loads in parallel** and only slows down if imgbb actually reports it's busy.
- 🔄 **No blank cards:** if a shiny image takes too long, the card shows the backup art and switches to the proper one as soon as it arrives.

---

## 🛠️ For developers

No framework and no build step for the page itself: plain HTML, CSS and JavaScript files.

```
index.html          the page markup (header, menus, bars) and the list of files below, in load order
css/                styles, loaded in cascade order (later files override earlier ones)
  base.css            colours, page basics, header
  selection.css       selection mode
  dex.css             dex sections, cards, paint fill, shiny-art note
  shiny.css           the ✨ switch effect
  mobile.css          phones and narrow windows
  ot.css              OT marks (Ash's cap)
  pokedex.css         the Pokédex tile
  games.css           game pages
js/                 the app, as ordinary scripts sharing one scope, run in this order
  core.js             constants, helpers, the checklist entries
  state.js            saved progress (localStorage), current dex and filters
  dex.js              builds the dex, loads artwork (imgbb speed control, fallbacks)
  filters.js          category chips, counts, search/filters, marking a card
  shiny.js            regular / shiny switch and its transition
  pokedex.js          the Pokédex tile
  events.js           card clicks, keyboard, search box
  selection.js        selection mode
  menu.js             settings, backup export/import, bulk marking, tucking header
  games.js            game pages
  main.js             start-up (runs last)
data/               generated by the tools below; don't edit by hand
  pokemon.js          the checklist entries and their artwork file names
  info-data.js        Pokédex panel data (loads with the page)
  info-places.js      exact places per game (loads on first badge hover)
  locations/<game>.js places → Pokémon for each game page (loads when that game is opened)
icons/              game icons for the GBA games, the tab icon, the OT cap
sw.js               image cache (service worker)
tools/              data scripts (Python), not published
```

| Tool | What it does |
|---|---|
| `tools/build.py` | Builds `data/pokemon.js` (the checklist entries) |
| `tools/fetch_info.py` | Builds `data/info-data.js` and `data/info-places.js` (types, stats, abilities, evolutions, locations) |
| `tools/fetch_locations.py` | Builds `data/locations/<game>.js` from pokemondb's location pages + the dex finds |
| `tools/check_pokemondb.py` | Accuracy check: compares the location data with pokemondb.net |
| `tools/check_locations.py` | Coverage check: every Pokémon the dex says is catchable in a game appears in one of its places |
| `tools/test_imgbb.py` | Measures how imgbb (shiny art) copes with 4–100 requests at once |
| `tools/copy_local.py` | Copies the site to the local test folder (`D:\Pokemon\Living Dex - Web Checker`) |
| `wrangler.jsonc`, `.assetsignore` | Cloudflare Workers config: the site is published as static files, without `tools/` or this README |

```bash
python tools/build.py            # rebuild the checklist entries (only when the Pokémon list changes)
python tools/fetch_info.py       # refresh the Pokédex data (downloaded pages are cached in tools/cache/)
python tools/fetch_locations.py  # refresh the game pages' place data (run after fetch_info.py)
python tools/copy_local.py       # update the local test copy
```

To test locally over http (with the image cache), serve the folder: `python -m http.server` and open http://localhost:8000.

### ✅ Tests
Two suites, no installs needed (they're not published, see `.assetsignore`):

- **Data and files** (`tests/test_data.py`, about 0.1 s):
  - the Pokémon list and the Pokédex data match
  - every game's routes list exactly the Pokémon it can catch
  - known cases stay right (Camerupt in Ruby by evolving, no event-only finds)
  - every file the page loads exists, and none is excluded from publishing

  ```bash
  python -m unittest discover -s tests -v
  ```
- **The app in a browser** (`tests/index.html`, about 25 s): with `python -m http.server` running, open http://localhost:8000/tests/. It loads the real page in a frame and clicks through:
  - marking, search and filters
  - the Pokédex tile, selection mode, OT marks
  - the ✨ switch, including its first-time animation, and the shiny note
  - the game picker and game pages: highlights, marking, the shiny redraw, title and back button
  - the phone header

  Your own marks and settings are saved before the run and restored afterwards.

**Publishing:** the site runs on Cloudflare Workers (static assets, no server code). Cloudflare deploys it automatically on every push to `main`.

---

## 🙏 Credits

### 🖼️ Images
- **Official artwork** by Ken Sugimori and The Pokémon Company, loaded from [**Bulbapedia**](https://bulbapedia.bulbagarden.net) / [Bulbagarden Archives](https://archives.bulbagarden.net).
- **Fallback artwork** from [**Serebii.net**](https://www.serebii.net).
- **Shiny artwork** in the official art style from [**sneasvile's imgbb gallery**](https://tonofdirt726.imgbb.com/albums). Thank you for making these! 💙
- **Shiny fallback:** Pokémon HOME renders hosted on Bulbapedia.
- **Game icons** (DS, 3DS, Switch and 3DS Virtual Console home-menu icons) from the [Bulbagarden Archives' game icons](https://archives.bulbagarden.net/wiki/Category:Game_icons).
- **GBA game icons** (Ruby, Sapphire, Emerald, FireRed, LeafGreen; those games never had official ones): custom HD icons by **Viator_** on [SteamGridDB](https://www.steamgriddb.com/icon/40864), based on EuroBeat's. These five are the only images stored in this repository (`icons/`).

All other images are linked from those sites at view time; your browser keeps its own copy for speed.

### 📚 Data
- [**PokéAPI**](https://pokeapi.co): types, base stats, abilities, evolutions, and encounter data for Red/Blue through Sword/Shield.
- [**Serebii.net**](https://www.serebii.net): locations for Omega Ruby/Alpha Sapphire, Brilliant Diamond/Shining Pearl, Legends: Arceus, Scarlet/Violet + DLC and Legends: Z-A. Also the colour palette 🎨.
- [**Pokémon Database (pokemondb.net)**](https://pokemondb.net): extra locations (White Forest, swarms, fossils, in-game trades), the accuracy check, and the place-by-place encounter tables behind the game pages.

### 💙 Thank you
Thank you to:
- [**Bulbapedia**](https://bulbapedia.bulbagarden.net) and the [**Bulbagarden Archives**](https://archives.bulbagarden.net): for the artwork of every Pokémon and form, and decades of carefully kept Pokémon knowledge.
- [**Serebii.net**](https://www.serebii.net): for the most complete location data of the newest games, the backup artwork, and the look this page borrows.
- [**Pokémon Database (pokemondb.net)**](https://pokemondb.net): for the place-by-place encounter tables behind the game pages and a second opinion on every location.
- [**PokéAPI**](https://pokeapi.co): for the open data on types, stats, abilities, evolutions and encounters.
- [**imgbb**](https://imgbb.com): for hosting the shiny artwork.
- **sneasvile**, the artist behind the [shiny artwork gallery](https://tonofdirt726.imgbb.com/albums): for drawing every shiny in the official art style. The shiny dex wouldn't look like this without you. ✨
- **Viator_** and **EuroBeat** on [SteamGridDB](https://www.steamgriddb.com): for the GBA game icons.

### ⚖️ Disclaimer
Pokémon and all related names and images are © Nintendo, Creatures Inc. and GAME FREAK Inc. This is a free, unofficial fan project, not affiliated with or endorsed by them.
