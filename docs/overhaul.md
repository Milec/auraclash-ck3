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
| Mortal Limit by region | Regional cap on Core training: outer regions slow advancement above a limit; inner regions and Azuma Honsha raise it |
| Zenshin, Cathayan, Oni, Yokai, Kitsune | Cultures and heritages (Oni, Yokai and Kitsune as heritages with traits) |
| Devanic Temple, Shugendō, Wild Gods | Religions and faiths |

## Roadmap

1. **Map geometry (done, generated).** `tools/build_rasen_map.py` classifies the painting and generates:
   - `provinces.png`, `definition.csv` and `default.map`: 1,157 land provinces, 149 sea zones and 16 impassable ocean zones.
   - A greyscale `heightmap.png`.
   - The landed title hierarchy: one empire, 10 kingdoms, 92 duchies and 313 counties.
   - Geographical regions and localization.

   Edit `tools/rasen_regions.json` (region geometry, densities, colours, canonical names) or `tools/rasen_names.py`, then rerun the script. `python tools/build_rasen_map.py --check` verifies the committed output, and `output/rasen-preview.png` shows the regions.
2. **Map assets that need the CK3 install** (to do on a machine with CK3):
   - Bake the heightmap. CK3 reads a packed `heightmap.heightmap`, `packed_heightmap.png` and `indirection_heightmap.png`, not the plain PNG. Generate them from `heightmap.png` with the game's map tooling, then verify that the game loads the result.
   - `rivers.png` in CK3's indexed palette (a builder option will copy the palette from the vanilla file), plus terrain masks under `gfx/map/terrain/`, `province_terrain`, flatmap, water and climate.
   - Map object locators (cities, units, combat) from the in-game map editor.
3. **Peoples and faiths:** Zenshin and Cathayan cultures; Oni, Yokai and Kitsune heritages; the Devanic faith, Shugendō and Wild God cults; holy sites at the Devanic Temple and the Heavenly Storm Gate.
4. **History and bookmark:** title holders, Magistrates, the five Exalts, Inner Kingdom houses (Ryuuzan, Ozaki, Nakamoto), the canonical sects, and a start date shortly before the Trials at Nanhou.
5. **Regional systems:** a regional Mortal Limit, Ice Incursions in Outer North, Inner Kingdom favour (honour, compassion, ruthlessness, intelligence, practicality) affecting Trial scoring, and caste promotion events.
6. **Cleanup:** replace or guard vanilla content that assumes Earth's map (vanilla event overrides that reference real places, struggles, travel events).

## Loading

`RasenMap/` is not yet a loadable mod. CK3 needs the baked heightmap, rivers, terrain, history and a bookmark first. Until step 4 is complete, keep using `AuraClash/` alone. The intended load order is `AuraClash`, then `RasenMap`, with `RasenMap` replacing `map_data`, `common/landed_titles`, `history/provinces`, `history/titles`, `history/characters` and `common/bookmarks`.
