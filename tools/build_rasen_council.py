"""Generate the Exalted Council of Imperial Rasen for AuraClash/.

In the IF, the five Inner Kingdoms "maintain shaky peace through a seat on the
Exalted Council that rules from the capital". Chapter 9 adds:
- inter-council conflicts are common;
- Exalts sponsor and send gifts to their favourites in the Heavenly Ascension Trials;
- one Exalt will counter another's interference through a proxy (the Bladed Exalt
  against the Wild Exalt).

Exalts hold no land. Each is chosen from their Inner Kingdom for a hundred-year term
(or until death): the strongest unlanded cultivator living there takes the seat,
moves to the High Steward's court and founds a Celestial noble family with an
estate on Azuma Honsha. The seat is the global variable rasen_exalt_<land>.

Every three years each Exalt votes for a decree. AI
Exalts back their own land's decree, lean towards Exalts they like and never back
a rival. Players vote, and may lobby with prestige for a second vote. The decree is
drawn in proportion to the votes. Exalts outvoted on their own decree resent the
winner.

When the Trials open, one Exalt sponsors the year's favourite and a rival Exalt
offers each player entrant patronage to counter it.

Writes (into AuraClash/):
  common/on_action/rasen_council_on_actions.txt
  common/scripted_effects/rasen_council_effects.txt
  common/scripted_triggers/rasen_council_triggers.txt
  common/modifiers/rasen_council_modifiers.txt
  common/opinion_modifiers/rasen_council_opinions.txt
  events/rasen_council_events.txt
  localization/english/rasen_council_l_english.yml

Usage: python tools/build_rasen_council.py [--check]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
BOM = '﻿'

# land, decree key, decree name, what it does (tooltip), the land's value in the IF
LANDS = [
    ('bladed', 'archons', 'Dispatch the Archons',
     'Archon patrols keep order in the Outer provinces for three years, and any Ice Incursion ends a year sooner.',
     'honour'),
    ('sacred', 'fiends', 'Purge the Fiends',
     'Every county resists disease for three years, and Devanic rulers gain #V 100#! piety.',
     'compassion'),
    ('mystic', 'archives', 'Open the Imperial Archives',
     'Lost knowledge from the Archonate archives is lent to the worthy: Path Manuals cost half as much for three years.',
     'knowledge'),
    ('cursed', 'levy', 'Levy the Outer Provinces',
     'Each Exalt receives #V 150#! gold, and the Outer provinces pay heavier taxes for three years.',
     'practicality'),
    ('wild', 'trials', 'Call the Trials',
     'Strength must be found and claimed: the Heavenly Ascension Trials are called for next year.',
     'strength'),
]
KEYS = [land for land, *_ in LANDS]
SESSION_YEARS = 3
LOBBY_PRESTIGE = 150


EXALT_TERM_YEARS = 100
# The dynastic cycle's movements are the Council's factions, each led by the Exalt whose land shares its
# aims. Exalts are landless, so they are not the cycle's own participants: their leadership is set on the
# movement directly. The Cursed Exalt rules from the shadows and leads none.
MOVEMENTS = {'bladed': 'pro_hegemon', 'mystic': 'advancement', 'wild': 'expansion', 'sacred': 'conservative'}


def holder(land):
    return f'global_var:rasen_exalt_{land}'


def filled(land):
    """Trigger: the land's seat has a living Exalt."""
    return f'rasen_seat_filled_trigger = {{ LAND = {land} }}'


def at_seat(land, effect):
    """Run an effect on the land's Exalt, if the seat is filled."""
    return f'if = {{ limit = {{ {filled(land)} }} {holder(land)} = {{ {effect} }} }}'


def on_actions():
    return '\n'.join([
        '# The Exalted Council of Imperial Rasen. Lists append to vanilla and base-mod hooks.',
        'yearly_global_pulse = { on_actions = { rasen_council_yearly } }',
        'rasen_council_yearly = { effect = { rasen_exalt_succession_effect = yes rasen_exalt_movements_effect = yes rasen_council_yearly_effect = yes } }',
        '# Once the Exalts are seated at the start, they take up their movements.',
        'on_game_start_after_lobby = { on_actions = { rasen_exalt_movements_start } }',
        'rasen_exalt_movements_start = { effect = { title:h_china.holder ?= { trigger_event = { on_action = rasen_exalt_movements_delayed days = 2 } } } }',
        'rasen_exalt_movements_delayed = { effect = { rasen_exalt_movements_effect = yes } }',
    ])


