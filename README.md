# Aura Clash — Crusader Kings III Mod

Bring the cultivation system of **Aura Clash**, an eastern-fantasy (xianxia/wuxia) setting, into Crusader Kings III. Awaken as a Cultivator, train your four Combat Cores, temper your Foundation in battle, master a Martial Arts Style and two Elements, and condense an Immortal Core.

**Version:** 0.5.0 · **Event integrations target:** CK3 1.20.1 · **Status:** early and playable; many perks are still placeholders

---

## Installation

### Manual
1. Download or clone this repository.
2. Copy **both** `AuraClash.mod` and the `AuraClash/` folder into your CK3 mod directory:
   - Windows: `Documents\Paradox Interactive\Crusader Kings III\mod\`
   - Linux: `~/.local/share/Paradox Interactive/Crusader Kings III/mod/`
   - macOS: `~/Documents/Paradox Interactive/Crusader Kings III/mod/`
3. Enable **Aura Clash** in your launcher playset. It is a total conversion: it replaces the map with Imperial Rasen, so do not combine it with other map mods.
4. Start from the **Imperial Rasen** bookmark (year 3000).

The final layout should be:
```
mod/
├── AuraClash.mod
└── AuraClash/
    ├── descriptor.mod
    ├── common/ events/ gui/ gfx/ localization/
