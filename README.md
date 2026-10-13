# Aura Clash — Crusader Kings III Mod

Bring the cultivation system of **Aura Clash**, an eastern-fantasy (xianxia/wuxia) setting, into Crusader Kings III. Awaken as a Cultivator, train your four Combat Cores, temper your Foundation in battle, master a Martial Arts Style and two Elements, and condense an Immortal Core.

**Version:** 0.4.0 · **Game version:** CK3 1.x · **Status:** early and playable; many perks are still placeholders

---

## Installation

### Manual
1. Download or clone this repository.
2. Copy **both** `AuraClash.mod` and the `AuraClash/` folder into your CK3 mod directory:
   - Windows: `Documents\Paradox Interactive\Crusader Kings III\mod\`
   - Linux: `~/.local/share/Paradox Interactive/Crusader Kings III/mod/`
   - macOS: `~/Documents/Paradox Interactive/Crusader Kings III/mod/`
3. Enable **Aura Clash** in your launcher playset.

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
- Otherwise the mod only adds new content. Its on_actions are appended to vanilla's, and no vanilla scripts are overwritten.

---

## Features

### Cultivator
A trait that grants **+0.5 health, +20 life expectancy, +10 years of fertility and +4 prowess**, and unlocks everything below.
- Children inherit it **25%** of the time.
- Newborns and generated characters get it at random **0.5%** of the time.
- It's available in the ruler designer for 80 points.
- **Awaken Cultivation** (decision): costs 100 prestige, usable once per year. It's a Martial + Learning check with a 5–85% chance. Failure leaves you wounded, but never kills you.
- **AI rulers** only attempt Awaken Cultivation if they are warrior-like or hardworking. That means any of: Ambitious, Brave, Diligent, Martial or Prowess education rank 3+, Strong, Hale, Robust, Herculean, Berserker, Blademaster, Populist Leader, Adventurer, Military Order member, Crusader or Holy Warrior, Warrior of the Faith, Raider, Varangian, or 3+ commander traits.
- **Legendary conquerors:** the fame traits **Conqueror**, **Despoiler of Byzantium** and **Greatest of Khans** grant the Cultivator trait if the character doesn't have it, plus **5 / 10 / 20** randomly distributed Core dots. Characters who are already Cultivators still get the dots, up to the Cores' caps. This happens once per trait.
- Cultivation only advances from **age 16**: Core training, Foundations, Styles, Elements, perks and the lifestyle tab all wait until then.

### Decisions
All Cultivation decisions appear in their own **Cultivation** group in the decisions panel.

### Mortal Core Training
- **Mortal Core Training** (decision → event): costs 100 prestige, once per year. It raises one Combat Core, which raises its linked skill by 1, up to +20 per Core:

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
- All four options stay visible but greyed out until the yearly cooldown ends.
- **Auto-training:** a toggle in the same event repeats your last choice each year, whenever you can pay. Open the decision again to turn it off.

### Foundations
When a character becomes a Cultivator (or turns 16 as one), they choose **one of twelve zodiac Foundations**. Each gives +1 to a skill and a minor bonus:

| Foundation | Bonus | | Foundation | Bonus |
|---|---|---|---|---|
| Dragon | +1 Diplomacy, +0.5 monthly prestige | | Monkey | +1 Intrigue, +5% lifestyle XP |
| Rabbit | +1 Diplomacy, +15% fertility | | Crane | +1 Learning, +5 years life expectancy |
| Tiger | +1 Martial, +3 prowess | | Wolf | +1 Martial, +10% knight effectiveness |
| Snake | +1 Intrigue, +5% hostile scheme success | | Boar | +1 Stewardship, +0.25 health |
| Stallion | +1 Martial, +10% army movement speed | | Rat | +1 Stewardship, +0.5 monthly gold |
| Ram | +1 Learning, +0.5 monthly piety | | Ox | +1 Stewardship, −5% building cost |

Fighting as a **commander or knight** tempers your Foundation through the tiers **Mortal → Iron → Jade → Golden → Heavenly** (shown as, for example, *Jade Tiger Foundation*). Each tier adds prowess, knight effectiveness and advantage. Players pick through an event; the AI picks automatically, weighted toward its best skill.

### Immortal Core
- **Immortal Core Advancement** (decision): costs 150 piety, once per year. It's a Learning + Martial check with a 5–75% chance.
- Each failure adds **+5% Insight** to the next attempt, and high Foundation tiers add more.
- Success grants **+20 life expectancy and +0.5 health**, plus **20 Cultivation lifestyle XP every month**, whatever your current focus.

### Martial Arts Styles and Elements
- **Study a Martial Arts Style** (decision): costs 150 prestige. Choose one of **Akakiru, Aoyusumu, Kiihakai, Kurokonton or Midorikatai**. Styles are exclusive.
- **Awaken Elemental Affinity** (decision): costs 100 piety. Attune to up to **two** of **Darkness, Earth, Fire, Ice, Light, Storm, Water and Wind**.
- Each Style and Element grants +5 prowess and unlocks its own perk tree.
- Learning a Style **or** an Element starts a shared **1-year cooldown** on both decisions.

### Preserved Youth (game rule: *Cultivator Aging*, default **Slowed**)
Cultivators stay young-looking much longer.
- **When it starts:** age 22, or later if they awaken after 22. Nobody's appearance changes before then.
- **How it works:** from that point the portrait ages only **5 visible years** over as many real years as their **longevity bonus**, then ages normally from there.
- **Default** (+20 years): characters who are cultivators by 22 look **22–27 from age 22 to 42**. Every extra year of longevity (Cores, Immortal Core, Crane Foundation, Alchemy) stretches that window.
- **Late awakeners** keep their current age as the starting point. Someone who awakens at 40 looks 40–45 until about 60.
- **Fertility:** cultivators stay fertile longer, because CK3 bases fertility on apparent age while this effect is active.

**The Death Spiral:** at age **60 + their longevity bonus**, or whenever their health drops below 1 for a lasting reason, Preserved Youth ends. Low health from wounds or a passing illness (ill, pneumonia, typhus, plague, smallpox, measles, dysentery, ergotism, lover's pox) or pregnancy doesn't count.

**Still mortal:** CK3's way of keeping a portrait young also stops natural death, so the mod runs its own low-health death check for these characters. A small hidden check runs every 90 days, or every 30 days when health is below 3, only while Preserved Youth is active. It uses the vanilla odds: a monthly death chance of 25% × ((3 − health) / 3)², which is 25% at 0 health. Death is reported with the illness or wound as the cause. A cultivator who dies of measles at 42 still looks young. Their true age catches up at once and they age and die like a mortal. Cultivators whose growing strength (longevity from Cores, Immortal Core, Foundation and perks) outpaces the years can hold this off longer. Set the rule to *Normal* to turn the effect off.

### AI cultivators
Adult AI cultivators run **one short routine per year**, on a random day, through `random_yearly_everyone_pulse`. There are no constant scripts and no per-character timers. Each year, an AI cultivator:
- **Trains a Core** (one picked at random, skipping maxed ones) if it has more than 300 prestige.
- Has a **15% chance** to learn a Style (150 prestige), or else an Element (100 piety). This is subject to the shared yearly cooldown.
- Has a **30% chance** to attempt an Immortal Core, if it has 150 piety and Martial + Learning of at least 16.
- **With an Immortal Core**, banks 240 Cultivation XP. Each time the bank passes 1,000, it unlocks its next perk in this order: Style, then Elements, then Alchemy, then Handseals.

Non-cultivators only cost a single trait check, so the load is negligible.

### Train in Cultivation
A character interaction (right-click a character). It needs a Cultivator aged 16+ as the trainer and a target who isn't a Cultivator.
- **Who you can train:** your **courtiers**, your **vassals**, or your **children within diplomatic range**. Anyone else shows the option greyed out.
- **Cost:** 250 piety and 250 prestige. Each person can be trained at most once per year.
- **Success chance:** 1% per point of the target's Martial and Learning, plus 1% per Combat Core dot you've unlocked (up to 100%).
- **Failure** wounds the target.
- The AI does not use this interaction.

### Chi Healing
A character interaction that mends one level of wounds on any character, including yourself, with a 6-month cooldown. It's unlocked by the *Water: Healing Waters*, *Kiihakai: Mending Chi* or *Aoyusumu: Mastery* perks.

### Cultivation Lifestyle
A seventh lifestyle tab, visible only to Cultivators aged 16+, with a gold XP bar.
- **Focuses:** Deep Meditation and Physical Training.
- **Trees shown, in order:** Alchemy, then Handseals, then your Style, then your Element(s) alphabetically. Trees you haven't unlocked stay hidden.
- The window scrolls sideways when the trees don't fit on screen.

#### Linked skills
Placeholder perks in Style and Element trees give **+1 to the linked skill and +2 prowess**; capstones give +2 and +4.

| Style | Skill | | Element | Skill |
|---|---|---|---|---|
| Akakiru | Stewardship | | Darkness | Intrigue |
| Aoyusumu | Diplomacy | | Earth | Stewardship |
| Kiihakai | Learning | | Fire | Martial |
| Kurokonton | Intrigue | | Ice | Learning |
| Midorikatai | Martial | | Light | Diplomacy |
| | | | Storm | Martial |
| | | | Water | Diplomacy |
| | | | Wind | Intrigue |

#### Mechanic perks
These replace placeholders with real CK3 effects:

| Tree | Perks |
|---|---|
| Akakiru | Crimson Edge (+5% enemy fatalities) · Scorched Path (+5% enemy fatalities, +10% pursuit) · Mastery (+10% enemy fatalities) |
| Aoyusumu | Calming Current (+10% stress loss) · Flowing Retreat (−15% retreat losses) · Mastery (Chi Healing) |
| Kiihakai | Fertile Fields (+0.2 capital development growth) · Mending Chi (−10% own fatalities, Chi Healing) · Binding Wards (+0.2 monthly control growth) · Mastery (+0.2 development growth) |
| Kurokonton | Shadow Step (+10% hostile scheme success) · Vanishing Arts (−20% retreat losses) · Mastery (+1 hostile scheme) |
| Midorikatai | Iron Body (+0.25 health) · Unbreaking Line (−10% own fatalities) · Rooted Stance (+3 defender advantage) · Mastery (+15% knight effectiveness) |
| Darkness | Veil of Night (+5% scheme success) · Dread Aura (+5 dread) · Avatar (+10 dread) |
| Earth | Stone Shaping (−10% build time) · Fortress Ground (+3 defender advantage) · Avatar (+0.25 health) |
| Fire | Wildfire (+10% enemy fatalities) · Searing Advance (+3 attacker advantage) · Avatar (+5% enemy fatalities) |
| Ice | Frozen March (+3 winter advantage) · Preserved Stores (+25% supply duration) |
| Light | Radiant Presence (+10% piety) · Purifying Light (+10 epidemic resistance) |
| Storm | Thunderous Charge (+15% army movement speed) · Lightning Pursuit (+20% pursuit) |
| Water | Healing Waters (−5% own fatalities, Chi Healing) · Tidal Mending (−10% own fatalities) |
| Wind | Swift Winds (+15% travel speed) · Carried on the Wind (+10% army movement speed) · Avatar (−20% retreat losses) |

---

## Testing (console, launch with `-debug_mode`)
```
add_trait ac_cultivator
effect = { add_prestige = 1000 add_piety = 1000 }
effect = { add_ac_cultivation_lifestyle_xp = 5000 }
```
Problems are logged to `Documents/Paradox Interactive/Crusader Kings III/logs/error.log`; search it for `ac_`.

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

## Roadmap
- Lore-accurate perks to replace the remaining placeholders, plus capstone traits
- Prayer Talisman requirement for Aoyusumu's Chi Healing
- Cultivator gained through a good tutor, or a childhood event when raised by a cultivator
- Final artwork (the current icons are placeholders)

---

## License
This repository uses more than one license. **[NOTICE.md](NOTICE.md) lists which license covers which files.**
- **Code:** MIT. See [LICENSE](LICENSE).
- **Aura Clash setting content** (names, lore, localization text and artwork): all rights reserved, with permission to use it in CK3 mods and submods of this mod, non-commercially, with credit. See [LICENSE-CONTENT.md](LICENSE-CONTENT.md).
- **Files derived from Crusader Kings III** remain © Paradox Interactive.

"Aura Clash" is a trademark of Aurillian Productions LLC. This is an unofficial mod and is not affiliated with or endorsed by Paradox Interactive.

More Aura Clash: [auraclash.com](https://www.auraclash.com) · [banishedtales.com](https://www.banishedtales.com)