def triggers():
    return '\n'.join([
        '# Character scope: holds a seat on the Exalted Council.',
        'rasen_is_exalt_trigger = { has_variable = rasen_exalt_seat }',
        '# Character scope: holds the seat of the given land.',
        'rasen_holds_seat_trigger = { has_variable = rasen_exalt_seat var:rasen_exalt_seat = flag:$LAND$ }',
        '# Global scope: the land\'s seat has a living Exalt.',
        'rasen_seat_filled_trigger = { has_global_variable = rasen_exalt_$LAND$ global_var:rasen_exalt_$LAND$ = { is_alive = yes } }',
        '# Character scope: may be chosen as the land\'s Exalt. Exalts give up their lands, so only the unlanded are chosen.',
        'rasen_exalt_candidate_trigger = {',
        '\tis_alive = yes', '\tis_adult = yes', '\thas_trait = ac_cultivator', '\tis_ruler = no',
        '\tNOT = { has_variable = rasen_exalt_seat }',
        '\tlocation ?= { geographical_region = world_rasen_$LAND$ }',
        '}',
    ])


def anchor(effect):
    """Run a delayed global event on the High Steward, or failing that any Exalt."""
    lines = [f'	if = {{ limit = {{ exists = title:k_azuma.holder }} title:k_azuma.holder = {{ {effect} }} }}']
    lines += [f'	else_if = {{ limit = {{ {filled(land)} }} {holder(land)} = {{ {effect} }} }}' for land in KEYS]
    return lines


def ai_vote(land):
    """The AI Exalt of `land` votes: own decree first, then friends; never a rival."""
    lines = [f'\tif = {{ limit = {{ {filled(land)} }} {holder(land)} = {{', '\t\tif = {', f'\t\t\tlimit = {{ is_ai = no }}',
             '\t\t\ttrigger_event = rasen_council.0001', '\t\t}', '\t\telse = {', '\t\t\trandom_list = {',
             f'\t\t\t\t60 = {{ change_global_variable = {{ name = rasen_votes_{land} add = 1 }} }}']
    for other in KEYS:
        if other == land:
            continue
        lines += [f'\t\t\t\t6 = {{',
                  f'\t\t\t\t\tmodifier = {{ factor = 3 {filled(other)} opinion = {{ target = {holder(other)} value >= 25 }} }}',
                  f'\t\t\t\t\tmodifier = {{ factor = 0 {filled(other)} has_relation_rival = {holder(other)} }}',
                  f'\t\t\t\t\tmodifier = {{ factor = 0 NOT = {{ {filled(other)} }} }}',
                  f'\t\t\t\t\tchange_global_variable = {{ name = rasen_votes_{other} add = 1 }}',
                  '\t\t\t\t}']
    return lines + ['\t\t\t}', '\t\t}', '\t} }']


