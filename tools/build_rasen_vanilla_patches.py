"""Patch vanilla files that crash CK3 on the Imperial Rasen map.

Vanilla scripts name Earth's titles, characters and provinces directly. A missing title
or character only logs an error, but a missing province id (`province:6650`) can crash
the game, and Imperial Rasen stops at province 1322. The mod therefore overrides each
affected vanilla file with a copy read from the installed game, changing only:

- `province:N` for any N beyond the map: replaced by the map's last impassable ocean
  zone, which never holds a holding, character or army, so those checks are false.
- `barony ?= title:b_constantinople` / `title:b_roma` in common/buildings/
  00_special_buildings.txt: replaced by `always = no` (Theodosian and Aurelian Walls).
- Game-start setup of Earth's military and monastic orders, and two test events, in
  common/on_action/game_start.txt: commented out (each logged hundreds of errors).
- Earth counties in the Japanese house-name table (common/scripted_effects/
  10_dlc_tgp_japan_scripted_effects.txt): replaced by a never-held stub title, so the table
  parses without errors and its county conditions are simply false.
- Vanilla holy sites whose county or barony is not on the map: pointed at Azuma Honsha
  (c_azuma / b_azuma), so vanilla faiths still have valid holy sites.

The Atlantis total-conversion template patches the same kinds of lines.

Usage: python tools/build_rasen_vanilla_patches.py [--check] [--game-root <game>]
Needs CK3_GAME_ROOT (or --game-root); without it, prints a notice and does nothing.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import build_event_overrides as overrides
import build_rasen_peace as peace

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
SCAN = ('common', 'events', 'gfx/interface/illustrations')
LINE_EDITS = {
    'common/buildings/00_special_buildings.txt': [
        ('\t\tbarony ?= title:b_constantinople\n', '\t\talways = no # Imperial Rasen: no Constantinople\n'),
        ('\t\tbarony ?= title:b_roma\n', '\t\talways = no # Imperial Rasen: no Rome\n'),
    ],
    # New courtiers take a culture chosen by Earth region, with the ruler's own culture only for
    # pagans; on this map no region matches and generation fails. Always allow the ruler's culture.
    'common/scripted_character_templates/00_pool_repopulation_character_templates.txt': [
        ('\t\troot.culture = {\n\t\t\ttrigger = {\n\t\t\t\troot.faith = { religion = { is_in_family = rf_pagan } }\n',
         '\t\troot.culture = {\n\t\t\ttrigger = {\n\t\t\t\talways = yes # Imperial Rasen: the ruler\'s own culture\n'),
    ],
}
LINE_EDITS['common/on_action/game_start.txt'] = [
    ('\t\tdebug_portraits.1 \t\t\t\t\t# Debug portraits for animation testing\n', '\t\t# Imperial Rasen: no debug portraits\n'),
    ('\t\teasteregg_event.0001\t\t\t\t# Charna and Jakub duel.\n', '\t\t# Imperial Rasen: no Earth easter egg\n'),
    ('\t\t\tset_up_historical_monastic_orders_effect = yes\n', '\t\t\t# Imperial Rasen: no Earth monastic orders\n'),
    ('\t\tset_up_historical_military_orders_effect = yes\n', '\t\t# Imperial Rasen: no Earth military orders\n'),
    ('\t\tsetup_tributaries_effect = yes # defined in 00_tributary_setup_effect.txt\n', '\t\t# Imperial Rasen: no Earth tributaries\n'),
]
# China's wall great projects check dozens of Chinese baronies and were the bulk of the error log once
# Rasen's hegemony took the h_china key (about 95,000 errors a century). They never apply to Rasen.
LINE_EDITS['common/great_projects/types/00_great_project_types.txt'] = [
    ('\t\t# You are the hegemon or a relevant minister\n', '\t\talways = no # Imperial Rasen: no Great Wall of China\n', 4),
]
# The Council Peace (tools/build_rasen_peace.py): great lords need leave to fight; Azuma Honsha falls only to rebellion.
LINE_EDITS['common/scripted_triggers/00_war_and_peace_triggers.txt'] = peace.PEACE_EDITS
LINE_EDITS['common/casus_belli_types/10_tgp_china_wars.txt'] = peace.PEACE_CB_EDITS
# Files whose missing Earth counties become a stub title that is never held.
TITLE_STANDIN_FILES = ('common/scripted_effects/10_dlc_tgp_japan_scripted_effects.txt',
                       # The Greek fire decision checked Constantinople's county on every look at the decisions.
                       'common/decisions/dlc_decisions/ep3_decisions.txt')
TITLE_STANDIN = 'k_yamato'
COUNTY = re.compile(r'title:(c_\w+)')
# Files whose checks for one of Earth's dynasties become plainly false (each logged an error
# every time the game looked for legends, thousands of times over a few years).
DYNASTY_FILES = ('common/legends/legend_seeds/00_legend_seeds.txt',
                 'common/decisions/80_major_decisions_british_isles.txt')
DYNASTY = re.compile(r'dynasty \??= dynasty:\w+')
PROVINCE = re.compile(r'province:(\d+)')
HOLY_SITES = 'common/religion/holy_site_types/00_holy_site_types.txt'
SITE_COUNTY, SITE_BARONY = 'c_azuma', 'b_azuma'


def our_titles():
    text = (OUT / 'common/landed_titles/00_rasen_titles.txt').read_text(encoding='utf-8-sig')
    return set(re.findall(r'\b([cb]_\w+) = \{', text))


def map_limits():
    """Highest province id, and the last impassable ocean zone (the stand-in)."""
    default = (OUT / 'map_data/default.map').read_text(encoding='utf-8-sig')
    ocean = re.search(r'impassable_seas = RANGE \{ (\d+) (\d+) \}', default)
    return int(ocean.group(2)), int(ocean.group(2))


def affected(game: Path, last: int):
    found = set(LINE_EDITS) | {HOLY_SITES} | set(TITLE_STANDIN_FILES) | set(DYNASTY_FILES)
    for folder in SCAN:
        for path in (game / folder).rglob('*.txt'):
            text = path.read_text(encoding='utf-8-sig', errors='replace')
            if any(int(n) > last for n in PROVINCE.findall(text)):
                found.add(path.relative_to(game).as_posix())
    return sorted(found)


def render(game: Path):
    last, standin = map_limits()
    files = {}
    for relative in affected(game, last):
        text = (game / relative).read_bytes().decode('utf-8-sig').replace('\r\n', '\n')
        for old, new, *count in LINE_EDITS.get(relative, []):
            expected = count[0] if count else 1
            if text.count(old) != expected:
                raise SystemExit(f'{relative}: expected {expected} of "{old.strip()}" (game version changed?)')
            text = text.replace(old, new)
        text = PROVINCE.sub(lambda m: m.group(0) if int(m.group(1)) <= last else f'province:{standin}', text)
        ours = our_titles()
        if relative in TITLE_STANDIN_FILES:
            text = COUNTY.sub(lambda m: m.group(0) if m.group(1) in ours else f'title:{TITLE_STANDIN}', text)
        if relative in DYNASTY_FILES:
            text = DYNASTY.sub('always = no # Imperial Rasen: none of Earth\'s dynasties', text)
        if relative == HOLY_SITES:
            text = re.sub(r'(\bcounty = )(c_\w+)', lambda m: m.group(0) if m.group(2) in ours else m.group(1) + SITE_COUNTY, text)
            text = re.sub(r'(\bbarony = )(b_\w+)', lambda m: m.group(0) if m.group(2) in ours else m.group(1) + SITE_BARONY, text)
        header = ('# Generated by tools/build_rasen_vanilla_patches.py from CK3 1.20.1: vanilla, except that\n'
                  f'# provinces beyond Imperial Rasen point to ocean zone {standin}, holy sites off the map to\n'
                  f'# {SITE_COUNTY}, and lines marked "Imperial Rasen" or naming the stub title:{TITLE_STANDIN}.\n')
        files[relative] = ('﻿' + header + text).encode('utf-8')
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--game-root', type=Path, default=overrides.DEFAULT_GAME)
    args = parser.parse_args()
    if not (args.game_root / 'common').exists():
        print('CK3 game files not found; skipping (set CK3_GAME_ROOT).')
        return
    files = render(args.game_root)
    if args.check:
        stale = [r for r, d in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale patched files: ' + ', '.join(stale))
    else:
        for relative, data in files.items():
            path = OUT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'Vanilla patches: {len(files)} file(s).')


if __name__ == '__main__':
    main()
