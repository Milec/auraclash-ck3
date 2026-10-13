# Aura Clash — Crusader Kings III Mod

Bring the cultivation system of **Aura Clash**, an eastern-fantasy (xianxia/wuxia) setting, into Crusader Kings III. Awaken as a Cultivator, train your four Combat Cores, temper your Foundation in battle, master a Martial Arts Style and two Elements, and condense an Immortal Core.

**Version:** 0.2.0 · **Game version:** CK3 1.x · **Status:** early and playable; many perks are still placeholders

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
- **Start a new game** when updating from v0.1. Tree and perk keys were renamed in v0.2.
- `AuraClash/gui/window_character_lifestyle.gui` **replaces** the vanilla lifestyle window. It will conflict with other mods that edit that window, including Princes of Darkness and most UI overhauls.
- Otherwise the mod only adds new content. Its on_actions are appended to vanilla's, and no vanilla scripts are overwritten.

---

## Features

### Cultivator
A trait that grants **+0.5 health, +10 life expectancy and +4 prowess**, and unlocks everything below.
- Children inherit it **25%** of the time.
- Newborns and generated characters get it at random **0.5%** of the time.
- It's available in the ruler designer for 80 points.
- **Awaken Cultivation** (decision): costs 100 prestige, usable once per year. It's a Martial + Learning check with a 5–85% chance. Failure leaves you wounded, but never kills you.

### Mortal Core Training
- **Mortal Core Training** (decision → event): costs 100 prestige, once per year. It raises one Combat Core, which raises its linked skill by 1, up to +20 per Core:

| Core | Skill |
|---|---|
| Soul | Learning |
| Agility | Intrigue |
| Power | Martial |
| Fortitude | Stewardship |

- Core progress shows as track bars on the Cultivator trait tooltip.
- All four options stay visible but greyed out until the yearly cooldown ends.
- **Auto-training:** a toggle in the same event repeats your last choice each year, whenever you can pay. Open the decision again to turn it off.

### Foundation
A tiered trait: **Mortal → Iron → Jade → Golden → Heavenly**. Cultivators gain it in their first battle as a **commander or knight**, and every battle adds XP (more for winning, more for commanders).

### Immortal Core
- **Immortal Core Advancement** (decision): costs 150 piety, once per year. It's a Learning + Martial check with a 5–75% chance.
- Each failure adds **+5% Insight** to the next attempt, and high Foundation tiers add more.
- Success grants **+20 life expectancy and +0.5 health**, plus **20 Cultivation lifestyle XP every month**, whatever your current focus.

### Martial Arts Styles and Elements
- **Study a Martial Arts Style** (decision): costs 150 prestige. Choose one of **Akakiru, Aoyusumu, Kiihakai, Kurokonton or Midorikatai**. Styles are exclusive.
- **Awaken Elemental Affinity** (decision): costs 100 piety. Attune to up to **two** of **Darkness, Earth, Fire, Ice, Light, Storm, Water and Wind**.
- Each Style and Element grants +5 prowess and unlocks its own perk tree.
- Learning a Style **or** an Element starts a shared **1-year cooldown** on both decisions.

### Chi Healing
A character interaction that mends one level of wounds on any character, including yourself, with a 6-month cooldown. It's unlocked by the *Water: Healing Waters*, *Kiihakai: Mending Chi* or *Aoyusumu: Mastery* perks.

### Cultivation Lifestyle
A seventh lifestyle tab, visible only to Cultivators.
- **Focuses:** Closed-Door Cultivation and Martial Seclusion.
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
| `AuraClash/common/` | Traits, decisions, lifestyle, perks, focuses, interactions, on_actions, scripted triggers/effects/values/GUIs |
| `AuraClash/events/` | Events (Mortal Core Training, Style and Element choice) |
| `AuraClash/gui/` | Lifestyle window (modified copy of vanilla) |
| `AuraClash/gfx/` | Icons and illustrations |
| `AuraClash/localization/` | English text |

All script keys use the `ac_` prefix to avoid clashing with vanilla or other mods.

---

## Roadmap
- Lore-accurate perks to replace the remaining placeholders, plus capstone traits
- Prayer Talisman requirement for Aoyusumu's Chi Healing
- Cultivator gained through a good tutor, or a childhood event when raised by a cultivator
- NPC cultivators starting with a Style or Element
- Final artwork (the current icons are placeholders)

---

## License
This repository uses more than one license. **[NOTICE.md](NOTICE.md) lists which license covers which files.**
- **Code:** MIT. See [LICENSE](LICENSE).
- **Aura Clash setting content** (names, lore, localization text and artwork): all rights reserved, with permission to use it in CK3 mods and submods of this mod, non-commercially, with credit. See [LICENSE-CONTENT.md](LICENSE-CONTENT.md).
- **Files derived from Crusader Kings III** remain © Paradox Interactive.

"Aura Clash" is a trademark of Aurillian Productions LLC. This is an unofficial mod and is not affiliated with or endorsed by Paradox Interactive.

More Aura Clash: [auraclash.com](https://www.auraclash.com) · [banishedtales.com](https://www.banishedtales.com)