def effects():
    out = [
        '# "All five maintain shaky peace through a seat on the Exalted Council that rules from the capital."',
        '# Global scope, yearly.',
        'rasen_council_yearly_effect = {',
        '\tif = {',
        '\t\tlimit = { NOT = { has_global_variable = rasen_council_countdown } }',
        f'\t\tset_global_variable = {{ name = rasen_council_countdown value = {SESSION_YEARS - 1} }}',
        '\t}',
        '\tchange_global_variable = { name = rasen_council_countdown add = -1 }',
        '\tif = {',
        '\t\tlimit = { global_var:rasen_council_countdown <= 0 }',
        f'\t\tset_global_variable = {{ name = rasen_council_countdown value = {SESSION_YEARS} }}',
        '\t\trasen_council_session_effect = yes',
        '\t}',
        '\t# Patronage is checked after the Trials (base mod) have had their own yearly pulse.',
        *anchor('trigger_event = { id = rasen_council.0080 days = 45 }'),
        '}',
        '',
    ]
    out += ['# Global scope. Count the votes; player Exalts have 30 days to cast theirs.', 'rasen_council_session_effect = {']
    out += [f'\tset_global_variable = {{ name = rasen_votes_{land} value = 0 }}' for land in KEYS]
    for land in KEYS:
        out += ai_vote(land)
    out += [*anchor('trigger_event = { id = rasen_council.0090 days = 30 }'), '}', '',
            '# Global scope. Draw the decree in proportion to the votes and enact it.',
            'rasen_council_enact_effect = {', '\trandom_list = {']
    for land in KEYS:
        out += [f'\t\t0 = {{', f'\t\t\tmodifier = {{ add = global_var:rasen_votes_{land} }}',
                f'\t\t\tset_global_variable = {{ name = rasen_decree value = flag:{land} }}', '\t\t}']
    out += ['\t\t# Nobody voted: the Bladed Exalt\'s decree stands by default.',
            '\t\t1 = {', '\t\t\tmodifier = { factor = 0 OR = {', *[f'\t\t\t\tglobal_var:rasen_votes_{land} > 0' for land in KEYS],
            '\t\t\t} }', '\t\t\tset_global_variable = { name = rasen_decree value = flag:bladed }', '\t\t}', '\t}']
    for i, (land, decree, *_rest) in enumerate(LANDS):
        kw = 'if' if i == 0 else 'else_if'
        out += [f'\t{kw} = {{', f'\t\tlimit = {{ global_var:rasen_decree = flag:{land} }}', f'\t\trasen_decree_{decree}_effect = yes',
                f'\t\t{at_seat(land, "save_scope_as = rasen_council_winner")}', '\t}']
    out += ['\t# The winning Exalt gains standing. Exalts outvoted on their own decree resent the winner.',
            '\tscope:rasen_council_winner ?= { add_prestige = 100 }']
    for land in KEYS:
        out += ['\tif = {', f'\t\tlimit = {{ exists = scope:rasen_council_winner {filled(land)} NOT = {{ global_var:rasen_decree = flag:{land} }}',
                f'\t\t\tglobal_var:rasen_votes_{land} > 0 NOT = {{ {holder(land)} = scope:rasen_council_winner }} }}',
                f'\t\t{holder(land)} = {{ add_opinion = {{ target = scope:rasen_council_winner modifier = rasen_council_outvoted_opinion }} }}', '\t}']
    out += ['\tevery_player = { trigger_event = rasen_council.0002 }', '}', '',
            'rasen_decree_archons_effect = {',
            '\tevery_county_in_region = {', '\t\tregion = world_rasen_outer',
            '\t\tadd_county_modifier = { modifier = rasen_archon_patrols_modifier years = 3 }', '\t}',
            '\tif = {', '\t\tlimit = { has_global_variable = rasen_ice_incursion_active global_var:rasen_ice_remaining > 1 }',
            '\t\tchange_global_variable = { name = rasen_ice_remaining add = -1 }', '\t}', '}', '',
            'rasen_decree_fiends_effect = {',
            '\tevery_county_in_region = { region = world_rasen_inner add_county_modifier = { modifier = rasen_fiend_purge_modifier years = 3 } }',
            '\tevery_county_in_region = { region = world_rasen_outer add_county_modifier = { modifier = rasen_fiend_purge_modifier years = 3 } }',
            '\tevery_ruler = { limit = { faith = faith:devanic_temple } add_piety = 100 }', '}', '',
            '# Read by ac_path_manual_gold in the base mod.',
            'rasen_decree_archives_effect = {', '\tset_global_variable = { name = rasen_archives_open value = yes years = 3 }', '}', '',
            'rasen_decree_levy_effect = {',
            '\tevery_county_in_region = { region = world_rasen_outer add_county_modifier = { modifier = rasen_imperial_levy_modifier years = 3 } }',
            *[f'\t{at_seat(land, "add_gold = 150")}' for land in KEYS], '}', '',
            '# The Trials open on the next yearly pulse.',
            'rasen_decree_trials_effect = {',
            '\tif = {', '\t\tlimit = { OR = { NOT = { has_global_variable = ac_ascension_countdown } global_var:ac_ascension_countdown > 1 } }',
            '\t\tset_global_variable = { name = ac_ascension_countdown value = 1 }', '\t}', '}', '']
    out += patronage_effects()
    out += succession_effects()
    out += movement_effects()
    return '\n'.join(out)


