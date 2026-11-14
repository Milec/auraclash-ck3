"""Generate the Akuma Lords and Ryugujo (from the IF's chapter 9) for AuraClash/.

The Akuma Lords:
- a cult of three Lords on azure crystal thrones, with Taio and his Clones as their hand;
- they draw power from blood (crimson chi, blood marbles) and plot to "end this
  stagnant Empire and bring about a new age";
- they mind-control future Archons, and one of Ryugujo's Dragon Princes works with them.

Ryugujo: draconic underwater dome-city-states to the southeast, ruled from Dragon Prince
seats, with spies inside the Archonate.

In CK3: cult membership is a secret (rasen_secret_akuma), criminal to all outsiders.
Members gain Blood Chi (prowess for health). The Lords recruit AI cultivators each year
and tempt players. When the cult is large it strikes an Outer province, and Exalts may
dispatch Archons to expose a member. Players in the Archonate or on the Council may
uncover a Ryugujo spy, and through them the Dragon Prince's pact with the cult.

Usage: python tools/build_rasen_shadows.py [--check]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
BOM = '﻿'

STRIKE_MEMBERS = 12      # living members before the cult strikes
STRIKE_COOLDOWN = 5      # years between strikes
RECRUIT_CHANCE = 40      # per Lord per year
TEMPT_CHANCE = 6         # per eligible player per year
SPY_CHANCE = 5           # per eligible player per year


def traits():
    return '\n'.join([
        '# Chapter 9 of the IF. Icons reuse the base mod\'s cultivation art.',
        'rasen_akuma_lord = {', '\ticon = ac_immortal_core.dds', '\tshown_in_ruler_designer = no',
        '\tintrigue = 4', '\tprowess = 4', '\tdread_baseline_add = 20', '}', '',
        'rasen_akuma_acolyte = {', '\ticon = ac_immortal_core.dds', '\tshown_in_ruler_designer = no',
        '\tintrigue = 2', '\tprowess = 3', '}', '',
        '# Draconic kin of Ryugujo, such as its Dragon Princes.',
        'rasen_dragon_blood = {', '\ticon = ac_immortal_core.dds', '\tshown_in_ruler_designer = no',
        '\tprowess = 6', '\thealth = 1', '\tlife_expectancy = 60', '\tmonthly_prestige = 0.5', '}',
    ])


def secrets():
    return '\n'.join([
        'rasen_secret_akuma = {',
        '\tcategory = religious',
        '\tis_valid = { scope:secret_owner = { has_variable = rasen_akuma_member } }',
        '\tis_shunned = { scope:target = { NOT = { has_variable = rasen_akuma_member } } }',
        '\tis_criminal = { scope:target = { NOT = { has_variable = rasen_akuma_member } } }',
        '\ton_expose = {',
        '\t\tsecret_exposed_notification_effect = yes',
        '\t\tscope:secret_owner = { add_prestige = -200 }',
        '\t}',
        '}',
    ])


def modifiers():
    return '\n'.join([
        '# "A cult that uses people\'s blood for power and might turn into Fiends."',
        'rasen_blood_chi_modifier = {', '\ticon = health_negative', '\tprowess = 3', '\thealth = -0.5', '\tstress_gain_mult = 0.1', '}', '',
        'rasen_akuma_terror_modifier = {', '\ticon = county_modifier_development_negative',
        '\tcounty_opinion_add = -15', '\tdevelopment_growth_factor = -0.2', '\tmonthly_county_control_growth_add = -0.5', '}',
    ])


def on_actions():
    return '\n'.join([
        '# The Akuma Lords and Ryugujo. Lists append to vanilla and base-mod hooks.',
        'yearly_global_pulse = { on_actions = { rasen_shadows_yearly } }',
        'rasen_shadows_yearly = { effect = { rasen_shadows_yearly_effect = yes } }',
    ])


def effects():
    return '\n'.join([
        '# Character scope.',
        'rasen_join_akuma_effect = {',
        '\tif = {',
        '\t\tlimit = { NOT = { has_variable = rasen_akuma_member } }',
        '\t\tset_variable = rasen_akuma_member',
        '\t\tadd_secret = { type = rasen_secret_akuma }',
        '\t\tadd_character_modifier = rasen_blood_chi_modifier',
        '\t\tadd_to_global_variable_list = { name = rasen_akuma_members target = this }',
        '\t}',
        '}',
        '',
        '# Character scope: leave the cult (the secret becomes invalid and disappears).',
        'rasen_leave_akuma_effect = {',
        '\tremove_variable = rasen_akuma_member',
        '\tremove_character_modifier = rasen_blood_chi_modifier',
        '\tif = {',
        '\t\tlimit = { is_target_in_global_variable_list = { name = rasen_akuma_members target = this } }',
        '\t\tremove_list_global_variable = { name = rasen_akuma_members target = this }',
        '\t}',
        '}',
        '',
        '# Global scope, yearly.',
        'rasen_shadows_yearly_effect = {',
        '\t# Each living Lord may draw an ambitious or broken cultivator into the cult.',
        '\tevery_in_global_list = {',
        '\t\tvariable = rasen_akuma_members',
        '\t\tlimit = { is_alive = yes has_trait = rasen_akuma_lord }',
        '\t\trandom = {',
        f'\t\t\tchance = {RECRUIT_CHANCE}',
        '\t\t\trandom_living_character = {',
        '\t\t\t\tlimit = {',
        '\t\t\t\t\tis_ai = yes', '\t\t\t\t\tage >= 16', '\t\t\t\t\thas_trait = ac_cultivator',
        '\t\t\t\t\tNOT = { has_variable = rasen_akuma_member }', '\t\t\t\t\tNOT = { rasen_is_exalt_trigger = yes }',
        '\t\t\t\t\tOR = { has_trait = ambitious has_trait = callous has_trait = arbitrary stress >= 100 }',
        '\t\t\t\t}',
        '\t\t\t\trasen_join_akuma_effect = yes',
        '\t\t\t}',
        '\t\t}',
        '\t}',
        '\t# Players are tempted by a Clone of Taio.',
        '\tevery_player = {',
        '\t\tlimit = { age >= 16 has_trait = ac_cultivator NOT = { has_variable = rasen_akuma_member } }',
        f'\t\trandom = {{ chance = {TEMPT_CHANCE} trigger_event = {{ id = rasen_shadows.0001 days = {{ 30 300 }} }} }}',
        '\t}',
        '\t# The cult strikes once it is large enough.',
        '\tif = {',
        '\t\tlimit = {',
        '\t\t\tNOT = { has_global_variable = rasen_akuma_strike_cooldown }',
        f'\t\t\tany_in_global_list = {{ variable = rasen_akuma_members count >= {STRIKE_MEMBERS} is_alive = yes }}',
        '\t\t}',
        '\t\trasen_akuma_strike_effect = yes',
        '\t}',
        '\t# Ryugujo\'s spies in the Archonate.',
        '\tevery_player = {',
        '\t\tlimit = { OR = { has_trait = ac_archonate_disciple rasen_is_exalt_trigger = yes } }',
        f'\t\trandom = {{ chance = {SPY_CHANCE} trigger_event = {{ id = rasen_shadows.0020 days = {{ 30 300 }} }} }}',
        '\t}',
        '}',
        '',
        '# Global scope.',
        'rasen_akuma_strike_effect = {',
        f'\tset_global_variable = {{ name = rasen_akuma_strike_cooldown value = yes years = {STRIKE_COOLDOWN} }}',
        '\trandom_county_in_region = {',
        '\t\tregion = world_rasen_outer',
        '\t\tlimit = { NOT = { has_county_modifier = rasen_akuma_terror_modifier } }',
        '\t\tadd_county_modifier = { modifier = rasen_akuma_terror_modifier years = 5 }',
        '\t\tsave_scope_as = rasen_akuma_target',
        '\t}',
        '\tif = {',
        '\t\tlimit = { exists = scope:rasen_akuma_target }',
        '\t\tevery_player = {',
        '\t\t\tlimit = { NOT = { has_variable = rasen_akuma_member } }',
        '\t\t\ttrigger_event = rasen_shadows.0010',
        '\t\t}',
        '\t}',
        '}',
        '',
        '# Character scope (an Exalt): the Archons expose one living member of the cult.',
        'rasen_archons_hunt_akuma_effect = {',
        '\trandom_in_global_list = {',
        '\t\tvariable = rasen_akuma_members',
        '\t\tlimit = { is_alive = yes NOT = { has_trait = rasen_akuma_lord } any_secret = { secret_type = rasen_secret_akuma } }',
        '\t\trandom_secret = {',
        '\t\t\tlimit = { secret_type = rasen_secret_akuma }',
        '\t\t\texpose_secret = root',
        '\t\t}',
        '\t}',
        '}',
    ])


def events():
    return '\n'.join([
        'namespace = rasen_shadows',
        '',
        '# 0001 a Clone of Taio offers Blood Chi; 0010 the Akuma Lords strike; 0020 a Ryugujo spy.',
        '',
        'rasen_shadows.0001 = {',
        '\ttype = character_event',
        '\ttitle = rasen_shadows.0001.t',
        '\tdesc = rasen_shadows.0001.desc',
        '\ttheme = intrigue',
        '\ttrigger = { NOT = { has_variable = rasen_akuma_member } }',
        '\tleft_portrait = { character = root animation = worry }',
        '\toption = {',
        '\t\tname = rasen_shadows.0001.accept',
        '\t\trasen_join_akuma_effect = yes',
        '\t\tai_chance = { base = 0 }',
        '\t}',
        '\toption = {',
        '\t\tname = rasen_shadows.0001.refuse',
        '\t\tadd_prestige = 50',
        '\t}',
        '\toption = {',
        '\t\tname = rasen_shadows.0001.report',
        '\t\ttrigger = { has_trait = ac_archonate_disciple }',
        '\t\tadd_prestige = 150',
        '\t\tac_favor_change_effect = { LAND = bladed AMOUNT = 1 }',
        '\t}',
        '}',
        '',
        'rasen_shadows.0010 = {',
        '\ttype = character_event',
        '\ttitle = rasen_shadows.0010.t',
        '\tdesc = rasen_shadows.0010.desc',
        '\ttheme = war',
        '\tleft_portrait = { character = root animation = shock }',
        '\toption = {',
        '\t\tname = rasen_shadows.0010.archons',
        '\t\ttrigger = { rasen_is_exalt_trigger = yes gold >= 100 }',
        '\t\tremove_short_term_gold = 100',
        '\t\tscope:rasen_akuma_target ?= { add_county_modifier = { modifier = rasen_archon_patrols_modifier years = 3 } }',
        '\t\trasen_archons_hunt_akuma_effect = yes',
        '\t}',
        '\toption = {',
        '\t\tname = rasen_shadows.0010.ok',
        '\t}',
        '}',
        '',
        'rasen_shadows.0020 = {',
        '\ttype = character_event',
        '\ttitle = rasen_shadows.0020.t',
        '\tdesc = rasen_shadows.0020.desc',
        '\ttheme = intrigue',
        '\timmediate = {',
        '\t\tcreate_character = {',
        '\t\t\tage = { 18 30 }', '\t\t\tgender_female_chance = 50', '\t\t\tculture = culture:ryugujin',
        '\t\t\tfaith = root.faith', '\t\t\tlocation = root.location', '\t\t\ttrait = ac_cultivator',
        '\t\t\tsave_scope_as = rasen_ryugujo_spy',
        '\t\t}',
        '\t}',
        '\tleft_portrait = { character = root animation = personality_rational }',
        '\tright_portrait = { character = scope:rasen_ryugujo_spy animation = worry }',
        '\toption = {',
        '\t\tname = rasen_shadows.0020.expose',
        '\t\tadd_prestige = 100',
        '\t\t# "Was Tenkairyu your only connection to Ryugujo?" The spy names the Dragon Prince.',
        '\t\trandom_in_global_list = {',
        '\t\t\tvariable = rasen_akuma_members',
        '\t\t\tlimit = { is_alive = yes has_trait = rasen_dragon_blood }',
        '\t\t\trandom_secret = { limit = { secret_type = rasen_secret_akuma } reveal_to = root }',
        '\t\t}',
        '\t\tscope:rasen_ryugujo_spy = { death = { death_reason = death_execution killer = root } }',
        '\t}',
        '\toption = {',
        '\t\tname = rasen_shadows.0020.turn',
        '\t\tadd_gold = 100',
        '\t\tadd_hook = { type = favor_hook target = scope:rasen_ryugujo_spy }',
        '\t\tadd_courtier = scope:rasen_ryugujo_spy',
        '\t}',
        '\toption = {',
        '\t\tname = rasen_shadows.0020.release',
        '\t\tadd_piety = 50',
        '\t\tscope:rasen_ryugujo_spy = { death = { death_reason = death_vanished } }',
        '\t}',
        '}',
    ])


def localization():
    return '\n'.join([
        'l_english:',
        ' trait_rasen_akuma_lord:0 "Akuma Lord"',
        ' trait_rasen_akuma_lord_desc:0 "This character sits on an azure crystal throne among the Akuma Lords, who seek to end the stagnant Empire and bring about a new age."',
        ' trait_rasen_akuma_acolyte:0 "Hand of the Akuma Lords"',
        ' trait_rasen_akuma_acolyte_desc:0 "This character serves the Akuma Lords, and their crimson chi feels sickening to any spiritual sense."',
        ' trait_rasen_dragon_blood:0 "Dragon Blood"',
        ' trait_rasen_dragon_blood_desc:0 "This character is draconic kin of Ryugujo, the underwater nation of Dragon Princes far to the southeast."',
        ' rasen_secret_akuma:0 "Akuma Cultist"',
        ' rasen_secret_akuma_desc:0 "Serves the Akuma Lords"',
        ' rasen_secret_akuma_tooltip_desc:0 "This character draws power from blood in service of the Akuma Lords."',
        ' rasen_secret_akuma_type_desc:0 "$rasen_secret_akuma_tooltip_desc$"',
        ' rasen_blood_chi_modifier:0 "Blood Chi"',
        ' rasen_blood_chi_modifier_desc:0 "Crimson chi drawn from blood: power at the cost of the body."',
        ' rasen_akuma_terror_modifier:0 "Akuma Terror"',
        ' rasen_akuma_terror_modifier_desc:0 "Acolytes of the Akuma Lords have struck here, and the people live in fear."',
        ' rasen_shadows.0001.t:0 "A Familiar Stranger"',
        ' rasen_shadows.0001.desc:0 "He calls himself Taio, though the crimson chi swirling about his fist feels sickening, and I suspect he is only a Clone of someone far stronger. He offers me a blood marble and a place among those who serve the Akuma Lords. \\"This Empire is stagnant,\\" he says. \\"We will bring about a new age.\\""',
        ' rasen_shadows.0001.accept:0 "Power is power. I accept."',
        ' rasen_shadows.0001.refuse:0 "Begone, and take your blood with you."',
        ' rasen_shadows.0001.report:0 "Report him to the Archons."',
        ' rasen_shadows.0010.t:0 "The Akuma Lords Strike"',
        ' rasen_shadows.0010.desc:0 "Acolytes of the Akuma Lords have struck in [rasen_akuma_target.GetName], leaving the county in terror. Whatever the cult wants, they no longer bother to hide it."',
        ' rasen_shadows.0010.archons:0 "Dispatch Archons to hunt the cult."',
        ' rasen_shadows.0010.ok:0 "The Council will have to answer for this."',
        ' rasen_shadows.0020.t:0 "A Spy for Ryugujo"',
        ' rasen_shadows.0020.desc:0 "[rasen_ryugujo_spy.GetFirstName] has been passing secrets of the Archonate to the dragon city-states of Ryugujo. Under questioning, [rasen_ryugujo_spy.GetSheHe] swears [rasen_ryugujo_spy.GetSheHe] spied only to help the dragons, never to leak their secrets to anyone else."',
        ' rasen_shadows.0020.expose:0 "Expose the spy, and whoever [rasen_ryugujo_spy.GetSheHe] really serves."',
        ' rasen_shadows.0020.turn:0 "Spy for me instead."',
        ' rasen_shadows.0020.release:0 "Send [rasen_ryugujo_spy.GetHerHim] back to the sea."',
    ])


def render():
    texts = {
        'common/traits/rasen_shadow_traits.txt': traits(),
        'common/secret_types/rasen_secret_types.txt': secrets(),
        'common/modifiers/rasen_shadow_modifiers.txt': modifiers(),
        'common/on_action/rasen_shadow_on_actions.txt': on_actions(),
        'common/scripted_effects/rasen_shadow_effects.txt': effects(),
        'events/rasen_shadow_events.txt': events(),
        'localization/english/rasen_shadows_l_english.yml': localization(),
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
    print(f'Akuma Lords and Ryugujo: {len(files)} files.')


if __name__ == '__main__':
    main()
