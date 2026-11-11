# Imperial Rasen overhaul

Goal: turn Aura Clash into a full CK3 overhaul set in **Imperial Rasen**, the world of the Aura Clash interactive fiction, using the painted world map in `assets/map/imperial_rasen_source.jpg`.

The overhaul is built as a separate mod folder, `RasenMap/`, loaded after `AuraClash/`. The base mod keeps working on the vanilla map until the overhaul can load on its own.

## Setting summary (from the Aura Clash game text)

- **Imperial Rasen** is a 3,000-mile-wide spiral continent. Its rulers raised the seabed into a spiral long ago as a defence after the **Calamity** shattered the **Cathayan Empire** to the west into hundreds of islands.
- **Azuma Honsha**, the capital island, sits at the centre, where the leylines meet and natural aura is strongest. Its city spreads along the entire coast.
- **Government:** the imperial family vanished centuries ago. The **Exalted Council** rules from Azuma Honsha; each of the five Inner Kingdoms holds a seat through an Exalt (for example, Bladed Exalt Ryuuzan Masaru and the Wild Exalt). The Council's police force are the **Archons**, recruited through the **Heavenly Ascension Trials**. The Archonate keeps master trainers from all five Inner Kingdoms.
- **The five Inner Kingdoms**, each with a colour, a Martial Style and a value judged in the Trials:

| Kingdom | Colour | Style (role) | Values |
|---|---|---|---|
| Bladed Lands | Red / scarlet | Akakiru (samurai swordsmen) | Honour |
| Sacred Lands | Blue | Aoyusumu (exorcist-monks, Devanic Temple) | Compassion |
| Wild Lands | Green | Midorikatai (apex warriors; warrior-kings, slave arenas, beast clans) | Ruthless strength |
| Mystic Lands | Gold | Kiihakai (sorcerers; rigid hierarchy, cities of wonders) | Intelligence |
| Cursed Lands | Purple | Kurokonton (shinobi; Ozaki and other shinobi clans) | Practical results |

- **The Outer Lands** (Outer North, East, South and West) ring the Inner Sea. Natural aura there is weak: each region has a "Mortal Limit" (Outer West: 800 AP). Outer North fights generational **Ice Incursions** of demonic ice and yin spirits; a rebel **Divine General** holds its northern border. Outer East has the richest trade sects. Settlements and colonies change hands constantly.
- **Society:** castes (Noble, Warrior, Laborer, and the Clanless) and Magistrates who govern towns. Sects include martial sects (Thunderfall, Sunbringer, Dreamriver, Windrising, Waverunner), trade sects (Choral Line, Thousand Lantern) and others (Lost Siren, Hidden Coil, Mountain Hazard).
- **Peoples:** Humans of **Zenshin** culture, descended from Cathayans, whose katana distinguishes them; Cathayan heritage survives in hanfu and qiang. Also **Oni** ("spirits who want a human form"), **Yokai** ("animals who want a human form", such as wolf and monkey yokai) and **Kitsune** (rare, part beast, spirit and human, often hunted as tricksters).
- **Faith and spirit:** the **Devanic Temple** (monks, shrinemaidens, Saints; hunts Fiends; allied with the Sacred Lands). **Shugendō**, the elemental art, comes from mountain pilgrimages. Wild Gods such as Gazhurra make pacts with sects.
- **Places:** Nanhou (an Outer West town that hosts the Trials), Thunderfall Village, Sunbringer Village, Dead Mountain, Rabbit Trial Valley, Burning Forest, Harehama, the Heavenly Storm Gate, and the Inner Sea.

## Mapping to CK3

| Aura Clash | CK3 |
|---|---|
| Imperial Rasen | Empire `e_rasen` (de jure only at start; the Exalted Council holds power) |
| Five Inner Kingdoms, Azuma Honsha, four Outer provinces | 10 de jure kingdoms `k_<region>`; geographical regions `world_rasen_*` |
| Exalted Council | Council of Exalts: a custom government or struggle-like mechanic over Azuma Honsha (phase 4) |
| Archons and the Heavenly Ascension Trials | Already in the base mod (Archonate Disciple, the Trials event chain) |
| Castes and Clans | Estates and houses; "Clanless" lowborn; promotion into the Warrior Caste via events |
| Sects | The base mod's provincial sects, reseeded with canonical sects |
| Mortal Limit by region | Implemented: Aura Pressure gains halve above the Mortal Limit; `RasenMap` adds +700 in the Inner Kingdoms and +1,700 on Azuma Honsha (`ac_mortal_limit_region_values.txt`) |
| Zenshin, Cathayan, Oni, Yokai, Kitsune | Five cultures, each with its own heritage; Zenshin and Old Cathayan languages |
| Devanic Temple, Shugendō, Wild Gods | Religions and faiths |

## Roadmap