def movement_effects():
    out = ['# Global scope. Each seated Exalt leads their land\'s movement in the dynastic cycle.',
           'rasen_exalt_movements_effect = {',
           '\tsituation:dynastic_cycle ?= {']
    for land, movement in MOVEMENTS.items():
        out += ['\t\tevery_participant_group = {',
                f'\t\t\tlimit = {{ participant_group_type = {movement}_movement {filled(land)} }}',
                f'\t\t\tset_variable = {{ name = movement_leader value = {holder(land)} }}',
                '\t\t}']
    return out + ['\t}', '}', '']


def succession_effects():
    out = ['# Character scope. Take the seat of $LAND$: give up any lands, move to the High Steward\'s court and',
           '# found a Celestial noble family with an estate on Azuma Honsha.',
           'rasen_seat_exalt_effect = {',
           '\tsave_scope_as = rasen_new_exalt',
           '\tif = {',
           '\t\tlimit = { has_global_variable = rasen_exalt_$LAND$ global_var:rasen_exalt_$LAND$ = { is_alive = yes } }',
           '\t\tglobal_var:rasen_exalt_$LAND$ = { remove_variable = rasen_exalt_seat remove_variable = rasen_exalt_since }',
           '\t}',
           '\tset_global_variable = { name = rasen_exalt_$LAND$ value = scope:rasen_new_exalt }',
           '\tset_variable = { name = rasen_exalt_seat value = flag:$LAND$ }',
           '\tset_variable = { name = rasen_exalt_since value = current_year }',
           '\tif = {',
           '\t\tlimit = { is_ruler = no exists = title:h_china.holder NOT = { liege_or_court_owner ?= title:h_china.holder } }',
           '\t\ttitle:h_china.holder = { add_courtier = scope:rasen_new_exalt }',
           '\t}',
           '\tif = {',
           '\t\tlimit = { is_ruler = no exists = title:h_china.holder }',
           '\t\tcreate_noble_family_effect = { GOVERNMENT_GIVER = title:h_china.holder }',
           '\t}',
           '}',
           '',
           f'# Global scope, yearly, before the Council sits. A seat falls vacant when its Exalt dies or after {EXALT_TERM_YEARS} years;',
           '# the land ruler\'s nominee takes it if they still qualify (build_rasen_interactions.py), otherwise the',
           '# strongest unlanded cultivator of that land.',
           'rasen_exalt_succession_effect = {']
    for land in KEYS:
        designate = f'global_var:rasen_exalt_designate_{land}'
        out += ['\tif = {',
                f'\t\tlimit = {{ OR = {{ NOT = {{ {filled(land)} }} {holder(land)} = {{ var:rasen_exalt_since <= {{ value = current_year subtract = {EXALT_TERM_YEARS} }} }} }} }}',
                '\t\tif = {',
                f'\t\t\tlimit = {{ has_global_variable = rasen_exalt_designate_{land} {designate} = {{ rasen_exalt_candidate_trigger = {{ LAND = {land} }} }} }}',
                f'\t\t\t{designate} = {{ rasen_seat_exalt_effect = {{ LAND = {land} }} }}',
                '\t\t}',
                '\t\telse = {',
                '\t\t\tordered_living_character = {',
                f'\t\t\t\tlimit = {{ rasen_exalt_candidate_trigger = {{ LAND = {land} }} }}',
                '\t\t\t\torder_by = ac_aura_pressure_value',
                f'\t\t\t\trasen_seat_exalt_effect = {{ LAND = {land} }}',
                '\t\t\t}',
                '\t\t}',
                f'\t\tremove_global_variable = rasen_exalt_designate_{land}',
                '\t}']
    return out + ['}', '']


