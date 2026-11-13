"""Generate the Council's Peace of Imperial Rasen for AuraClash/.

Under the hegemony's Council Peace law (the default for every Celestial realm, read from the top
liege), a duke or above needs a usable hook on their liege to declare war on another duke or above.
Counts are exempt and may feud freely. The hegemon may lift the peace by law. Azuma Honsha cannot be
attacked by a declared war from within the hegemony at all: it falls only to open rebellion
(faction wars do not use the declare-war interaction).

The rules themselves are two edits to vanilla's common/scripted_triggers/00_war_and_peace_triggers.txt,
made by tools/build_rasen_vanilla_patches.py (PEACE_EDITS below); this builder writes the law.

Writes (into AuraClash/):
  common/law_groups/rasen_peace_law_groups.txt
  common/laws/rasen_peace_laws.txt
  localization/english/rasen_peace_l_english.yml

Usage: python tools/build_rasen_peace.py [--check]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
BOM = '﻿'
PEACE_FLAG = 'rasen_great_lords_need_leave'
LIFT_PRESTIGE = 500

# Applied to vanilla's 00_war_and_peace_triggers.txt by build_rasen_vanilla_patches.py.
PEACE_EDITS = [
    # A duke or above needs a hook on their liege to make war on another duke or above.
    # (Each edit stays on its own line so the patched file keeps vanilla's line numbers.)
    ('\t\tliege = { has_realm_law_flag = vassal_all_wars_banned }\n',
     '\t\tliege = { has_realm_law_flag = vassal_all_wars_banned }'
     f' AND = {{ top_liege = {{ has_realm_law_flag = {PEACE_FLAG} }} highest_held_title_tier >= tier_duchy'
     ' scope:recipient = { highest_held_title_tier >= tier_duchy } } # Imperial Rasen: the Council Peace (counts are exempt)\n'),
    # Azuma Honsha falls only to open rebellion, never to a war declared from within the hegemony.
    ('\t\tNOT = { has_strong_hook = scope:attacker_check }\n',
     '\t\tNOT = { has_strong_hook = scope:attacker_check }'
     ' trigger_if = { limit = { exists = title:h_china.holder scope:attacker_check.top_liege = title:h_china.holder'
     ' capital_province ?= { geographical_region = world_rasen_azuma } }'
     ' custom_tooltip = { text = rasen_azuma_protected_tt always = no } } # Imperial Rasen: Azuma Honsha falls only to open rebellion\n'),
]
# The Expansion era of the dynastic cycle lets non-Celestial vassals seize counties and duchies from each
# other (china_seize_county_cb, china_seize_duchy_cb). Under the Council Peace a great lord still needs a
# hook on their liege for it. The line occurs once in each casus belli (third element: expected count).
PEACE_CB_EDITS = [
    ('\t\t\t\t\thas_participant_group_parameter = dynastic_cycle_vassal_internal_wars_allowed\n',
     '\t\t\t\t\thas_participant_group_parameter = dynastic_cycle_vassal_internal_wars_allowed'
     f' root = {{ OR = {{ highest_held_title_tier < tier_duchy NOT = {{ top_liege = {{ has_realm_law_flag = {PEACE_FLAG} }} }} has_usable_hook = liege }} }}'
     ' # Imperial Rasen: the Council Peace (great lords need a hook on their liege)\n', 2),
]


def law_groups():
    return '\n'.join([
        '# The hegemony\'s peace between its great lords. Only the top liege\'s law is read.',
        'rasen_peace_laws = {',
        '\trequired_government_flag = { government_is_celestial }',
        '\tdefault = rasen_council_peace_law',
        '\tcumulative = no',
        '\tflag = realm_law',
        '}',
    ])


def laws():
    return '\n'.join([
        'rasen_council_peace_law = {',
        '\tlaw_group_type = rasen_peace_laws',
        '\tindex = 0',
        f'\tflag = {PEACE_FLAG}',
        '\tcan_keep = { government_has_flag = government_is_celestial }',
        '\tpass_cost = { prestige = 100 }',
        '\tai_will_do = { value = 10 }',
        '}',
        '',
        'rasen_council_war_law = {',
        '\tlaw_group_type = rasen_peace_laws',
        '\tindex = 1',
        '\tcan_keep = { government_has_flag = government_is_celestial }',
        '\tcan_have = { exists = title:h_china.holder this = title:h_china.holder }',
        f'\tpass_cost = {{ prestige = {LIFT_PRESTIGE} }}',
        '\tai_will_do = { value = 0 }',
        '}',
    ])


def localization():
    return '\n'.join([
        'l_english:',
        ' rasen_peace_laws:0 "The Council Peace"',
        ' rasen_council_peace_law:0 "Council Peace"',
        ' rasen_council_peace_law_effects:0 "A duke or greater lord needs a [hook|E] on their [liege|E] to declare war on another duke or greater lord. Counts may feud freely. Azuma Honsha cannot be attacked except by open rebellion."',
        ' rasen_council_peace_law_desc:0 "The Exalted Council keeps a shaky peace among the great lords of Imperial Rasen. Petty counts may feud as they please, but no great lord marches on another without leave."',
        ' rasen_council_war_law:0 "Peace Lifted"',
        ' rasen_council_war_law_effects:0 "Great lords may make war on each other as feudal lords do. Azuma Honsha still cannot be attacked except by open rebellion."',
        ' rasen_council_war_law_desc:0 "The Council has lifted its peace, and the great lords of Rasen may settle their quarrels by the sword."',
        ' rasen_azuma_protected_tt:0 "Azuma Honsha falls only to open rebellion"',
    ])


def render():
    texts = {
        'common/law_groups/rasen_peace_law_groups.txt': law_groups(),
        'common/laws/rasen_peace_laws.txt': laws(),
        'localization/english/rasen_peace_l_english.yml': localization(),
    }
    return {k: (BOM + v.rstrip('\n') + '\n').encode('utf-8') for k, v in texts.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = [r for r, d in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale generated files: ' + ', '.join(stale))
    else:
        for relative, data in files.items():
            path = OUT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'Council Peace: {len(files)} files.')


if __name__ == '__main__':
    main()
