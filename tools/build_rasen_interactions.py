"""Generate Imperial Rasen's governing interactions for AuraClash/.

- Nominate the land's next Exalt: each land's ruler (the Shogun, the High Saint, the Grand Archivist, the
  Clan Lord, or for the Wild Lands any Mao) may name an unlanded cultivator of their land to take its
  Council seat when it next falls vacant. The nominee is kept in global_var:rasen_exalt_designate_<land>,
  which rasen_exalt_succession_effect (build_rasen_council.py) prefers over the strongest cultivator.
- Raise an Archon: an Exalt or the hegemon raises a cultivator of at least 8,000 Aura Pressure to the
  Archonate, the Council's enforcers (author's lore: Archons range from 8,000 to about 19,000 AP). At most
  twelve live at once. Each year the hegemon fills one empty place with the strongest candidate.
- Appoint a Magistrate: Outer Province Magistrates come from the Inner Kingdoms (Azuma's nobles would not go
  out there). The hegemon grants an Outer county it holds directly to a noble living in the Inner Kingdoms;
  each year an AI hegemon does so for one such county.
- Convene the Exalted Council: the hegemon may call the Council's session early, once every three years.

Writes (into AuraClash/):
  common/character_interactions/rasen_governing_interactions.txt
  common/decisions/rasen_governing_decisions.txt
  common/traits/rasen_archon_traits.txt
  common/scripted_triggers/rasen_governing_triggers.txt
  common/scripted_effects/rasen_governing_effects.txt
  common/on_action/rasen_governing_on_actions.txt
  localization/english/rasen_governing_l_english.yml

Usage: python tools/build_rasen_interactions.py [--check]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
BOM = '﻿'
LANDS = ['bladed', 'sacred', 'mystic', 'cursed', 'wild']
LAND_NAMES = {'bladed': 'Bladed', 'sacred': 'Sacred', 'mystic': 'Mystic', 'cursed': 'Cursed', 'wild': 'Wild'}
ARCHON_MIN_AP = 8000
ARCHON_LIMIT = 12
COUNCIL_COOLDOWN_YEARS = 3


def land_ruler(land):
    """Character trigger: rules the land (the Wild Lands have no ruler, only Maos)."""
    if land == 'wild':
        return ('highest_held_title_tier >= tier_duchy has_government = tribal_government '
                'capital_province ?= { geographical_region = world_rasen_wild }')
    return f'has_title = title:k_{land}'


def triggers():
    out = ['# Character scope: may be raised to the Archonate.',
           'rasen_archon_candidate_trigger = {',
           '\tis_alive = yes', '\tis_adult = yes', '\tis_imprisoned = no', '\tis_ruler = no',
           '\thas_trait = ac_cultivator',
           f'\tac_aura_pressure_value >= {ARCHON_MIN_AP}',
           '\tNOT = { has_trait = rasen_archon }',
           '\tNOT = { rasen_is_exalt_trigger = yes }',
           '}',
           '# Global scope: the Archonate has room for another Archon.',
           'rasen_archonate_has_room_trigger = {',
           f'\tNOT = {{ any_living_character = {{ has_trait = rasen_archon count >= {ARCHON_LIMIT} }} }}',
           '}',
           '# Character scope: a noble of the Inner Kingdoms who could serve as an Outer Magistrate.',
           'rasen_magistrate_candidate_trigger = {',
           '\tis_alive = yes', '\tis_adult = yes', '\tis_imprisoned = no', '\tis_ruler = no',
           '\texists = dynasty',
           '\tNOT = { rasen_is_exalt_trigger = yes }',
           '\tNOT = { has_trait = rasen_archon }',
           '\tlocation ?= { geographical_region = world_rasen_inner }',
           '}',
           '# Character scope: holds an Outer county directly.',
           'rasen_holds_outer_county_trigger = {',
           '\tany_held_title = { tier = tier_county title_province = { geographical_region = world_rasen_outer } }',
           '}']
    for land in LANDS:
        out += [f'# Character scope: rules the {LAND_NAMES[land]} Lands.', f'rasen_rules_{land}_trigger = {{ {land_ruler(land)} }}']
    return '\n'.join(out)


def effects():
    return '\n'.join([
        '# Character scope: join the Archonate and serve at the hegemon\'s court.',
        'rasen_raise_archon_effect = {',
        '\tadd_trait = rasen_archon',
        '\tif = {',
        '\t\tlimit = { exists = title:h_china.holder NOT = { liege_or_court_owner ?= title:h_china.holder } }',
        '\t\ttitle:h_china.holder = { add_courtier = prev }',
        '\t}',
        '}',
        '',
        '# Character scope (the hegemon), with scope:rasen_magistrate: grant them an Outer county from the domain.',
        'rasen_appoint_magistrate_effect = {',
        '\tordered_held_title = {',
        '\t\tlimit = { tier = tier_county title_province = { geographical_region = world_rasen_outer } }',
        '\t\torder_by = development_level',
        '\t\tsave_scope_as = rasen_magistrate_county',
        '\t}',
        '\tif = {',
        '\t\tlimit = { exists = scope:rasen_magistrate_county }',
        '\t\tcreate_title_and_vassal_change = { type = granted save_scope_as = rasen_magistrate_change add_claim_on_loss = no }',
        '\t\tscope:rasen_magistrate_county = { change_title_holder = { holder = scope:rasen_magistrate change = scope:rasen_magistrate_change } }',
        '\t\tresolve_title_and_vassal_change = scope:rasen_magistrate_change',
        '\t\tscope:rasen_magistrate = { if = { limit = { is_ruler = yes NOT = { has_government = celestial_government } } change_government = celestial_government } }',
        '\t}',
        '}',
        '',
        '# Global scope, yearly. The hegemon fills an empty place in the Archonate, and an AI hegemon sends an',
        '# Inner Kingdom noble to govern an Outer county it holds directly.',
        'rasen_governing_yearly_effect = {',
        '\tif = {',
        '\t\tlimit = { rasen_archonate_has_room_trigger = yes exists = title:h_china.holder }',
        '\t\tordered_living_character = {',
        '\t\t\tlimit = { rasen_archon_candidate_trigger = yes }',
        '\t\t\torder_by = ac_aura_pressure_value',
        '\t\t\trasen_raise_archon_effect = yes',
        '\t\t}',
        '\t}',
        '\ttitle:h_china.holder ?= {',
        '\t\tif = {',
        '\t\t\tlimit = { is_ai = yes rasen_holds_outer_county_trigger = yes }',
        '\t\t\tordered_living_character = {',
        '\t\t\t\tlimit = { rasen_magistrate_candidate_trigger = yes }',
        '\t\t\t\torder_by = stewardship',
        '\t\t\t\tsave_scope_as = rasen_magistrate',
        '\t\t\t}',
        '\t\t\tif = { limit = { exists = scope:rasen_magistrate } rasen_appoint_magistrate_effect = yes }',
        '\t\t}',
        '\t}',
        '}',
    ])


def on_actions():
    return '\n'.join([
        '# Imperial Rasen\'s governing. Lists append to vanilla and base-mod hooks.',
        'yearly_global_pulse = { on_actions = { rasen_governing_yearly } }',
        'rasen_governing_yearly = { effect = { rasen_governing_yearly_effect = yes } }',
    ])


def interactions():
    out = []
    for land in LANDS:
        out += [f'# The ruler of the {LAND_NAMES[land]} Lands names who will take its Council seat when it next falls vacant.',
                f'rasen_nominate_{land}_exalt_interaction = {{',
                '\tcategory = interaction_category_diplomacy', '\tcommon_interaction = no', '\ticon = support_candidacy',
                f'\tdesc = rasen_nominate_exalt_interaction_desc', '\tauto_accept = yes',
                '\tis_shown = {',
                f'\t\tscope:actor = {{ rasen_rules_{land}_trigger = yes }}',
                f'\t\tscope:recipient = {{ rasen_exalt_candidate_trigger = {{ LAND = {land} }} }}',
                '\t}',
                '\tis_valid_showing_failures_only = {',
                # (Inside NOT the variable would be read even when unset, logging an error every frame.)
                f'\t\ttrigger_if = {{ limit = {{ has_global_variable = rasen_exalt_designate_{land} }} '
                f'NOT = {{ global_var:rasen_exalt_designate_{land} = scope:recipient }} }}',
                '\t}',
                '\tcost = { prestige = 100 }',
                '\ton_accept = {',
                f'\t\tset_global_variable = {{ name = rasen_exalt_designate_{land} value = scope:recipient }}',
                '\t\tscope:recipient = { add_opinion = { target = scope:actor modifier = grateful_opinion opinion = 30 } }',
                f'\t\tcustom_tooltip = rasen_nominate_exalt_tt',
                '\t}',
                '\tai_will_do = { base = 0 }',
                '}',
                '']
    out += ['# An Exalt or the hegemon raises a mighty cultivator to the Archonate, the Council\'s enforcers.',
            'rasen_raise_archon_interaction = {',
            '\tcategory = interaction_category_diplomacy', '\tcommon_interaction = no', '\ticon = icon_combat',
            '\tdesc = rasen_raise_archon_interaction_desc', '\tauto_accept = yes',
            '\tis_shown = {',
            '\t\tscope:actor = { OR = { rasen_is_exalt_trigger = yes this = title:h_china.holder } }',
            '\t\tscope:recipient = { has_trait = ac_cultivator NOT = { has_trait = rasen_archon } NOT = { rasen_is_exalt_trigger = yes } }',
            '\t}',
            '\tis_valid_showing_failures_only = {',
            '\t\tscope:recipient = { rasen_archon_candidate_trigger = yes }',
            '\t\tcustom_tooltip = { text = rasen_archonate_full_tt rasen_archonate_has_room_trigger = yes }',
            '\t}',
            '\tcost = { prestige = 200 }',
            '\ton_accept = { scope:recipient = { rasen_raise_archon_effect = yes } }',
            '\tai_will_do = { base = 0 }',
            '}',
            '',
            '# The hegemon sends an Inner Kingdom noble to govern an Outer county it holds directly.',
            'rasen_appoint_magistrate_interaction = {',
            '\tcategory = interaction_category_vassal', '\tcommon_interaction = no', '\ticon = grant_governorship',
            '\tdesc = rasen_appoint_magistrate_interaction_desc', '\tauto_accept = yes',
            '\tis_shown = {',
            '\t\tscope:actor = { this = title:h_china.holder }',
            '\t\tscope:recipient = { rasen_magistrate_candidate_trigger = yes }',
            '\t}',
            '\tis_valid_showing_failures_only = {',
            '\t\tscope:actor = { custom_tooltip = { text = rasen_no_outer_county_tt rasen_holds_outer_county_trigger = yes } }',
            '\t}',
            '\ton_accept = {',
            '\t\tscope:recipient = { save_scope_as = rasen_magistrate }',
            '\t\tscope:actor = { rasen_appoint_magistrate_effect = yes }',
            '\t}',
            '\tai_will_do = { base = 0 }',
            '}']
    return '\n'.join(out)


def decisions():
    return '\n'.join([
        '# The hegemon rules Azuma Honsha with the Exalted Council and may call its session early.',
        'rasen_convene_council_decision = {',
        '\tpicture = { reference = "gfx/interface/illustrations/decisions/decision_realm.dds" }',
        '\tdecision_group_type = major',
        '\tdesc = rasen_convene_council_decision_desc',
        '\tselection_tooltip = rasen_convene_council_decision_tooltip',
        '\tconfirm_text = rasen_convene_council_decision_confirm',
        '\tis_shown = { exists = title:h_china.holder this = title:h_china.holder }',
        '\tis_valid_showing_failures_only = { is_available_adult = yes }',
        f'\tcooldown = {{ years = {COUNCIL_COOLDOWN_YEARS} }}',
        '\tcost = { prestige = 200 }',
        '\teffect = {',
        '\t\tcustom_tooltip = rasen_convene_council_decision_effect_tt',
        f'\t\tset_global_variable = {{ name = rasen_council_countdown value = {COUNCIL_COOLDOWN_YEARS} }}',
        '\t\trasen_council_session_effect = yes',
        '\t}',
        '\tai_check_interval = 0',
        '\tai_will_do = { base = 0 }',
        '}',
    ])


def traits():
    return '\n'.join([
        '# The Archonate: once the royal family\'s police, now the enforcers of the Exalted Council.',
        'rasen_archon = {',
        '\ticon = ac_immortal_core.dds',
        '\tshown_in_ruler_designer = no',
        '\tprowess = 6',
        '\tmonthly_prestige = 2',
        '\tgeneral_opinion = 10',
        '\tdread_baseline_add = 10',
        '}',
    ])


def localization():
    out = ['l_english:',
           ' rasen_nominate_exalt_interaction_desc:0 "Name [recipient.GetShortUIName] to take your land\'s seat on the Exalted Council when it next falls vacant."',
           ' rasen_nominate_exalt_tt:0 "When the seat next falls vacant, they take it in place of the strongest cultivator of the land, if they still qualify."',
           ' rasen_raise_archon_interaction:0 "Raise to the Archonate"',
           ' rasen_raise_archon_interaction_desc:0 "Make [recipient.GetShortUIName] an Archon, an enforcer of the Exalted Council\'s will. Archons serve at the hegemon\'s court."',
           f' rasen_archonate_full_tt:0 "The Archonate has no empty place (at most {ARCHON_LIMIT} Archons)"',
           ' rasen_appoint_magistrate_interaction:0 "Appoint as Magistrate"',
           ' rasen_appoint_magistrate_interaction_desc:0 "Send [recipient.GetShortUIName] out from the Inner Kingdoms to govern an Outer county you hold directly, as a Magistrate of the Council."',
           ' rasen_no_outer_county_tt:0 "You must hold an Outer county directly"',
           ' rasen_convene_council_decision:0 "Convene the Exalted Council"',
           ' rasen_convene_council_decision_desc:0 "Azuma Honsha is ruled with the Exalted Council. I may summon the Exalts to sit now rather than wait for the appointed session."',
           ' rasen_convene_council_decision_tooltip:0 "The Exalts vote on a decree now"',
           ' rasen_convene_council_decision_confirm:0 "Summon the Exalts"',
           ' rasen_convene_council_decision_effect_tt:0 "The Exalted Council sits now; the next regular session is three years away."',
           ' trait_rasen_archon:0 "Archon"',
           f' trait_rasen_archon_desc:0 "An Archon of the Exalted Council. Archons were created as the royal family\'s police; they now enforce the Council\'s will, and stand between {ARCHON_MIN_AP:,} and about 19,000 Aura Pressure."',
           ' trait_rasen_archon_character_desc:0 "[ROOT.Char.GetFirstName] is an Archon of the Exalted Council."']
    for land in LANDS:
        out.append(f' rasen_nominate_{land}_exalt_interaction:0 "Nominate as {LAND_NAMES[land]} Exalt"')
    return '\n'.join(out)


def render():
    texts = {
        'common/character_interactions/rasen_governing_interactions.txt': interactions(),
        'common/decisions/rasen_governing_decisions.txt': decisions(),
        'common/traits/rasen_archon_traits.txt': traits(),
        'common/scripted_triggers/rasen_governing_triggers.txt': triggers(),
        'common/scripted_effects/rasen_governing_effects.txt': effects(),
        'common/on_action/rasen_governing_on_actions.txt': on_actions(),
        'localization/english/rasen_governing_l_english.yml': localization(),
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
    print(f'Governing: {len(files)} files, {len(LANDS)} nominations.')


if __name__ == '__main__':
    main()