def patronage_effects():
    out = ['# Global scope, 45 days after a yearly pulse. When the Trials have just opened,',
           '# "the Exalts themselves are sending customary gifts to their favored among the Top Five".',
           'rasen_trial_patronage_effect = {',
           '\tif = {',
           '\t\tlimit = {',
           '\t\t\thas_global_variable = ac_ascension_countdown',
           '\t\t\tglobal_var:ac_ascension_countdown = ac_ascension_interval_years',
           '\t\t\tNOT = { has_global_variable = rasen_patronage_this_trials }',
           '\t\t}',
           '\t\tset_global_variable = { name = rasen_patronage_this_trials value = yes years = 1 }',
           '\t\t# One AI Exalt sponsors the favourite, tilting the scales in their land\'s eyes.',
           '\t\tif = {',
           '\t\t\tlimit = { has_global_variable = ac_ascension_champion }',
           '\t\t\trandom_list = {']
    for land in KEYS:
        out += [f'\t\t\t\t1 = {{', f'\t\t\t\t\tmodifier = {{ factor = 0 NOT = {{ {filled(land)} }} }}',
                f'\t\t\t\t\tmodifier = {{ factor = 0 {filled(land)} {holder(land)} = {{ is_ai = no }} }}',
                f'\t\t\t\t\tset_global_variable = {{ name = rasen_trial_patron_land value = flag:{land} }}',
                f'\t\t\t\t\t{at_seat(land, "save_scope_as = rasen_trial_patron")}', '\t\t\t\t}']
    out += ['\t\t\t}',
            '\t\t\tif = {',
            '\t\t\t\tlimit = { exists = scope:rasen_trial_patron }',
            '\t\t\t\tglobal_var:ac_ascension_champion = {',
            '\t\t\t\t\tadd_gold = 100',
            '\t\t\t\t\tadd_opinion = { target = scope:rasen_trial_patron modifier = rasen_trial_patron_opinion }',
            ]
    for i, land in enumerate(KEYS):
        kw = 'if' if i == 0 else 'else_if'
        out.append(f'\t\t\t\t\t{kw} = {{ limit = {{ global_var:rasen_trial_patron_land = flag:{land} }} '
                   f'ac_favor_change_effect = {{ LAND = {land} AMOUNT = 2 }} }}')
    out += ['\t\t\t\t}',
            '\t\t\t\t# Another Exalt counters the interference through the players in the Trials.',
            '\t\t\t\tevery_player = {',
            '\t\t\t\t\tlimit = { has_character_flag = ac_ascension_entrant }',
            '\t\t\t\t\ttrigger_event = rasen_council.0081',
            '\t\t\t\t}',
            '\t\t\t}',
            '\t\t}',
            '\t}',
            '}',
            '',
            '# Entrant scope: pick the counter-patron, an Exalt other than the favourite\'s patron.',
            'rasen_pick_counter_patron_effect = {',
            '\trandom_list = {']
    for land in KEYS:
        out += [f'\t\t1 = {{', f'\t\t\tmodifier = {{ factor = 0 NOT = {{ {filled(land)} }} }}',
                f'\t\t\tmodifier = {{ factor = 0 global_var:rasen_trial_patron_land = flag:{land} }}',
                f'\t\t\tmodifier = {{ factor = 0 {filled(land)} {holder(land)} = root }}',
                f'\t\t\tmodifier = {{ factor = 3 {filled(land)} has_variable = ac_favor_{land} var:ac_favor_{land} > 0 }}',
                f'\t\t\tset_variable = {{ name = rasen_counter_patron_land value = flag:{land} years = 1 }}',
                f'\t\t\t{at_seat(land, "save_scope_as = rasen_counter_patron")}', '\t\t}']
    out += ['\t}', '}', '', '# Entrant scope: accept the counter-patron\'s offer.', 'rasen_accept_counter_patron_effect = {',
            '\tadd_gold = 100',
            '\tadd_opinion = { target = scope:rasen_counter_patron modifier = rasen_trial_patron_opinion }',
            '\tscope:rasen_counter_patron = { add_opinion = { target = root modifier = rasen_trial_protege_opinion } }']
    for i, land in enumerate(KEYS):
        kw = 'if' if i == 0 else 'else_if'
        out.append(f'\t{kw} = {{ limit = {{ var:rasen_counter_patron_land = flag:{land} }} ac_favor_change_effect = {{ LAND = {land} AMOUNT = 1 }} }}')
    out += ['}']
    return out