1. **Map geometry (done, generated).** `tools/build_rasen_map.py` classifies the painting and generates:
   - `provinces.png`, `definition.csv` and `default.map`: 1,157 land provinces, 149 sea zones and 16 impassable ocean zones.
   - A greyscale `heightmap.png`.
   - The landed title hierarchy: one empire, 10 kingdoms, 92 duchies and 313 counties.
   - Geographical regions and localization.

   Edit `tools/rasen_regions.json` (region geometry, densities, colours, canonical names) or `tools/rasen_names.py`, then rerun the script. `python tools/build_rasen_map.py --check` verifies the committed output, and `output/rasen-preview.png` shows the regions.
2. **Map assets.** Generated so far:
   - **Terrain** for every province (`common/province_terrain`), taken from the painting's relief and each region's character:
     - snowy mountains and taiga in Outer North;
     - mountains and forest in the Sacred Lands;
     - jungle and forest in the Wild Lands;
     - wetlands in the Cursed Lands;
     - drylands and hills in the Bladed Lands;
     - farmland on Azuma Honsha.
   - **Winter severity** for the north (Outer North, Sacred mountains).
   - A blank, valid **`rivers.png`** (index 255 land, 254 water).

   Still needs the CK3 install:
   - **Bake the heightmap.** CK3 reads a packed `heightmap.heightmap`, `packed_heightmap.png` and `indirection_heightmap.png`. Generate them from `heightmap.png` with the game's map tooling.
   - **Painted rivers**, terrain detail masks under `gfx/map/terrain/`, flatmap and water.
   - **Map object locators** (cities, units, combat) from the in-game map editor.
   - `map_data` is no longer replaced wholesale, so vanilla `seasons.txt` and `continent.txt` remain available to `default.map`.
3. **Peoples and faiths (done, generated).** `tools/build_rasen_world.py`, with its data in `tools/rasen_world_data.py`:
   - **Cultures:** Zenshin, Cathayan, Oni, Yokai and Kitsune, each with its own heritage and Zenshin-style or Cathayan name lists.
   - **Rasenese Rites:** Ancestral Rites (the Outer lands, Azuma Honsha and the Bladed Lands), the Celestial Order (Mystic) and the Veiled Ancestors (Cursed).
   - **Devanic Faith:** the Devanic Temple (Sacred) and Shugendō (Outer North).
   - **Wild Gods:** the Pacts of the Wild Gods (Wild).
   - **Holy sites:** 12, including the Devanic Temple, Dead Mountain, Rabbit Trial Valley, the Burning Forest, the Leyline Nexus and the Heavenly Storm Gate.
4. **History and bookmark (first pass, generated).**
   - Start date 3000.3.1, "The Heavenly Ascension Trials".
   - 92 rulers in 29 dynasties.
   - The five Exalts hold the Inner Kingdoms as grandmaster cultivators with Immortal Cores: Bladed Exalt Ryuuzan Masaru (canon); the Wild, Cursed (Ozaki), Mystic and Sacred Exalts (generated names).
   - A High Steward of the Exalted Council holds Azuma Honsha. The Outer lands are independent duchies; Magistrates Khan (Thunderfall) and Fuyu (Nanhou) are canon.
   - Province culture, faith and holdings.
   - Every ruler has a spouse and one to three children (matrilineal for female rulers), 360 characters in all. Each culture starts in the Early Medieval era with first-tier innovations.
   - Still to do: the canonical sects as seeded sects, and bookmark portraits.
5. **Regional systems:** (regional Mortal Limit done) Ice Incursions in Outer North, Inner Kingdom favour (honour, compassion, ruthlessness, intelligence, practicality) affecting Trial scoring, and caste promotion events.
6. **Cleanup:** replace or guard vanilla content that assumes Earth's map (vanilla event overrides that reference real places, struggles, travel events).

## Loading

`RasenMap/` is not yet a loadable mod: it still needs the step 2 map assets. Until then, keep using `AuraClash/` alone. Its `descriptor.mod` loads after `AuraClash`, overrides the `map_data` files it generates, and replaces `common/landed_titles`, the bookmarks, `common/dynasties` and `history/{characters,provinces,titles}`. Vanilla cultures and religions stay loaded but unused.

### Verify in-game first
The generated scripts use vanilla keys that cannot be checked without the game files:
- Graphics sets (`mongol_*_gfx`, `steppe_*_gfx`) and the `asian` ethnicity.
- Traditions, tenets and doctrines.
- `graphical_faith` and `piety_icon_group`, and the `custom_faith_N` icons.
- `NGame.START_DATE` and `NGame.END_DATE`.
- Innovation keys and `culture_era_early_medieval` in `history/cultures`.
- Terrain keys and `winter_severity_bias`.

Check `error.log` for unknown keys on the first launch, and correct them in `tools/rasen_world_data.py`.