```

### Compatibility
- **Start a new game** when updating from an earlier version. v0.3 replaces the Foundation trait, and v0.2 renamed the tree and perk keys.
- `AuraClash/gui/window_character_lifestyle.gui` **replaces** the vanilla lifestyle window. It will conflict with other mods that edit that window, including Princes of Darkness and most UI overhauls.
- One vanilla option-display define is changed: unavailable options can remain visible until **6** options are shown (vanilla is 4). This does not cap the number of available choices.
- Cultivation integration overrides **143 individual vanilla events** using `id_override_priority = 10`, targeting CK3 **1.20.1 / 1.20.1.1**: **269 added choices in 141 events**, plus two linked tournament outcome events. Mods changing those same events need a compatibility patch. Original event files are not replaced; normal choices and cleanup are preserved, with guarded resolution for successful cultivation interventions. The generator includes required file-local helpers and constants alongside relocated events. Fully restart CK3 after updating: event priority overrides do not support hot reload.
- Native sect domiciles add a landless Sect Master title and register its government in `NGovernment.GOVERNMENT_TYPES`, retaining all 20 native entries. Mods replacing that list need a merged compatibility definition.
- Six construction-notification localization keys use generic wording for Sect Masters because native messages assume a personal domicile. Other characters keep vanilla wording; mods replacing those same keys need a localization merge.
- Potential adds conditional descriptions to `TRAIT_LEVEL_TRACK_TT`; other traits retain their native pip text. Mods replacing that localization key need a merge.
- Its on_actions (including a hook on hunts) are appended to vanilla's.

---

## Features

### Trait artwork
All 28 cultivation, Foundation, Style and Element traits have replacement painted icons. Akakiru uses a katana with a straight hilt. [Preview and approved PNG masters](assets/trait-icons/README.md) are included; runtime textures retain their original filenames and 120 × 120 DDS format. Potential adds three tier variants and two track icons. With Pillow installed, `python tools/build_trait_icons.py --check` verifies all 31 trait textures and both Potential track icons against their sources.

### Cultivation choices in vanilla events
Cultivators aged 16+ can use relevant affinities, styles, trained Cores and perks in existing events:
- **Travel:** White Squall, Person Overboard, The Flood, Not a Drop, A Fire in the Night, Snowbound, Avalanche, Familiar Trees, On a Mountain Trail, Bandits on the Bridge, Flawed Fare and Rainstorm.
- **Bridge bandits:** Midorikatai overpowers the leader; Akakiru disarms the bandits; Storm frightens them away; Darkness conceals the crossing.
- **Healing:** three wound-treatment events offer the existing one-tier Chi Healing effect. This shares a six-month cooldown with the character interaction and does not cure infection or gangrene. The healer must be physically present with the patient.
- **Hunts:** a trained Midorikatai or Akakiru cultivator can stop a charging animal; sword techniques, protective wards or Blinding Flash can interrupt an attack on another hunter.
- **Court:** cultivation can support three-year agricultural relief and patrol projects in the petitioning county. These cost money and do not instantly remove famine, epidemics or all unrest.
- **Fatal outcomes:** Dangers of the Deep checks for Water, Wind or Storm cultivation before executing its death effects. A poisoned visitor can intervene using Toxicology, Grandmaster Alchemist, Flame Purge, Purifying Light, an Immortal Core or at least ten Fortitude Core dots. The normal fatal outcome remains available if the rescue is declined; characters without a qualifying ability follow vanilla behavior.
- **More travel:** retrieve a sliding artifact chest; treat frostbite or a snakebite; subdue or frighten a beast; free muddy wagons; rescue plantation workers and a companion trapped in a forest fire. Frostbite treatment updates native severity and modifiers without restoring lost limbs.
- **Disaster relief:** funded food distribution, rubble rescue, medical assistance and nonlethal responses to looting complete existing governor contracts. A ruined farmhouse can be rebuilt with cultivation support. These checks use the actual destination and preserve the contract's rewards and cleanup.
- **Plagues and alchemy:** funded capital defenses, an alchemical medical book, emergency burials or cremation, containment of a diseased siege projectile, and treatment of the child in Healing Hands. These do not erase a county's epidemic. Cremation costs piety when it conflicts with the ruler's faith's funeral doctrine.
- **Tournaments and intrigue:** Wind-Guided Arrows changes archery score; Treasure Refining preserves a chipped weapon; Akakiru, Midorikatai, Kurokonton and Aoyusumu can interrupt a lethal tournament encounter. The delayed wound/death resolver honors these choices. Scrying and Shadow Step improve use of a secret tunnel; trained alchemists can send poisoned gifts without accidentally poisoning their own household.
- **Aoyusumu:** named techniques calm a coronation stampede, perform an Exorcist's Rite, reassure people facing plague or earthquake, and resolve Haunted by the Past through meditation. Precognition averts the hunt attack and the tournament assault, and guides a safe disaster retreat. Meditation has a three-year cooldown and six months of reduced diplomacy/stewardship duties; it does not add exertion stress.
- **Kiihakai:** Barrier of Chi protects the family members present during Selfless Acts; Ward shelters a disaster rallying point; Runic Empowerment repairs a wagon wheel or neglected artifact; Scrying Sphere inspects a secret tunnel. Named Mending Chi options appear in all three wound-treatment events and disaster medical relief, sharing the normal healing cooldown.
- **Prison:** captive cultivators can purify an infected wound or use Wallbreaker, Vanishing Arts or Stone Shaping after a failed escape. Captive-specific triggers permit these techniques while imprisoned. Successful escapes retain vanilla release, memory, opinion and notification effects.
- **Tournament combat:** Akakiru and Midorikatai gain techniques in melee, tournament duels and jousting; Midorikatai also gains grappling stances, pin reversals and a safe escape from the lethal headlock. Skill and Core training affect contest rolls, and cultivating opponents resist more effectively. Techniques change native contest progress rather than declaring a winner. Ordinary one-on-one duels and tour sparring are unchanged.
- **Recitals and races:** Aoyusumu can steady a performance, answer insults and anticipate the audience; Kiihakai can draw on academy training or shelter a recital with a barrier. Race preparation preserves all three jockey candidates. Techniques during the Final Lap require the actual jockey's cultivation, and charge that rider's exertion. Owners can provide coaching, reassurance, wards or treatment when physically present.
- **Board games:** Precognition supplies one strong supported move per day while preserving native counters, stakes and resolution. An opposing practitioner of Precognition reduces its advantage. Tournament board games also gain foresight choices.
- **More activities:** track game with Scrying Sphere or Earthsense, escape a hunting pit before the fall injury, coach a child's ordinary archery, settle tournament fans, aid pilgrims, repair the exact damage from a feast brawl, escape a murder feast, reach precarious prey during a tour, and comfort a fellow mourner. Murder-feast escapes retain the normal survivor bookkeeping and the original fates of other guests and companions.
- **Examinations, debates and festivals:** trained techniques assist native examination attempts and scholarly argument rolls, cleansing rites, strength contests and a guest's wish. Preparation advantages are temporary; native scores, political consequences and final promotion checks remain in control.
- **Adventurers and imperial defenses:** find water for a parched camp, protect a stormbound convoy, repel a night attack, free a contract prisoner without single combat, assist paid watermill construction, and prevent catastrophic friendly fire during an opposed Greek-fire attack. A chariot-crash rescue saves the actual drivers with nonfatal injuries and retains race standings.
- **Herds and commissions:** protect migrating herds at a river or difficult passage, treat surviving livestock after blight, and tend an injured messenger while retaining the message delay. Support an artisan's forge or composure, handle an exotic court animal, and answer riddles with a trained mind.
- **Households, towns and accidents:** comfort a distressed spouse, provide temporary refrigeration or fund icehouse repairs, treat an ordinarily ill wet nurse, rescue residents from a town fire, assist paid wall improvements, obstruct witch trials, save a threatened artifact, and ease religious nightmares. Five physical-harm events gain ways to prevent the new accident's incapacity; existing incapacity is not cured.

The complete sorted register is available as an [Excel workbook](outputs/aura-clash-events/AuraClash-event-tracker.xlsx), an [event table](docs/events.csv), and an [option table](docs/event-options.csv). The workbook has filterable Events and Options tabs. It records event IDs, content families, added choices, ability references, outcomes, exertion and source locations. [The registry JSON](docs/event-registry.json) retains exact eligibility and effect scripts; the ability index is a readable index, not a replacement for AND/OR, presence and cooldown checks. Dynamic title placeholders depend on the save. Content families identify source content rather than asserting that every associated event requires owning a DLC.

Travel techniques can be performed by the ruler or a qualified cultivator in the actual entourage. Techniques draw on the practitioner's **Chi Pool** first. With chi available, the practitioner spends 1 chi and gains 25 Cultivation XP and 5 stress; with an empty pool, they suffer 15 stress and three months of Spent Chi (-2 prowess, +10% stress gain). An avalanche rescue or fatal-outcome intervention grants 100 XP and costs 2 chi and 20 stress, or with less chi, 40 stress and six months of Overextended Chi (-4 prowess, -0.25 health, +20% stress gain). Poison survivors also recover for six months with a further -0.25 health.

### Cultivation sects

One provincial sect is seeded per eligible de-jure kingdom (on Imperial Rasen, the story's 23 sects at their own seats), with a Master, up to ten Upper Disciples and twenty Lower Disciples. Each is called by its own name, such as the Thunderfall Sect or the Choral Line Trade Sect, and has a standing from Frontier to Imperial set by its region, which decides how strong, rich and selective it is; renown earned in battles, missions, trials and duels can raise it. Rulers can join while keeping their titles. Each sect has two elements, a martial style and a foundation, plus a persistent estate that passes to the next master.

Use **Decisions → Cultivation → Consult the Sect Register** for membership, six estate building lines, mission contracts and the contribution exchange. Public **Sect Trial** activities admit mortals and cultivators and examine disciples for promotion. Sects can form alliances and rivalries, fight group battles and host **Joint Sect Training**. See the [sect guide](docs/sects.md) for costs, succession, geography and testing.

The estate is a native CK3 domicile attached to a separate landless Sect Master title, with an original Chinese-inspired landscape and six building chains. It passes with sect leadership while rulers keep their lands, government and personal estate. The sect register opens illustrated building plots and sect-aware controls for the native construction queue; the vanilla editor assumes a ruler's personal domicile. Sect battles resolve as group clashes; they do not use ordinary single combat or conquer territory.

### Castes
Imperial Rasen's castes, from the IF, follow a character's Clan (a dynasty). "Caste documents require a Clan entry for Merchant Caste and above"; the lowborn are Clanless.
- **Noble Caste:** a landed ruler of a Clan, or their parent or spouse.
- **Warrior Caste:** a Clan member who is a cultivator or a strong fighter (prowess 12+). Any landed ruler can **Elevate to the Warrior Caste** a Clanless cultivator courtier or vassal and their children (100 prestige), as Magistrate Khan does in the IF.
- **Merchant Caste:** other Clan members.
- **Laborer Caste:** the Clanless.

The Warrior and Noble Castes "claim the land's natural aura" (+10% Aura Pressure gains), and only they may enter the Heavenly Ascension Trials. The caste is shown in the Mortal Core Training menu.

### Races
The IF's races, each with its racial bonus. A character has exactly one race, inherited from a parent at birth. Races only appear where characters are given one, as in the Imperial Rasen overhaul, which assigns them by culture.
- **Human:** Lore (+1 Learning). "The Human body is designed perfectly for cycling chi", so Aura Pressure gains +10%.
- **Oni:** Deception (+1 Intrigue). They control banks and trade in the cities (+5% domain tax) but are distrusted in rural lands (−5 county opinion). Ice and Fire chi come naturally (+5% AP).
- **Lunargoth:** Craft (+1 Stewardship); said to have come down from the Moon.
- **Yokai:** five lineages from the IF: Cat, Wolf, Reptile, Monkey and Bovine, each with its own small bonus. Midorikatai comes naturally (+10% AP).
- **Kitsune:** +2 Intrigue and +10 attraction opinion, but distrusted as trickster spirits (−5 general opinion). They know the **Fox Charm** Technique, and grow a tail per eight Immortal Cores, up to nine.

### Soul Treasures
As in Aura Clash, a slain chi-saturated beast leaves a **Soul Treasure** holding its Aura Pressure.
- **Hunt a Spirit Beast** (yearly decision): Sabretooth (600 AP), Quadrafang (900), Mawcharger (1,300), Shakengara (1,800), Drake (2,200) or Wyrm (3,000).
  - Success chance: 30% + 3% per Power and Agility rating, ±1% per 40 AP difference from the beast, between 5% and 95%.
  - Victory yields the treasure, 8 Aura Pressure, Power progress and prestige. Defeat leaves you wounded.
  - The Drake's 2,200 AP is stated in the IF; the other beasts' AP values are estimates.
- **Buy a Fishbone Soul Treasure:** 75 gold, 300 AP, once a year. The game sells it for 75 Shards.
- **Refine a Soul Treasure** into an Advancement Elixir:
  - Formula: 11% of (treasure AP − your AP), clamped between 10 + 3 × Alchemy and 100. Alchemy is the number of Alchemy perks.
  - Mortal Limits apply, except with 4+ Alchemy perks; Talent does not apply.
  - You hold up to three treasures; extras are sold for a tenth of their AP in gold.
- **AI cultivators** hunt beasts they can probably beat and refine their treasures.

### Honor and Ruthless
As in Aura Clash, every cultivator has **Honor** and **Ruthless**, two 0–100 scales that start at 50.
- **Starting values** are seeded once from personality: honest, just and brave raise Honor; deceitful, arbitrary and craven lower it; callous, sadistic, wrathful and vengeful raise Ruthless; compassionate and forgiving lower it.
- **In the Trials**, impressing a land moves them the way that land judges: Bladed honour +2 Honor, Sacred compassion −2 Ruthless, Wild strength +2 Ruthless, Cursed practicality −1 Honor.
- **Style harmony:** following the IF's style synergies, conduct in harmony with your path speeds Aura Pressure gains.
  - +10% for each Style in harmony: Akakiru with Honor ≥ 70, Aoyusumu with Ruthless ≤ 30, Kurokonton with Intrigue ≥ 15, Kiihakai with Learning ≥ 15, Midorikatai with prowess ≥ 20.
  - +5% for each Element in harmony: Light with Ruthless ≤ 35, Fire with Ruthless ≥ 75.

The Mortal Core Training menu shows both values.

### Clash of Auras (duels)
**Challenge to a Clash** (a hostile interaction, optionally to the death) starts a turn-based duel. It is inspired by Princes of Darkness's turn-based combat and built on the IF's own fights, where every exchange goes through a Core.
- **Vitality** is 3 + the Fortitude rating. A duel lasts up to 8 rounds.
- **Moves.** Each round both fighters pick one, and the moves counter each other in a cycle:
  - **Power Strike** beats Iron Guard.
  - **Iron Guard** (Fortitude) beats Chi Blast. It takes 1 less damage, and when it wins it restores 1 Vitality instead of striking.
  - **Flash Step** (Agility) beats Power Strike.
  - **Chi Blast** (Soul) beats Flash Step. It costs 1 Chi and rolls +1.
- **The roll** is 2 x the Core's rating, + Prowess / 4, + that Core's known Techniques (up to 3), + d6. Countering the foe's move adds +2, and Aura Pressure suppression (at least double the foe's) adds +2.
- **Surge my Cores** adds the Core's Surge value and hits 1 harder, spending a real Core charge.
- **Unleash a Technique:** once per duel, a fighter who knows an attack Technique (Cleave, Inferno, Shockblast, Midnight Blade and nine others) can unleash it. It costs 1 Chi, fights through the Technique's Core, adds +3 to the roll and hits 1 harder.
- **Damage:** the higher roll deals 1, +1 on a margin of 5 or more.
- **Controls:** the round log shows both rolls and the foe's move. You can also auto-resolve or yield.
- **AI:** AI-versus-AI duels resolve instantly with the same rules, and AI cultivators challenge their rivals.
- **Outcome:** the loser is wounded, or killed in a duel to the death. The winner gains prestige and Power progress.
- Vanilla duels and tournament contests are unchanged.

### Techniques, Focus and the Chi Pool
This follows the Aura Clash game's technique menu.
- **Techniques** are typed by Core: Power, Fortitude, Agility or Soul. A cultivator can know up to **25**. The mod includes 34 of the IF's Techniques with their original names and effects, such as Cleave, Hidden Dragon, Spiritwell, Palm of Endless Beating, Sacred Armor, Iaijutsu, Wavewalking, Zen Focus, Prayer Talisman and Tenebrous Rift. Some require a Style or Element, for example Inferno (Fire), Iaijutsu (Akakiru) and Combat Seals (Kiihakai).
- **Learning** grants the passive effect:
  - Aura Pressure +10 or +15.
  - Chi Pool +1.
  - Health Pool +1 (+0.2 health).
  - +5 battle AP.
  - +1 to an IF skill, mapped to CK3: Athletics → prowess, Insight → learning, Deception, Thievery and Stealth → intrigue, Persuasion → diplomacy, Craft → stewardship, Survival → epidemic resistance, Perception → scheme detection, Seals, Alchemy and Handseals → lifestyle XP.

  Techniques are learned by **Study a Path Manual** (100 gold, yearly) or **Study the Sect Library** (50 sect contribution, yearly). Both pick a learnable Technique at random, favouring your strongest Cores, Style and Elements.
- **Focus:** each Core has one Focus slot (**Meditate upon your Techniques**). A focused Technique grants **+1 Surge** to its Core or **+1 Core rating** (with +1 linked skill). Focusing a new Technique replaces the old one.
- **Innate Techniques:** Thunderfall, Iron Body, Flash Step and Energy Tide awaken when Power, Fortitude, Agility or Soul reaches rating 5, each adding +1 Surge to its Core.
- **Surge value** is 2 plus these bonuses. It is the score bonus when you push a Core to the limit in the Trials.
- **Chi Pool:** 1 + half the Soul Core rating (Soul Cores give +0.5 chi), plus Techniques. Techniques used in vanilla events spend chi before your body pays in stress and Spent Chi. Meditation restores spent chi each quarter (yearly for AI).
- **AI** cultivators study a Path Manual when they have spare gold, and fill empty Focus slots.

### Transformation Techniques
These follow the IF's Transformations. Each wraps a stronger aura, built for battle, around the body for a time. There is one per Style, plus Limitbreaker for any:

| Transformation | Style | While transformed |
|---|---|---|
| Limitbreaker | any (Freestyle) | +1 Power, +1 Health; every Core Surge +1; +10 AP from battle victories |
| Reaper | Akakiru | +2 Power, +1 Agility, +1 Health; doubled bonuses from a bladed weapon |
| Godhand | Aoyusumu | +1 Soul, Agility, Fortitude, Health and Chi; heals to full on transforming |
| Soul Domain | Kiihakai | +2 Soul, +1 Power, +2 Chi; every attack Focused (+1 to every roll) |
| Malocchio | Kurokonton | +2 Agility, +1 Fortitude, +1 Chi; a victory copies one of the foe's attack Techniques |
| Titan or Asura | Midorikatai | Titan: +2 Fortitude, +1 Power, +2 Health, +1 damage on every hit. Asura: +2 Power, +1 Fortitude, +1 Health, +1 to melee moves |

- **In the Clash of Auras**, a fighter who knows a Transformation can transform once per duel for 1 Chi. It's a free action, like surging. Each Core point is +2 to that Core's rolls, Health is Vitality, and the aura boost (+500 AP, or 250 + AP/8 from 2,000 AP) counts toward Aura Pressure suppression. The AI transforms too.
- **Requirements:** the Immortal Core, 1,500 Aura Pressure and the form's Style. Limitbreaker instead needs every Combat Core at rating 3 or more. Titan and Asura exclude each other.
- **Training** is a personal scheme, like CK3's study and Learn Language schemes: **Train a Transformation** (an interaction on yourself), or **Seek Transformation Training** (an interaction on a master who knows the form, +25% success). Its success chance grows with Martial, Style perks and Aura Pressure, and with Touched by a Heavenly Gate. A failed phase costs stress or a wound.
- **A Heavenly Gate** is the MC's way: draw a whole Gate into your aura to awaken a form at once (see below).
- The traits use their Style's icon for now.

### Seals
All 22 Seals from the Core Rulebook are castable interactions in their own **Seals** category: right-click yourself or another character.
- **Freestyle:** Craft Shard, Reinforcement, Four Winds Enhancement, Keystone, Counterseal.
- **Akakiru:** Reinforcement (Improved), Soulsoak Imbuement (releasable in a Clash for +3), Celestial Forge (exchange your Foundation, keeping its tempering).
- **Aoyusumu:** Exorcism, Prayer Engine, Heavenly Message, Divine Intervention.
- **Kiihakai:** Scry, Ward (a person, or the county you stand in), Charm, Spiritbinding (Earth or Water Elemental, Wisps or a Kami).
- **Kurokonton:** Hex, Thousand-Face Mask, Puppetmaster (a strong "Puppet" hook, from a month to permanent).
- **Midorikatai:** Subjugation Domain, Alpha Seal (bind a Spirit Beast you have just slain), Unlock Potential.
- **Requirements,** as in the rulebook: a Handseals rank (+1d6/+2d6/+3d6 = 2/5/8 Handseals perks) and/or Aura Pressure in a Style's Techniques (300/500–600/700/900 AP = the Style with 0/3/5/7 of its perks).
- **Cost:** the rulebook's AP cost is spent as Chi (1 per 100 AP), or paid in Shards at a tenth (gold).
- **Strength:** a Handseals roll of 2 dice + 1 per rank, a success on 5–6 with sixes exploding. Durations of "a day per success" become a month per success. Charm, Hex, Counterseal and Puppetmaster are contested.

### Heavenly Gates and Spirit Fruit
- **Heavenly Gates:** six a year, an area's aura surges for a season (a county modifier). Gate levels run 5–15: Outer lands 5–8, Outer North 6–9, Inner Kingdoms 8–12, Azuma Honsha 11–15. Cultivators in the region sense it.
- **Cycle the Heavenly Gate** (activity): travel there with your court's cultivators. Each gains the Gate's level plus their Athletics or Insight successes, up to triple the level, as Aura Pressure, plus Soul progress and *Touched by a Heavenly Gate* for two years. Beyond three cultivators the Gate's chi is shared out.
- At the Gate you can cycle quietly, drive off the local sect's disciples in a Clash of Auras (the winner takes half again as much), or draw the whole Gate into a Transformation.
- The first cycling drains a Gate. Unclaimed Gates go to the region's three strongest AI cultivators after 45 days.
- **Spirit Fruit Groves:** 17 special buildings placed at game start (3 on Azuma Honsha, 8 in the Inner Kingdoms, 2 in Outer North, 4 elsewhere). The county holder harvests 2 fruit a year, keeping up to 10.
- **Share Spirit Fruit** (interaction) feeds a cultivator, yourself included. A fruit gives up to 10 Aura Pressure, less for each fruit eaten that year. AI holders feed themselves and their court.

### Forged Equipment and the Soul Forge
Weapons and armour are real CK3 artifacts in the weapon and armour slots, drawn with vanilla's East Asian models.
- **Pieces:** the IF's Katana, Jian, Tanto, Kunai, Qiang, Greataxe, Kusarigama, Bo Staff, Meteor Hammer, Claws and Yumi, and Armour.
- **Materials** follow the IF's forgemaster: steel, Jade (100 Shards, Craft 2), Beastbone (80, Craft 3), Snowsteel (120, Craft 2) and Truegold (140, Craft 3). Craft is Stewardship: 10 for Craft 2, 15 for Craft 3. Each material fuels two Cores (+1 rating each in a Clash): Jade Soul and Power, Beastbone Fortitude and Agility, Snowsteel Fortitude and Soul, Truegold Power and Agility.
- **A Soul Treasure** forged in grants +1d6 to a skill. A superior-grade treasure (1,800 AP or more) fuels the material's first Core again. One Soul Treasure per piece.
- **Grades:** plain, Improved, Superior and Mastercrafted, with rising prowess and rarity.
- **In a Clash:** a weapon gives the rulebook's Armed bonus (+1, unless the foe is Armored), and a critical blow breaks plain steel armour.
- **The Soul Forge** is a crafting board modelled on Princes of Darkness's workshop. **Commission Forged Equipment** on yourself or a courtier opens it.
  1. Choose the piece and prepare the forge. The smith lays out a board of linked steps.
  2. Begin on a **Shape** step, then follow the links, one step per move. Steps include Temper, Hone, Lace Plates, Fold the Steel, Balance, Decorate, a material, a Soul Treasure for a chosen skill, and special steps from the smith's perks (Reinforcement Seal, Bladed Armory, Runic Inscription, Treasure Refining) and Elements.
  3. Press **Forge** to finish. The piece takes shape as you work it, so its effects show before it is done.
  - The smith's Stewardship sets the board's size and the number of moves; their Learning gives rerolls of the board.
  - Grade points set the grade: 1 Improved, 3 Superior, 5 Mastercrafted.
- **AI:** cultivators with spare gold forge a material weapon suited to their Style, and the strongest start the game armed.

### Heavenly Ascension Trials and the Archonate
This follows the Aura Clash game. The Exalted Council drafts young martial artists to replenish the Archons, holding the **Heavenly Ascension Trials** in the Outer West town of **Nanhou**. They're held every 10 years, first after 3; the IF's 30-year gap is shortened for play.
- **The draft:** cultivators **under 25 of the Warrior Caste** or above (see Castes) receive the Imperial draft letter, with 25 gold. Ignoring it costs 100 prestige.
- **Three zodiac Trials**, each scored **0–7** by the Imperial clerks. A score of 5 is a pass, and no one is disqualified until all three are complete:
  1. **Tiger Trial**, strength: march weighted plates to the arena wall. The base score is (Power + Fortitude Core ratings) / 2 + 1. Choose a grip (back or legs, favouring Fortitude or Power), strap on all twenty plates, help a fallen contestant, or push your Power Core to the limit.
  2. **Rabbit Trial**, speed and evasion, "about being prey". The base score is (2 × Agility + Soul) / 3 + 1. Outrun everyone, find an escape route, crash through attacks, hold back a stronger attacker, trip your neighbours, or push your Agility Core to the limit.
  3. **Dragon Trial:** medallions measure **Aura Pressure**, from 2 points below 500 AP to 7 points at 2,500 AP. Cycle quietly, defend your medallion fairly, ambush the weak, shadow a stronger group, protect a weaker contestant, or study the counting formation.
- Each score varies by ±1 with the day's luck.
- **Favor of the five Inner Kingdoms:** masked Judges watch every choice. Bladed rewards honour, Sacred compassion (Divine Favor), Mystic intelligence, Cursed practicality, and Wild ruthless strength. Choices raise or lower that land's Favor, which persists. If a choice impresses a land and you score a perfect 7, that land expends its limited pool to grant an **eighth point**.
- **Results:** a total of **15+** joins the **Archonate** with the Archonate Disciple trait (+1 monthly prestige, +3 prowess, +1 Diplomacy, +5 general opinion, 500 prestige, two Core dots, 100 cultivation XP a year). **21+** places you among the **Top Five** for another 300 prestige. The results compare you with the crowd's favourite, the strongest eligible AI entrant or a wandering prodigy.
- **AI entrants:** the three best-scoring AI entrants whose expected total passes also join the Archonate.

### Developed ranks and roaming masters

Upper Disciples receive 6–10 dots in each Combat Core (16–32 Immortal Cores) and a Jade Foundation; Sect Masters receive 12–16 dots (40–56 Immortal Cores) and a Golden Foundation. Minimums apply once on initialization, promotion and leadership changes, preserving stronger progress and existing paths.

Independent roaming cultivators appear throughout the world, initially one per eligible kingdom of origin. Roaming Adepts match Upper Disciples, Roaming Masters match Sect Masters, and rarer Roaming Grandmasters have 17–20 dots in each Core with a Heavenly Foundation. They use native wanderer pools, may visit courts and can be recruited. Find the Roaming Master trait in the character finder. Their relationships and hooks can qualify them as teachers through the normal targeted cultivation request. Annual maintenance moves only free AI wanderers and replaces deceased masters without spawning extras when one is recruited. See the [sect guide](docs/sects.md#roaming-masters) for distribution, caps and migration.

### Cultivator
A trait that grants **+0.5 health, +20 life expectancy, +10 years of fertility and +4 prowess**, and unlocks everything below.
- Cultivation is not genetically inherited; children must awaken through the available cultivation pathways.
- Spontaneous newborn/generated-character cultivation is disabled; sect founders and disciples supply established cultivators.
- It's available in the ruler designer for 80 points.
- **Request Cultivation Training** (right-click a qualifying cultivator): request an awakening ordeal from your cultivator parent, current/former cultivator guardian, friend/best friend, lover/soulmate, spouse, a member of your own sect, or a cultivator on whom you hold a usable hook. The relationship is checked against the selected teacher; an unrelated cultivator cannot substitute. Costs 100 prestige, and consumes a hook only when it is needed for that teacher. The Martial + Learning check has a 5–85% success chance; failure wounds without killing.
- **Raised by a cultivator:** from age 6, each birthday spent with a cultivator guardian, or with a cultivator parent in the same location, stores one year of **nurtured chi** (maximum 5). A player mentor chooses each year between breathing lessons (+1 Learning), dawn stances (+1 Martial) or letting the child rest; either lesson also grants the mentor 25 cultivation XP. AI mentors teach silently. On the 16th birthday, two or more years of nurtured chi trigger **The Spark of Chi**: a free awakening attempt using the normal Martial + Learning check plus 8% per year of nurture (max 95%). It shares the one-year attempt cooldown; if that cooldown is active at 16, the spark waits until 17, then fades. Declining or failing removes the stored chi, while the normal teacher and sect routes remain.
- **Seek Cultivation** (decision): Ambitious adults can instead fund their own search for 100 gold, 250 prestige and 250 piety, then face the same awakening check. Requests, offers of training and this decision share a one-year attempt cooldown; switching routes cannot bypass it.
- **NPC learners**, including courtiers and wanderers, consider awakening once a year if they are warrior-like or hardworking: Ambitious, Brave, Diligent, Martial or Prowess education rank 3+, Strong, Hale, Robust, Herculean, Berserker, Blademaster, Populist Leader, Adventurer, Military Order member, Crusader or Holy Warrior, Warrior of the Faith, Raider, Varangian, or 3+ commander traits. Ambition, diligence, bravery and aptitude increase willingness; contentment, cowardice and laziness reduce it. Injured, ill, imprisoned, incapable or frail characters wait.
- NPCs prefer an available cultivator parent, guardian/former guardian, friend, partner or fellow sect member, then a usable hook on a teacher. They retain at least 100 prestige after requesting training. Ambitious NPC rulers without a usable teacher can fund **Seek Cultivation** once they have 200 gold, 500 prestige and 500 piety. These routes use the normal costs, ordeal and shared cooldown.
- **NPC teachers** can offer training to qualifying, interested NPCs they like, with at least 500 prestige and 500 piety before paying the usual 250 of each. Compassionate, generous and diligent teachers are more willing; greedy and callous teachers are less willing. NPC offers do not force the player into an ordeal.
- **Legendary conquerors:** the fame traits **Conqueror**, **Despoiler of Byzantium** and **Greatest of Khans** grant existing Cultivators **5 / 10 / 20** randomly distributed Core dots, up to the Cores' caps. Fame does not awaken mortals or bypass the access requirements. Each reward happens once per trait, after awakening.
- Cultivation only advances from **age 16**: Core training, Foundations, Styles, Elements, perks and the lifestyle tab all wait until then.

### Decisions
All Cultivation decisions appear in their own **Cultivation** group in the decisions panel.

### Aura Pressure and Combat Cores
This follows the Aura Clash game. **Aura Pressure (AP)** is a cultivator's total spiritual power. Each of the four **Combat Cores** has a rating from 0 to 20.
- **Mortal Core Training** (decision → event): once a year, train one Core.
  - Until you hold **eight Mortal Cores in total**, "the peak of natural human power", it raises that Core by 1. Beyond that, the results of mortal training become minuscule, and Cores no longer rise.
  - Every session adds about **10 AP** and **10 progress** toward that Core's next Advancement.
  - Auto-training repeats your last choice yearly. It costs no prestige.
- **Immortal Core Advancement** (decision): the breakthrough that seizes control of the chi absorbed from the world. It requires first learning the **Immortal Core Method** (see Immortal Core below). Afterwards, each **Advance a Combat Core** binds free AP into a Core and forms a new **Immortal Core**: **100 AP, less that Core's progress**, with no cooldown. Free AP is total AP minus the AP already bound. A quarterly auto-advance toggle binds new AP into your last-advanced Core.
- **Progress** comes from using a Core:
  - Battles: Power and Fortitude, for commanders and knights.
  - Hunts: Agility.
  - Surges in the Trials.
  - Yearly practice: the Core linked to your strongest skill.
  - Progress above 100 carries over to the next Advancement.
- **AP sources:**
  - Yearly training: +10.
  - **Cycle Spirit Shards** (decision, monthly): spend `(AP + 10) / 10` gold for **16 + Soul rating** AP.
  - One fifth of every cultivation-XP reward (events, sects, Immortal Core).
  - Battles: +1 to +3.
  - Talent multiplies all AP gains.
- **Mortal Limit:** AP gains are **halved above your Mortal Limit**, then halved again for every further half of it: a quarter above 1.5×, an eighth above 2×, down to 1/32 above 3×. The limit comes from Potential Limit: Mortal I is 800 AP, Outer West's limit in the game. In the Imperial Rasen overhaul the land you are in adds its natural aura: +200 in Outer North, +1,200 in the Inner Kingdoms and +5,200 on Azuma Honsha, so a Mortal I cultivator measures 800 in the Outer lands, 1,000 in Outer North, 2,000 in the Inner Kingdoms and 6,000 in the capital.
- **Surging:** each Core's rating is also a pool of charges. In the Heavenly Ascension Trials you can push a Core to the limit (+25%, or more in the duel), spending a charge and earning progress. Meditation restores spent Cores each quarter.
- Existing cultivators keep their Cores; their current dots count as AP already bound into them.

| Core | Skill |
|---|---|
| Soul | Learning |
| Agility | Intrigue |
| Power | Martial |
| Fortitude | Stewardship |

- Every dot also has milestone bonuses:
  - dots **5 and 15**: +2 prowess each
  - dots **10 and 20**: +0.25 health and +5 years of life expectancy each
- Core progress shows as track bars on the Cultivator trait tooltip.

### Innate Potential
**Potential** is a genetic aptitude revealed when a character awakens as a Cultivator. It has two separate, fixed nine-grade tracks, **Limit** and **Talent**, each grouped into Mortal I–III, Earthly I–III and Heavenly I–III. The trait tooltip shows both exact grades. Hover each bar pip to see its named grade and full effect; pips 1, 4 and 7 mark the starts of Mortal, Earthly and Heavenly. The main trait tooltip shows the current Mortal Limit and Aura Pressure; the Limit bar lists the limit at all nine grades. Its three painted icon variants reflect the higher tier of the two aptitudes; a Heavenly icon does not imply both tracks are Heavenly.

| Grade | Mortal Limit (AP) | Talent: AP and lifestyle XP | Talent: monthly prestige |
|---|---:|---:|---:|
| Mortal I | 800 | +5% | +0.1 |
| Mortal II | 1,000 | +10% | +0.2 |
| Mortal III | 1,200 | +15% | +0.3 |
| Earthly I | 1,500 | +25% | +0.5 |
| Earthly II | 2,000 | +35% | +0.75 |
| Earthly III | 2,500 | +50% | +1 |
| Heavenly I | 3,500 | +75% | +1.5 |
| Heavenly II | 5,000 | +100% | +2 |
| Heavenly III | 8,000 | +150% | +3 |

Talent boosts native monthly lifestyle XP, and multiplies Aura Pressure gains and new shared cultivation XP rewards before dividing them between the three cultivation lifestyles. Legacy XP migration is not multiplied.

Each aptitude's fresh roll has an **86% Mortal / 13% Earthly / 1% Heavenly** distribution. Hidden gene values are assigned once and persist across failed or repeated awakening attempts. Children inherit each aptitude independently from their biological parents: with two available parents, 35% copies each parent's value, 27% rolls fresh variation, and 3% reinforces the stronger value. Two parents of the same tier can reinforce into the next tier; Heavenly reinforcement caps at grade nine. With one available parent, 75% copies that parent's value and 25% rolls fresh variation. Missing or deceased parents use the available-parent or fresh-roll fallback; historical ancestors are not retroactively assigned DNA.

CK3 does not natively inherit two independent trait-track XP values, so persistent character variables hold the genes, and the visible genetic trait mirrors them only after awakening. Mortal children keep hidden potential and must still learn cultivation through the normal pathways. Existing cultivators receive Potential at game start or the first playable quarterly pulse after loading an older save. Artwork masters, generation prompts and a labelled preview are in [assets/trait-icons/potential](assets/trait-icons/potential).

### Foundations
When a character becomes a Cultivator, or turns 16 as one, they choose **one of twelve zodiac Foundations**. The choice popup has two pages of six. Each Foundation gives +1 to a skill and a minor bonus. Fighting as a **commander or knight** tempers it through the tiers **Mortal → Iron → Jade → Golden → Heavenly**. Each tier strengthens that Foundation's own bonus, and Jade and Heavenly also add +5% knight effectiveness (Wolf gets +1 prowess there instead).

| Foundation | Base | Each tier adds |
|---|---|---|
| Dragon | +1 Diplomacy, +0.5 monthly prestige | +0.25 monthly prestige |
| Rabbit | +1 Diplomacy, +15% fertility | +5% fertility, +2 attraction opinion |
| Tiger | +1 Martial, +3 prowess | +1 prowess |
| Snake | +1 Intrigue, +5 hostile scheme success | +2 hostile scheme success |
| Stallion | +1 Martial, +10% army movement | +5% army movement |
| Ram | +1 Learning, +0.5 monthly piety | +0.25 monthly piety |
| Monkey | +1 Intrigue, +5% lifestyle XP | +2.5% lifestyle XP |
| Crane | +1 Learning, +5 years life expectancy | +2 years life expectancy |
| Wolf | +1 Martial, +10% knight effectiveness | +5% knight effectiveness |
| Boar | +1 Stewardship, +0.25 health | +0.1 health |
| Rat | +1 Stewardship, +0.5 monthly gold | +0.25 monthly gold |
| Ox | +1 Stewardship, −5% building cost | −2.5% building cost |

### Immortal Core
- **The Immortal Core Method** is a technique, shown as a trait, that you must learn first. The prerequisites are **eight Mortal Cores**, **300 Aura Pressure**, a **Foundation** and age 16. There are three ways to learn it:
  - **From a master:** right-click a cultivator who knows it and choose **Request Immortal Core Instruction** (150 prestige). They must be your parent, current or former guardian, friend, best friend, lover, soulmate, spouse or fellow sect member, or you must hold a usable hook on them. A hook is spent only if it is your only bond.
  - **From your sect:** **Study the Sect's Immortal Core Method** (100 sect contribution) is open to Upper Disciples and Sect Masters whose Sect Master knows it. Lower Disciples never see it.
  - **Through genius:** a character with the Genius trait or Heavenly Talent can **Comprehend Immortal Core Advancement** alone: 100 piety, once a year, a Learning check of 3% per point + 10% (+15% for Genius), between 5% and 90%.
- **Immortal Core Advancement** (decision): requires the method and the same prerequisites; costs 150 piety, once per year. It's a Learning + Martial check with a 5–75% chance.
- **Immortal Cores:** after the breakthrough, every Advancement forms another Immortal Core. A cultivator holds up to 8 Mortal Cores and up to 72 Immortal Cores, limited by each Core's 20-rating cap; powerful masters hold dozens. The **Immortal Cores** trait shows both counts and a track: every 8 Immortal Cores add +1 prowess and +0.1 monthly prestige, and 8, 24, 40, 56 and 72 also add +0.15 health and 3 years of life expectancy.
- **Seeded and historical characters:** every Core dot beyond the eighth counts as an Immortal Core, and holding one grants the ability. Upper Disciples hold 16–32, Sect Masters 40–56, and Grandmasters and Exalts 60–72.
- Each failure adds **+5% Insight** to the next attempt, and high Foundation tiers add more.
- Success unlocks **binding Aura Pressure into Cores** (Advance a Combat Core), and grants **+20 life expectancy and +0.5 health**, plus **60 total cultivation XP per quarter**, divided equally between the three cultivation lifestyles, whatever your current focus.

### Martial Arts Styles and Elements
- **Study a Martial Arts Style** (decision): costs 150 prestige. Choose Akakiru, Aoyusumu, Kiihakai, Kurokonton or Midorikatai. Styles are exclusive.
- **Awaken Elemental Affinity** (decision): costs 100 piety. Attune to up to **two** of Darkness, Earth, Fire, Ice, Light, Storm, Water and Wind. The choice popup has two pages of four.
- **Learning isn't guaranteed.** The chance is **4% per point** of the deciding skill, so 25 is certain. A failure refunds the cost but wounds you.
  - **Styles:** Akakiru = Stewardship, Aoyusumu = Diplomacy, Kiihakai = Learning, Kurokonton = Intrigue, Midorikatai = Martial.
  - **Elements** use the higher of two skills: Darkness = Intrigue or Learning, Earth = Stewardship or Diplomacy, Fire = Martial or Learning, Ice = Stewardship or Martial, Light = Learning or Intrigue, Storm = Learning or Stewardship, Water = Diplomacy or Martial, Wind = Martial or Intrigue.
- Each Style and Element grants +5 prowess and unlocks its own perk tree.
- Attempting a Style **or** an Element starts a shared **1-year cooldown**.

### Preserved Youth (game rule: *Cultivator Aging*, default **Slowed**)
Cultivators stay young-looking much longer, shown by the **Preserved Youth** trait.
- **When it starts:** age 22, or later if they awaken after 22. Nobody's appearance changes before then.
- **How it works:** from that point the portrait ages only **5 visible years** over as many real years as their **longevity bonus**, then ages normally from there.
- **Default** (+20 years): characters who are cultivators by 22 look **22–27 from age 22 to 42**. Every extra year of longevity (Cores, Immortal Core, Crane Foundation, Alchemy) stretches that window.
- **Late awakeners** keep their current age as the starting point. Someone who awakens at 40 looks 40–45 until about 60.
- **Fertility:** cultivators stay fertile longer, because CK3 bases fertility on apparent age while this effect is active.

**The Death Spiral:** at age **60 + their longevity bonus**, or whenever their health drops below 1 for a lasting reason, Preserved Youth ends. Low health from wounds or a passing illness (ill, pneumonia, typhus, plague, smallpox, measles, dysentery, ergotism, lover's pox) or pregnancy doesn't count.

**Still mortal:** CK3's way of keeping a portrait young also stops natural death, so the mod runs its own low-health death check for these characters. A small hidden check runs every 90 days, or every 30 days when health is below 3, only while Preserved Youth is active. It uses the vanilla odds: a monthly death chance of 25% × ((3 − health) / 3)², which is 25% at 0 health. Death is reported with the illness or wound as the cause. A cultivator who dies of measles at 42 still looks young. Their true age catches up at once and they age and die like a mortal. Cultivators whose growing strength (longevity from Cores, Immortal Core, Foundation and perks) outpaces the years can hold this off longer. Set the rule to *Normal* to turn the effect off.

### AI cultivators
Adult AI cultivators run **one short routine per year**, on a random day, through `random_yearly_everyone_pulse`. There are no constant scripts and no per-character timers. Each year, an AI cultivator:
- Does **Mortal Core Training** on a random Core until it holds eight Mortal Cores. It **cycles Shards** up to twice if it keeps 150 gold spare, and with an Immortal Core it **binds free AP** into Cores, favouring those with more progress.
- Has a **15% chance** to learn a Style (150 prestige), or else an Element (100 piety). This is subject to the shared yearly cooldown.
- Seeks the **Immortal Core Method** once it meets the prerequisites. It tries its sect first, then a master among its bonds or hooks, then genius. Once it knows the method, it has a **30% chance** to attempt the breakthrough, if it has 150 piety and Martial + Learning of at least 16.
- **With an Immortal Core**, gains 240 total cultivation XP annually, divided equally between Elements, Martial Styles, and Handseals & Alchemy. Each discipline spends only its own native perk points on learned paths and valid prerequisites; unavailable trees keep their saved points. Focus and sect/event XP feed those same pools.

Adult non-cultivators skip the annual cultivation routine. Children also receive a lightweight check for teaching from a cultivator guardian.

### Train in Cultivation
A character interaction (right-click a character). It needs a Cultivator aged 16+ as the trainer and a target who isn't a Cultivator.
- **Who you can train:** your children, current or former wards, friends/best friends, lovers/soulmates, spouses, fellow sect members, or someone holding a usable hook on you. Court membership and vassalage alone do not qualify. Children qualify directly through their parent; adult children can request training, while a parent can offer it to a minor through the existing teaching interaction. A hook is spent only when needed to obtain training.
- **Cost:** 250 piety and 250 prestige. Each person can be trained at most once per year.
- **Success chance:** 1% per point of the target's Martial and Learning, plus 1% per Combat Core dot you've unlocked (up to 100%).
- **Failure** wounds the target.
- NPC teachers can offer it to interested qualifying NPCs they like, when healthy and able to retain a resource reserve. Personality affects their willingness; NPC offers do not force player recipients into an ordeal.

### Perk-unlocked interactions (right-click a character)
- **Chi Healing:** unlocked by *Water: Healing Waters*, *Kiihakai: Mending Chi* or *Aoyusumu Mastery*. It mends one level of wounds on anyone, including yourself, with a 6-month cooldown.
- **Scry** and **Hex** are now Seals (see Seals below); *Scrying Sphere* and *Hex* still teach them.
- **Copy Technique:** unlocked by *Kurokonton: Malocchio Eyes*. Costs 100 piety, with a 1-year cooldown. The target must be **your prisoner** with an education trait. You gain 1 perk point in the lifestyle matching their education (Martial and Prowess educations both give Martial).

### Cultivation Lifestyles
Three separate lifestyle tabs are visible to Cultivators aged 16+. Each has its own experience and perk points, at **1,000 XP per point**.

| Lifestyle | Focus | Perk trees |
|---|---|---|
| **Elements** | Elemental Attunement | Your learned elements; up to two trees |
| **Martial Styles** | Physical Training | Your learned martial style |
| **Handseals & Alchemy** | Deep Meditation | Alchemy and Handseals, available to every adult cultivator |

Your selected focus generates **25 base XP per month** in its own lifestyle, increased by Talent and other monthly XP modifiers. Immortal Core income and general cultivation rewards apply Talent, then divide the total equally between all three pools: a base 150-XP manual grants 52.5 XP in each at Mortal I Talent. Unlearned Style and Element trees remain hidden, with saved points available when you learn the path. The window scrolls sideways when needed.

Existing perks keep their IDs and effects. Existing unspent Cultivation XP stays in **Handseals & Alchemy**; the old AI XP remainder transfers there once. The original focus IDs remain valid, with Physical Training now belonging to Martial Styles.

#### Perk trees
Every tree has **10 perks**:
- **Row 1:** two roots.
- **Row 2:** two perks continuing them.
- **Row 3:** a central perk that needs both.
- **Row 4:** four perks, each with a **secondary bonus**.
- **Capstone.**

Each Style and Element also favours specific men-at-arms:
- **Styles:** Akakiru → pikemen and heavy infantry (cheaper too), Aoyusumu → siege weapons, Kiihakai → archers, Kurokonton → skirmishers, Midorikatai → cavalry.
- **Elements:** Darkness → skirmishers, Earth → heavy infantry, Fire → heavy cavalry, Ice → pikemen, Light → archers, Storm → siege weapons, Water → light cavalry, Wind → archers.

| Tree | Perks (row 1 / row 2 / centre / row 4 / capstone) |
|---|---|
| **Alchemy** | Herb Lore (+0.15 health) · Poison Craft (+5 hostile scheme success)<br>Herbal Remedies (+10 epidemic resistance) · Toxicology (+5 hostile scheme success, +1 Stewardship)<br>Pill Refinement (+5% lifestyle XP)<br>Treasure Refining (-15% artifact decay, +0.25 monthly gold) · Elixir of Vigor (+0.15 health, +5% fertility) · Calming Draughts (+10% stress loss, +1 Learning) · Battlefield Salves (-5% own fatalities, +5 epidemic resistance)<br>**Grandmaster Alchemist (+5 yrs life expectancy, +0.25 health, +0.25 health-penalty negation, +1 Stewardship)** |
| **Handseals** | Craft Shard (+0.5 monthly gold) · Reinforcement (+3 holding defense, +10% garrison)<br>Counterseal (-10 enemy scheme success vs you) · Sealing Formations (-10% build time, -10% building cost)<br>Silent Seals (+1 Intrigue, +5 scheme secrecy)<br>Four Winds Enhancement (+10% stress loss, +1 Learning, +1 Diplomacy) · Warding Circles (+2 holding defense, +3 county opinion) · Binding Formations (+0.1 monthly control, +5% tax) · Shard Hoard (+0.5 monthly gold, -5% build cost)<br>**Thousand Seal Mastery (+1 Diplomacy, +1 Martial, +1 Stewardship, +1 Intrigue, +1 Learning)** |
| **Akakiru** | Crimson Edge (+5% enemy fatalities, +2 prowess) · Code of the Blade (+10% prestige gain, +10% legitimacy gain)<br>Pike Wall (+15% pikemen damage, +15% pikemen toughness, -10% pikemen maintenance) · Iron Ranks (+15% heavy infantry damage, +15% heavy infantry toughness, -10% heavy infantry maintenance)<br>Scorched Path (+5% enemy fatalities, +10% pursuit)<br>Bladed Lands Armory (-15% artifact decay, +10% knight effectiveness, -15% pikemen recruitment cost, -15% heavy infantry recruitment cost, +2 prowess) · Duelist's Honor (+5% prestige gain, +5% knight effectiveness) · Edge of Space (+10% travel speed, +5% army movement) · Severing Cut (+5% enemy fatalities, +5% pursuit)<br>**Akakiru Mastery (+2 Stewardship, +4 prowess, +10% enemy fatalities, +1 knight, +10% travel speed)** |
| **Aoyusumu** | Prayer Engine (+10% piety gain, +5 clergy opinion) · Calming Current (+10% stress loss, +5 vassal opinion)<br>Mirror Mind (+15% counter efficiency, -10 enemy scheme success vs you) · Flowing Retreat (-15% retreat losses, +2 prowess)<br>Shelter the Common Folk (+5 county opinion, +0.1 monthly control, +10 epidemic resistance)<br>Siege Prayer Engines (+20% siege weapon siege value, +15% siege weapon toughness, -10% siege weapon maintenance, +10% siege weapon damage) · Exorcist's Rite (+10 epidemic resistance, +5 same-faith opinion) · Hear the Prayers (+0.5 monthly piety, +5 clergy opinion) · Precognition (+10% counter efficiency, -5 enemy scheme success vs you)<br>**Aoyusumu Mastery (+2 Diplomacy, +4 prowess, +5 same-faith opinion, **unlocks Chi Healing**)** |
| **Kiihakai** | Fertile Fields (+0.2 capital development growth) · Ward (+4 holding defense, +10% garrison)<br>Mending Chi (-10% own fatalities, +2 prowess, **unlocks Chi Healing**) · Scrying Sphere (-10 enemy scheme success vs you, **unlocks Scry**)<br>Binding Wards (+0.2 monthly control, +10% innovation spread)<br>Sun Barrage (+20% archers damage, +10% archers toughness, -10% siege phase time, +10% archers pursuit) · Runic Empowerment (-10% artifact decay, -5% build time) · Mystic Academy (+5% lifestyle XP, +1 Learning) · Barrier of Chi (+5% army toughness, +2 defender adv.)<br>**Kiihakai Mastery (+2 Learning, +4 prowess, +10% lifestyle XP, +5% army damage)** |
| **Kurokonton** | Shadow Step (+10 hostile scheme success) · Yin Aura (+10 scheme secrecy, -10 days per scheme phase)<br>Hex (+5 dread, **unlocks Hex**) · Vanishing Arts (-20% retreat losses, +10 travel safety)<br>Malocchio Eyes (+1 Intrigue, **unlocks Copy Technique**)<br>Shadow Skirmishers (+20% skirmishers damage, +15% skirmishers toughness, +15% skirmishers pursuit, +10% raid speed) · Thousand-Face Mask (+5 travel safety, +5 scheme secrecy) · Curse Mastery (+10% dread gain, +3 dread) · Assassin's Patience (+5 hostile scheme success, -5 days per scheme phase)<br>**Kurokonton Mastery (+2 Intrigue, +4 prowess, +1 hostile scheme slot, +15% dread gain)** |
| **Midorikatai** | Iron Body (+0.25 health, +2 prowess) · Beast Clans (+2 hills adv., +2 forest adv., +2 mountains adv.)<br>Unbreaking Line (-10% own fatalities) · Strengthen the Weak (+10% levy size, +10% levy reinforcement, +5% army toughness)<br>Subjugation Domain (+25% Hunter XP, **+10% hunt success**)<br>Beast Riders (+15% light cavalry damage, +15% light cavalry toughness, +15% heavy cavalry damage, +15% heavy cavalry toughness, +10% light cavalry pursuit) · Wallbreaker (-10% siege phase time, +10% heavy infantry siege value) · Warrior-King (+1 knight, +5% knight effectiveness) · Volcanic Endurance (+0.15 health, +0.15 health-penalty negation)<br>**Midorikatai Mastery (+2 Martial, +4 prowess, +15% knight effectiveness, +5% army toughness)** |
| **Darkness Element** | Veil of Night (+10 scheme secrecy) · Shadow Ambush (+10% counter efficiency, +10% pursuit)<br>Dread Aura (+5 dread) · Devouring Dark (+5% enemy fatalities, +10% dread gain)<br>Absorption (+5 hostile scheme success)<br>Night Raiders (+15% skirmishers damage, +10% skirmishers toughness, +10% raid speed) · Snuff the Light (+5 scheme secrecy, -5 enemy scheme success vs you) · Drink the Sound (+5% counter efficiency, -10% retreat losses) · Yin Hunger (+3 dread, +5% dread gain)<br>**Darkness Avatar (+2 Intrigue, +4 prowess, +10 dread, +5 hostile scheme success)** |
| **Earth Element** | Stone Shaping (-10% build time) · Fortress Ground (+3 defender adv., +10% garrison)<br>Mineral Skin (+0.25 health, +5% army toughness) · Rich Soil (+0.15 capital development growth, +5% levy size)<br>Earthsense (+10% counter efficiency)<br>Stone Legion (+15% heavy infantry damage, +15% heavy infantry toughness, +10% heavy infantry siege value) · Walls of Stone (+3 holding defense, +5% garrison) · Fertile Plains (+5% levy size, +5% tax) · Mountain's Endurance (+0.1 health, +2 mountains adv.)<br>**Earth Avatar (+2 Stewardship, +4 prowess, -10% building cost)** |
| **Fire Element** | Wildfire (+10% enemy fatalities) · Burning Blood (+10 epidemic resistance)<br>Passion (+5 attraction opinion, +10% fertility) · Searing Advance (+3 attacker adv.)<br>Raiding Flame (+20% raid speed)<br>Blazing Charge (+15% heavy cavalry damage, +10% heavy cavalry toughness, +10% heavy cavalry pursuit) · Consuming Flames (+5% enemy fatalities, +5% dread gain) · More Fuel (+5% army damage, +2 prowess) · Flame Purge (+5 epidemic resistance, +0.1 health)<br>**Fire Avatar (+2 Martial, +4 prowess, +5% enemy fatalities)** |
| **Ice Element** | Frozen March (+3 winter adv., +10% winter movement) · Preserved Stores (+25% supply duration)<br>Frost Seal (-10% own fatalities) · Stillness (+10% stress loss)<br>Freeze the Rivers (+10% army movement)<br>Glacier Wall (+15% pikemen damage, +15% pikemen toughness, +10% pikemen screen) · Deep Freeze (+10% supply capacity, +10% supply duration) · Slowed Blood (+5% counter efficiency, +5% enemy fatalities) · Preservation (+0.15 health-penalty negation, +2 yrs life expectancy)<br>**Ice Avatar (+2 Learning, +4 prowess, +0.25 health-penalty negation)** |
| **Light Element** | Radiant Presence (+10% piety gain) · Beacon of Light (+15% diplomatic range, +5 other-culture opinion)<br>Purifying Light (+10 epidemic resistance) · Glory (+10% prestige gain)<br>Inspiring Aura (+3 court grandeur)<br>Searing Rays (+15% archers damage, +10% archers toughness, +10% archers pursuit) · Revelation (-5 enemy scheme success vs you, +5% diplomatic range) · Blinding Flash (+10% counter efficiency, +5% pursuit) · Radiant Court (+3 general opinion, +2 court grandeur)<br>**Light Avatar (+2 Diplomacy, +4 prowess, +5 other-culture opinion, +10% diplomatic range)** |
| **Storm Element** | Thunderous Charge (+15% army movement) · Thunderclap (+20% pursuit)<br>Unsubtle (+10% dread gain, +0.5 monthly prestige) · Shock Assault (+3 attacker adv.)<br>Lightning Siege (-10% siege phase time)<br>Thunder Engines (+20% siege weapon damage, +15% siege weapon siege value, +10% siege weapon toughness) · Rolling Thunder (+10% raid speed, +5% army movement) · Deafening Roar (+5% enemy fatalities, +3 dread) · Storm Front (+2 attacker adv., +3% army damage)<br>**Storm Avatar (+2 Martial, +4 prowess, +20% raid speed)** |
| **Water Element** | Healing Waters (-5% own fatalities, +2 prowess, **unlocks Chi Healing**) · Sailor's Grace (+15% naval speed, -15% embark cost, +3 coastal adv.)<br>Tidal Mending (-10% own fatalities) · Adaptation (+2 hills adv., +2 forest adv., +10% supply duration)<br>Inevitability (+0.15 monthly control)<br>Flowing Flank (+15% light cavalry damage, +10% light cavalry toughness, +10% light cavalry pursuit) · Redirect Force (+10% counter efficiency, -10% retreat losses) · Wave Walker (+10% naval speed, -10% embark cost) · River's Patience (+5 vassal opinion, +5% stress loss)<br>**Water Avatar (+2 Diplomacy, +4 prowess, +5 vassal opinion)** |
| **Wind Element** | Swift Winds (+15% travel speed) · Courier Winds (+15% diplomatic range)<br>Scout's Eye (+10% army movement, +10% counter efficiency) · Carried on the Wind (+10 travel safety)<br>Freedom (+10% stress loss)<br>Wind-Guided Arrows (+15% archers damage, +15% archers pursuit, +10% archers toughness) · Skyward Leap (+5% army movement, +10% pursuit) · Cushioned Fall (-15% retreat losses, +0.1 health) · Blades of Air (+5% enemy fatalities, +2 prowess)<br>**Wind Avatar (+2 Intrigue, +4 prowess, -20% retreat losses)** |

---

## Testing (console, launch with `-debug_mode`)

Lifestyle separation has an isolated native fixture: run `python tools/prepare_lifestyle_checks.py` and use its printed launch command. It checks independent XP, prerequisite-aware spending, point retention without a learned path, legacy AI XP migration and passive rewards. Its disposable UI includes an audit for buying Healing Waters with only the Elements pool.

Potential has a separate disposable fixture: `python tools/prepare_potential_checks.py`. It checks reveal stability, all nine grades, cost boundaries, actual manual/automatic/NPC charges, insufficient-fund and cooldown guards, shared XP bonuses, tier reinforcement and randomized distribution. `python tools/build_potential.py --check` verifies its generated production files.

Static checks run without the game: `python -m unittest discover -s tools -p "test_*.py"`. Event-override and tracker checks need the installed game files; they skip unless CK3 is at the default Steam path or `CK3_GAME_ROOT` points at its `game` directory.

Awakening access and decision costs have an isolated native fixture: run `python tools/prepare_awakening_checks.py`, launch with the printed arguments, and require `AC_AWAKENING_QA COMPLETE`, no failed assertions and an empty error log. The same fixture covers childhood nurture and the Spark of Chi. Add `--ui` to inspect the teacher's right-click menu, send an actual request and verify its cost with the audit button. The fixture changes only its disposable game.
```
add_trait ac_cultivator
effect = { add_prestige = 1000 add_piety = 1000 }
effect = { ac_gain_cultivation_study_xp_effect = { XP = 15000 } }
```
Problems are logged to `Documents/Paradox Interactive/Crusader Kings III/logs/error.log`; search it for `ac_`.

The vanilla event overrides are generated from the installed CK3 event definitions. Edit `tools/event_option_specs.py`, `tools/event_expansion_specs.py`, `tools/event_activity_specs.py` or `tools/event_dlc_specs.py`, then run:
```
python tools/build_event_overrides.py --game-root "C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game"
python tools/build_event_overrides.py --check
python tools/build_event_tracker.py
python tools/build_event_tracker.py --check
python -m unittest discover -s tools -p "test_*.py" -v
```
The builder refuses game versions other than 1.20.1 until their upstream changes are reviewed. `tools/event_override_sources.json` records the source event hashes. Regression checks verify preserved vanilla options and cleanup, fatal intervention gates, linked tournament outcomes, captive eligibility, native event references, file-local helper dependencies, healing cooldowns and localization. Activity checks also cover jockey eligibility, deferred fall injuries, board-game resolution, exact brawl repairs, murder-feast bookkeeping and the exclusion of ordinary duels. They do not replace an in-game playtest: use a separate debug save to test travel, disaster contracts, plagues, prison, school techniques, tournaments, hunts, court petitions and fatal outcomes with and without the required abilities. Most of these events require scopes supplied by their normal gameplay chains; firing a bare event ID from the console is insufficient.

To refresh the Excel workbook after generating the registry, run `node tools/build_event_tracker.mjs` with `@oai/artifact-tool` available through the external workspace runtime (`tools/node_modules` may be a junction to that runtime's `node_modules`). The workbook is generated from `docs/event-registry.json`; make persistent changes in the event specifications. Tracker checks verify complete coverage, sorting and source locations. DLC checks also cover restored examination preparation, the palace multiplier, noncombat rescue follow-ups, paid construction, native herd losses, driver scopes and the exclusion of catastrophic Greek-fire flags. CK3 Tiger 1.19 does not recognize several native 1.20.1 religious stress/fulfillment tokens, so its diagnostics require review rather than a blanket pass/fail claim.

---

## Repository layout
| Path | Contents |
|---|---|
| `AuraClash.mod` | Launcher descriptor |
| `AuraClash/descriptor.mod` | In-folder descriptor |
| `AuraClash/common/` | Traits, decisions, lifestyle, perks, focuses, interactions, on_actions, game rule, scripted triggers/effects/values/GUIs |
| `AuraClash/events/` | Events (Mortal Core Training, Style, Element and Foundation choice) |
| `AuraClash/gui/` | Lifestyle window (modified copy of vanilla) |
| `AuraClash/gfx/` | Icons and illustrations |
| `AuraClash/localization/` | English text |

All script keys use the `ac_` prefix to avoid clashing with vanilla or other mods.

---

## Imperial Rasen overhaul (in development)
The mod is becoming a full overhaul set in Imperial Rasen, the spiral continent of Aura Clash. `tools/build_rasen_map.py` generates the map geometry (1,157 land provinces across the five Inner Kingdoms, Azuma Honsha and the four Outer provinces), title hierarchy and regions into `AuraClash/` from the painted world map. It includes the Exalted Council (five Exalts voting on imperial decrees every three years, and sponsoring favourites in the Trials), the Ice Incursions of Outer North, and races and castes by culture. `AuraClash/` loads and plays in CK3 1.20.1: load it after `AuraClash/` and pick the Heavenly Ascension Trials bookmark (3000.3.1). See the [overhaul plan](docs/overhaul.md) for the setting, design and remaining steps.

## Roadmap
- Lore-accurate refinements of the current perks, plus capstone traits
- Prayer Talisman requirement for Aoyusumu's Chi Healing
- Cultivator gained through a good tutor (childhood nurture by a cultivator guardian or parent is implemented)
- Additional artwork for perks, decisions and interface elements

---

## License
This repository uses more than one license. **[NOTICE.md](NOTICE.md) lists which license covers which files.**
- **Code:** MIT. See [LICENSE](LICENSE).
- **Aura Clash setting content** (names, lore, localization text and artwork): all rights reserved, with permission to use it in CK3 mods and submods of this mod, non-commercially, with credit. See [LICENSE-CONTENT.md](LICENSE-CONTENT.md).
- **Files derived from Crusader Kings III** remain © Paradox Interactive.

"Aura Clash" is a trademark of Aurillian Productions LLC. This is an unofficial mod and is not affiliated with or endorsed by Paradox Interactive.

More Aura Clash: [auraclash.com](https://www.auraclash.com) · [banishedtales.com](https://www.banishedtales.com)

The Martial Styles and Elements lifestyle badge DDS files reuse CK3 artwork owned by Paradox Interactive; the code license does not change ownership of that artwork.