def modifiers():
    return '\n'.join([
        'rasen_archon_patrols_modifier = {', '\ticon = county_modifier_control_positive',
        '\tmonthly_county_control_growth_add = 0.5', '\tcounty_opinion_add = 5', '}', '',
        'rasen_fiend_purge_modifier = {', '\ticon = county_modifier_development_positive', '\tepidemic_resistance = 10', '}', '',
        'rasen_imperial_levy_modifier = {', '\ticon = county_modifier_development_negative',
        '\ttax_mult = -0.15', '\tcounty_opinion_add = -5', '}',
    ])


def opinions():
    return '\n'.join([
        '# "Inter-council conflicts are not uncommon."',
        'rasen_council_outvoted_opinion = {', '\topinion = -15', '\tyears = 6', '\tdecaying = yes', '}', '',
        '# An Exalt\'s sponsorship in the Heavenly Ascension Trials.',
        'rasen_trial_patron_opinion = {', '\topinion = 20', '\tyears = 10', '\tdecaying = yes', '}', '',
        'rasen_trial_protege_opinion = {', '\topinion = 15', '\tyears = 10', '\tdecaying = yes', '}',
    ])


def events():
    out = ['namespace = rasen_council', '',
           '# 0001 an Exalt casts a vote; 0002 the decree is proclaimed; 0080 Trial patronage (hidden);',
           '# 0081 an Exalt offers a player entrant patronage; 0090 the session closes (hidden).', '',
           'rasen_council.0001 = {', '\ttype = character_event', '\ttitle = rasen_council.0001.t',
           '\tdesc = rasen_council.0001.desc', '\ttheme = realm',
           '\tleft_portrait = { character = root animation = personality_rational }', '']
    own = {land: decree for land, decree, *_ in LANDS}
    for land, decree, *_ in LANDS:
        out += ['\toption = {', f'\t\tname = rasen_council.0001.{land}', f'\t\tcustom_tooltip = rasen_decree_{decree}_tt',
                f'\t\tchange_global_variable = {{ name = rasen_votes_{land} add = 1 }}',
                f'\t\tai_chance = {{ base = 10 modifier = {{ add = 50 rasen_holds_seat_trigger = {{ LAND = {land} }} }} }}', '\t}']
    # Lobbying: two votes for one's own land's decree.
    out += ['\toption = {', '\t\tname = rasen_council.0001.lobby',
            f'\t\ttrigger = {{ prestige >= {LOBBY_PRESTIGE} }}',
            f'\t\tadd_prestige = -{LOBBY_PRESTIGE}']
    for i, land in enumerate(KEYS):
        kw = 'if' if i == 0 else 'else_if'
        out += [f'\t\t{kw} = {{', f'\t\t\tlimit = {{ rasen_holds_seat_trigger = {{ LAND = {land} }} }}',
                f'\t\t\tcustom_tooltip = rasen_decree_{own[land]}_tt',
                f'\t\t\tchange_global_variable = {{ name = rasen_votes_{land} add = 2 }}', '\t\t}']
    out += ['\t\tai_chance = { base = 0 }', '\t}', '}', '',
            'rasen_council.0002 = {', '\ttype = character_event', '\ttitle = rasen_council.0002.t', '\tdesc = {', '\t\tfirst_valid = {']
    for land, *_ in LANDS:
        out.append(f'\t\t\ttriggered_desc = {{ trigger = {{ global_var:rasen_decree = flag:{land} }} desc = rasen_council.0002.{land} }}')
    out += ['\t\t}', '\t}', '\ttheme = realm', '\tleft_portrait = { character = root animation = personality_rational }',
            '\toption = { name = rasen_council.0002.ok }', '}', '',
            'rasen_council.0080 = {', '\ttype = character_event', '\thidden = yes',
            '\timmediate = { rasen_trial_patronage_effect = yes }', '}', '',
            'rasen_council.0081 = {', '\ttype = character_event', '\ttitle = rasen_council.0081.t', '\tdesc = rasen_council.0081.desc',
            '\ttheme = realm',
            '\ttrigger = { has_character_flag = ac_ascension_entrant }',
            '\timmediate = {', '\t\trasen_pick_counter_patron_effect = yes', '\t}',
            '\tleft_portrait = { character = root animation = personality_rational }',
            '\tright_portrait = { character = scope:rasen_counter_patron animation = scheme }',
            '\toption = {', '\t\tname = rasen_council.0081.accept',
            '\t\ttrigger = { exists = scope:rasen_counter_patron }', '\t\trasen_accept_counter_patron_effect = yes', '\t}',
            '\toption = {', '\t\tname = rasen_council.0081.refuse', '\t\tadd_prestige = 50', '\t}', '}', '',
            'rasen_council.0090 = {', '\ttype = character_event', '\thidden = yes',
            '\timmediate = { rasen_council_enact_effect = yes }', '}']
    return '\n'.join(out)


