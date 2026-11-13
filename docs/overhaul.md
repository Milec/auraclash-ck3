# Imperial Rasen overhaul

Goal: turn Aura Clash into a full CK3 overhaul set in **Imperial Rasen**, the world of the Aura Clash interactive fiction, using the painted world map in `assets/map/imperial_rasen_source.jpg`.

The overhaul and the cultivation mechanics are one mod, in `AuraClash/`: a total conversion that replaces the vanilla map, titles and history. (They were two folders, `AuraClash/` and `RasenMap/`, until the map loaded and played.)

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
| Sects | The story's 23 sects at their own seats, with standing by region (see [sects](sects.md)) |
| Mortal Limit by region | Implemented: Aura Pressure gains halve above the Mortal Limit and again for every further half of it (to 1/32 above 3×); the land a character is in adds +200 in Outer North, +1,200 in the Inner Kingdoms and +5,200 on Azuma Honsha, giving 800 / 1,000 / 2,000 / 6,000 at the lowest Potential (`ac_mortal_limit_region_values.txt`) |
| Zenshin, Cathayan, Lunargoth, Oni, Yokai, Kitsune | Six cultures, each with its own heritage; Zenshin, Old Cathayan and Lunargothic languages |
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
   - **Painted rivers** and water.

   **Ground textures** (`python tools/build_rasen_terrain.py`, generated from the province map and terrain): `gfx/map/terrain/detail_index.tga` and `detail_intensity.tga` give every province the vanilla material of its terrain (snow on the highest mountain ground, soft blends at borders), `colormap.dds` tints it, and `flat_maps/flatmap.dds` is the source painting for the zoomed-out paper map. The game loads them without errors; how they look in-game has not been checked by a person (the index maps are run-length-encoded TGA, which vanilla's are not).
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
   - The canonical sects are seeded at their seats, and the six featured rulers have portraits.
5. **Regional systems:**
   - **Regional Mortal Limit:** done.
   - **Ice Incursions:** done (`AuraClash/events/rasen_ice_incursion_events.txt`).
     - Every 20–30 years, demonic ice and yin hordes invade Outer North for 3–6 years.
     - Outer North counties suffer reduced development growth, opinion and levies.
     - Outer North rulers may march to the front, fund the Northern Army or hold their own walls.
     - The Council summons Archonate Disciples.
     - Holding the line yields a 1,500 AP ice demon Soul Treasure, Aura Pressure, Core progress, Honor and the Veteran of the Ice War modifier.
     - The **Divine General**, a generated Lunargoth grandmaster, leads Outer North. Per the Core Rulebook, **Lunargoths** live in Outer East and the Mystic Lands, **Oni** in the Cursed Lands and Outer South, and **Yokai** in the Wild Lands and Outer North; Humans are everywhere.
   - Inner Kingdom Favor in the Trials: done (base mod).
   - **Castes:** done (Noble, Warrior, Merchant and Clanless Laborer, plus elevation to the Warrior Caste).
   - **Exalted Council:** done (`tools/build_rasen_council.py`).
     - Every three years the five Exalts (holders of the Inner Kingdoms) vote on an imperial decree.
     - AI Exalts back their own land's decree, lean towards Exalts they like (opinion 25+) and never back a rival.
     - Player Exalts vote, or spend 150 prestige to cast two votes for their own land's decree.
     - The decree is drawn in proportion to the votes, reflecting the IF's "shaky peace".
     - The winner gains 100 prestige. Exalts outvoted on their own decree resent the winner ("inter-council conflicts are not uncommon", ch. 9).
     - Decrees:
       - Dispatch the Archons: patrols in the Outer provinces, and a shorter Ice Incursion.
       - Purge the Fiends: disease resistance, and piety for Devanic rulers.
       - Open the Imperial Archives: half-price Path Manuals.
       - Levy the Outer Provinces: gold for the Exalts, taxes on the Outer provinces.
       - Call the Trials: the Heavenly Ascension Trials next year.
     - **Trial patronage** (ch. 9):
       - When the Trials open, an AI Exalt sponsors the year's favourite with gold and +2 Favor with that land.
       - A different Exalt then offers each player entrant counter-patronage, as the Bladed Exalt uses the protagonist against the Wild Exalt.
       - Accepting gives gold, Favor and the Exalt's goodwill.
     - Approximations:
       - The decrees and the vote weights are design, not IF text.
       - The Council could later move onto Roads to Power's administrative government and influence.
   - **Chapter 9 of the IF** (the Patreon build): done (`tools/build_rasen_shadows.py`, `CANON_CAST` in `tools/rasen_world_data.py`).
     - **Ryuuzan Keiko:** the Bladed Exalt's only daughter, a Noble undercover as a head nurse. She is a courtier at her father's court (physician, intrigue).
     - **The Akuma Lords:**
       - The cast: Jahi, Black Flower and a third Lord (generated name), plus Taio, all seeded as cult members.
       - Membership is a secret (`rasen_secret_akuma`), criminal to all outsiders. Members gain Blood Chi (+3 prowess, -0.5 health).
       - Each year every Lord may recruit an ambitious, callous or stressed AI cultivator, and a Clone of Taio may tempt players.
       - With 12 or more living members the cult strikes an Outer county (Akuma Terror). Exalts may then pay 100 gold to dispatch Archons, which exposes one member.
     - **Ryugujo:**
       - A Ryugujin culture (off the painted map) and Dragon Prince Tenkairyu, who has Dragon Blood and is secretly in league with the Akuma Lords.
       - Archonate disciples and Exalts may uncover a Ryugujo spy, then expose them (which reveals the Dragon Prince's secret), turn them or release them.
     - Approximations:
       - The cult's faith, the Lords' ages and traits, and Ryugujin traditions and faith are design choices.
       - Masaru's twenty-three sons are not all generated.
6. **Cleanup:** replace or guard vanilla content that assumes Earth's map (vanilla event overrides that reference real places, struggles, travel events).

## Loading

`AuraClash/` loads and plays in CK3 1.20.1.2.

### Government
All of Rasen is one hegemony, **Imperial Rasen** (`h_rasen`), held for the Exalted Council by the High Steward at Azuma Honsha: the IF has had no Emperor for centuries. It uses All Under Heaven's merit bureaucracy (`meritocratic_government`: appointed governors, merit ranks and a treasury; China's own `celestial_government` is tied to the dynastic cycle and `h_china`).
- The five **Exalts** rule their Inner Kingdoms as hereditary (feudal) kings under the hegemony.
- The Outer Lands have no kings. The Council appoints a **Magistrate** to each duchy and to each county in it, as in the IF, where Magistrates govern towns. Canonical Magistrates (Khan of Thunderfall, Fuyu of Nanhou) keep their seats.
- The **Wild Lands** are not unified: thirteen **Maos** each run a faction. The strongest holds the Wild seat on the Council as Wild Exalt with only his own duchy; nine hold the other duchies and three have carved counties out of the largest ones. All answer only to the hegemony.
- The **Divine General** of the north answers to no one and stays independent.
- Rulers are titled Exalt, High Steward and Magistrate (`common/flavorization/rasen_title_holders.txt`).

### Verified in-game (CK3 1.20.1.2, all DLC)
`python tools/prepare_rasen_checks.py` prepares a separate user directory that starts the 3000.3.1 bookmark directly as the Bladed Exalt (`-skip -bookmark=bm_rasen_trials -play=k_bladed`). On game start it runs 52 checks, all passing:
- Each Inner Kingdom and Azuma Honsha has a ruler.
- The Bladed Exalt's cultivation, Immortal Core, race, faith and culture; Keiko; the Divine General; the seeded Akuma Lords; holdings.
- The 23 sects at their seats, with standing, treasury, roster and master strength by region; a duel between sects earning renown; renown raising a Frontier Sect one standing and no further; every sect-life event.
- An Exalted Council decree, an AI-versus-AI Clash of Auras, and an Ice Incursion.
- Three simulated years of the Council, Akuma Lords, Ice Incursion, Trials and sect yearly effects.

No crash, and no runtime errors from the mods' own scripts. The six featured rulers have bookmark portraits. Before the two folders were merged, the cultivation fixtures passed on the vanilla 1066 start: cultivation (59/59) and awakening and sects (62/62). Those fixtures (`prepare_potential_checks.py`, `prepare_sect_engine_checks.py` and the like) use England and other Earth realms, so they need porting to Rasen titles before they can run again.

Not yet verified by a person: the player-facing UI (duel rounds, Council voting, bookmark screen, sect register and sect-life events) and long play. The game starts paused and nothing found unpauses it unattended: the `-handsoff` flags and an interface widget calling the pause button's action were both tried. Once someone unpauses a QA run, each in-game year logs `RASEN_QA YEAR` marks (tick, decree set, sects led, renown earned, sect ties, Exalt alive).

`error.log` is about 7,300 lines after loading (down from 18,700): vanilla scripts naming Earth's counties, baronies, characters and houses.

### Total-conversion lessons (CK3 1.20)
- Do **not** `replace_path` `history/province_mapping`: without it the game crashes (null read) as soon as any province has a holding.
- `adjacencies.csv` needs its `-1;-1;...` end line, or loading spins forever.
- `replace_path` is not recursive (`history/titles/ce3` needs its own entry).
- Keep every vanilla realm title (landless stubs) and geographical region (stubs), and patch vanilla files that name provinces beyond the map (`tools/build_rasen_vanilla_patches.py`). The Atlantis template (github.com/bombusfrigidus/Atlantis) does the same.
- `root` inside a scripted effect is the calling event's root, not the scope that called the effect.

### Vanilla keys (verified against CK3 1.20.1)
`python tools/verify_vanilla_keys.py` checks every vanilla key the mod names against the installed game; `tools/test_vanilla_keys.py` runs it whenever `CK3_GAME_ROOT` is set. All 172 references resolve:
- The graphics sets (`mongol_*_gfx`, `steppe_*_gfx`) and the `asian` ethnicity exist. They are still placeholders for All Under Heaven's East Asian sets.
- Traditions, ethos, martial customs, tenets and doctrines exist.
- So do `graphical_faith`, `piety_icon_group`, the `custom_faith_N` icons, innovations, `culture_era_early_medieval`, terrain types, event themes and modifier icons.

Two 1.20 changes needed fixes:
- **The religion rework.** Religions moved to `common/religion/religion_types`, faiths to `faith_types` (each naming its `religion`, with `tenets = { }` and `eminent_holy_sites = { }`), and holy sites to `holy_site_types` (`faith_character_modifier`).
  - History now assigns faiths through Rites (`rite = <key>`). A faith with no scripted Rite gets a main Rite with the faith's own key, so `rite = ancestral_rites` works.
  - Bookmarks still use `religion =`.
- **`tenet_monasticism` is gone.** Monasticism is now a doctrine group. The Devanic Temple takes `doctrine_monasticism_encouraged` and `tenet_inner_journey` instead.

The year-3000 start date, `winter_severity_bias` and `add_matrilineal_spouse` all load without errors in 1.20.1.