def localization():
    out = ['l_english:',
           ' rasen_council.0001.t:0 "The Exalted Council Convenes"',
           ' rasen_council.0001.desc:0 "Since the disappearance of the Imperial family, the five Inner Kingdoms have kept a shaky peace through their seats on the Exalted Council, which rules Imperial Rasen from Azuma Honsha. The Council convenes, and as an Exalt I must cast my vote. The decree will fall where the votes are heaviest, though nothing on the Council is ever certain."',
           f' rasen_council.0001.lobby:0 "Press my seat\'s cause: two votes for my own land\'s decree"',
           ' rasen_council.0002.t:0 "A Decree of the Exalted Council"',
           ' rasen_council.0002.ok:0 "As the Council pleases."',
           ' rasen_council.0081.t:0 "An Exalt\'s Envoy"',
           ' rasen_council.0081.desc:0 "Word has spread that an Exalt is sponsoring the favourite of this year\'s Heavenly Ascension Trials, greatly tipping the scales. Now an envoy of [rasen_counter_patron.GetTitledFirstName] arrives with gold and an offer: their Exalt will see me favoured, so long as I serve to counter the interference. Inter-council conflicts are not uncommon, and I would be a tool in one."',
           ' rasen_council.0081.accept:0 "I accept the Exalt\'s patronage."',
           ' rasen_council.0081.refuse:0 "I will rise on my own merit."',
           ' rasen_archon_patrols_modifier:0 "Archon Patrols"',
           ' rasen_archon_patrols_modifier_desc:0 "Archons of the Exalted Council keep the peace here."',
           ' rasen_fiend_purge_modifier:0 "Fiend Purge"',
           ' rasen_fiend_purge_modifier_desc:0 "Exorcist-monks hunt Fiends and all things unnatural."',
           ' rasen_imperial_levy_modifier:0 "Imperial Levy"',
           ' rasen_imperial_levy_modifier_desc:0 "The Outer provinces pay for the capital."',
           ' rasen_council_outvoted_opinion:0 "Outvoted me on the Council"',
           ' rasen_trial_patron_opinion:0 "My patron in the Trials"',
           ' rasen_trial_protege_opinion:0 "My protégé in the Trials"']
    for land, decree, name, desc, value in LANDS:
        out += [f' rasen_council.0001.{land}:0 "{name} (the {land.title()} Lands value {value})"',
                f' rasen_decree_{decree}_tt:0 "{desc}"',
                f' rasen_council.0002.{land}:0 "Heralds carry the Exalted Council\'s decree across the spiral continent: #V {name}#!.\\n\\n{desc}"']
    return '\n'.join(out)


def render():
    texts = {
        'common/on_action/rasen_council_on_actions.txt': on_actions(),
        'common/scripted_effects/rasen_council_effects.txt': effects(),
        'common/scripted_triggers/rasen_council_triggers.txt': triggers(),
        'common/modifiers/rasen_council_modifiers.txt': modifiers(),
        'common/opinion_modifiers/rasen_council_opinions.txt': opinions(),
        'events/rasen_council_events.txt': events(),
        'localization/english/rasen_council_l_english.yml': localization(),
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
    print(f'Exalted Council: {len(files)} files, {len(LANDS)} seats.')


if __name__ == '__main__':
    main()
