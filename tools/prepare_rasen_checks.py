"""Prepare an in-game QA run of Imperial Rasen (no menus needed).

Writes a separate CK3 user directory under output/rasen-runtime with its own mod list
(AuraClash and a small QA overlay), so the player's own settings are untouched.
The overlay runs on game start: it checks the bookmark's setup and exercises the Exalted
Council, the Clash of Auras, the Akuma Lords and the Ice Incursions once, logging
"RASEN_QA PASS <name>" or "RASEN_QA FAIL <name>" for each check and "RASEN_QA COMPLETE".

Usage: python tools/prepare_rasen_checks.py
Then launch ck3.exe with the printed arguments, wait for COMPLETE in the logs, and close it.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/rasen-runtime'
BOOKMARK, PLAY = 'bm_rasen_trials', 'k_bladed'


def check(name, trigger):
    return (f'\tif = {{ limit = {{ {trigger} }} debug_log = "RASEN_QA PASS {name}" }}\n'
            f'\telse = {{ debug_log = "RASEN_QA FAIL {name}" }}\n')


def event():
    body = ['\tdebug_log = "RASEN_QA START"\n']
    # The bookmark's world.
    # Each Inner Kingdom has its own ruler and government; the Wild Lands have none, only Maos.
    for land, government in (('bladed', 'japan_feudal_government'), ('mystic', 'administrative_government'),
                             ('cursed', 'clan_government'), ('sacred', 'theocracy_government')):
        body.append(check(f'{land}_ruled', f'title:k_{land}.holder ?= {{ has_government = {government} liege = title:h_china.holder '
                          'NOT = { has_variable = rasen_exalt_seat } }'))
    body.append(check('azuma_ruled', 'exists = title:k_azuma.holder'))
    body.append(check('wild_unruled', 'NOT = { exists = title:k_wild.holder }'))
    # The Exalts hold no land: each sits at the High Steward's court as head of a Celestial noble family.
    for land in ('bladed', 'sacred', 'mystic', 'cursed', 'wild'):
        body.append(check(f'exalt_seated_{land}', f'rasen_seat_filled_trigger = {{ LAND = {land} }} global_var:rasen_exalt_{land} = {{ '
                          f'rasen_holds_seat_trigger = {{ LAND = {land} }} NOT = {{ any_held_title = {{ tier >= tier_county is_noble_family_title = no }} }} '
                          'any_held_title = { is_noble_family_title = yes } liege_or_court_owner = title:h_china.holder }'))
    # The Exalts lead the dynastic cycle's movements.
    for land, movement in (('bladed', 'pro_hegemon'), ('mystic', 'advancement'), ('wild', 'expansion'), ('sacred', 'conservative')):
        body.append(check(f'exalt_leads_{movement}', f'situation:dynastic_cycle = {{ any_participant_group = {{ '
                          f'participant_group_type = {movement}_movement var:movement_leader ?= global_var:rasen_exalt_{land} }} }}'))
    body.append(check('peace_law', 'title:h_china.holder = { has_realm_law_flag = rasen_great_lords_need_leave }'))
    body.append(check('exalt_co_monarch', 'title:h_china.holder = { diarch ?= { rasen_is_exalt_trigger = yes } }'))
    body.append(check('exalt_estate', 'global_var:rasen_exalt_bladed = { has_domicile = yes }'))
    body.append(check('exalt_cultivator', 'global_var:rasen_exalt_bladed = { has_trait = ac_cultivator has_trait = ac_immortal_core }'))
    body.append(check('exalt_race', 'global_var:rasen_exalt_bladed = { has_trait = ac_race_human }'))
    body.append(check('exalt_faith', 'global_var:rasen_exalt_bladed = { faith = faith:ancestral_rites }'))
    body.append(check('exalt_culture', 'global_var:rasen_exalt_bladed = { culture = culture:zenshin }'))
    body.append(check('keiko', 'global_var:rasen_exalt_bladed = { any_child = { has_trait = lifestyle_physician } }'))
    body.append(check('divine_general', 'any_living_character = { has_trait = rasen_divine_general }'))
    body.append(check('akuma_seeded', 'any_in_global_list = { variable = rasen_akuma_members count >= 5 }'))
    body.append(check('capital_holding', 'title:c_azuma.title_province = { has_holding = yes }'))
    # The realm: the High Steward holds the hegemony for the Council, and appointed Magistrates govern
    # the Outer duchies and counties.
    body.append(check('hegemony', 'title:h_china.holder = { this = title:k_azuma.holder has_government = celestial_government }'))
    body.append(check('magistrate_liege', 'title:d_kohara.holder = { liege = title:h_china.holder }'))
    body.append(check('magistrate_merit', 'title:d_kohara.holder = { has_government = celestial_government }'))
    body.append(check('county_magistrates', 'title:k_outer_west = { any_de_jure_county = { count >= 20 holder = { '
                      'has_government = celestial_government highest_held_title_tier = tier_county } } }'))
    body.append(check('steward_estate', 'title:h_china.holder = { has_domicile = yes any_held_title = { is_noble_family_title = yes } }'))
    # The game's own Celestial machinery runs over Rasen: the dynastic cycle, its movements and the ministries.
    body.append(check('celestial_cycle', 'exists = situation:dynastic_cycle'))
    body.append(check('celestial_movements', 'situation:dynastic_cycle = { any_participant_group = { count >= 4 } }'))
    body.append(check('celestial_ministries', 'exists = title:e_minister_chancellor exists = title:e_minister_of_works'))
    body.append(check('celestial_bureaucracy_law', 'title:h_china.holder = { realm_law_use_celestial_bureaucracy = yes }'))
    body.append(check('magistrate_estate','title:d_kohara.holder = { has_domicile = yes }'))
    body.append(check('county_magistrate_families', 'title:k_outer_west = { any_de_jure_county = { count >= 20 holder = { '
                      'highest_held_title_tier = tier_county any_held_title = { is_noble_family_title = yes } } } }'))
    # The Wild Lands are thirteen tribal Maos who answer only to the hegemony.
    body.append(check('wild_maos', 'title:h_china.holder = { any_vassal = { count = 13 '
                      'capital_county.kingdom = title:k_wild has_government = tribal_government } }'))
    body.append(check('divine_general_free', 'any_living_character = { has_trait = rasen_divine_general is_independent_ruler = yes }'))
    # The story's sects, each at its seat, with standing by region.
    def sect(county, condition):
        return f'title:{county}.title_province = {{ has_variable = ac_province_sect var:ac_province_sect = {{ {condition} }} }}'
    body.append('\ttrigger_event = { on_action = ac_sect_initialize }\n')
    body.append(check('sects_seeded', 'any_in_global_list = { variable = ac_sects count = 23 }'))
    body.append(check('sect_thunderfall', sect('c_thunderfall', 'var:ac_identity = flag:thunderfall var:ac_tier = 1 var:ac_treasury = 150')))
    body.append(check('sect_sunbringer', sect('c_sunbringer', 'var:ac_identity = flag:sunbringer')))
    body.append(check('sect_trade', sect('c_ironrise', 'var:ac_identity = flag:choral_line has_variable = ac_trade_sect var:ac_treasury = 350')))
    body.append(check('sect_outer_east', sect('c_sazawa', 'var:ac_tier = 2')))
    body.append(check('sect_inner', sect('c_gohara', 'var:ac_identity = flag:ten_thousand_blades var:ac_tier = 3 var:ac_scripture_library = 1')))
    body.append(check('sect_capital', sect('c_azuma', 'var:ac_tier = 4 var:ac_cultivation_hall = 2 exists = var:ac_estate_title')))
    body.append(check('sect_frontier_master', sect('c_thunderfall', 'story_owner = { has_trait = ac_sect_master '
                      'NOT = { has_trait_xp = { trait = ac_cultivator track = ac_core_soul value >= 70 } } }')))
    body.append(check('sect_imperial_master', sect('c_azuma', 'story_owner = { has_trait_xp = { trait = ac_cultivator track = ac_core_soul value >= 85 } }')))
    # Aura Pressure by rank and region, after the author's figures.
    body.append(check('ap_exalt', 'global_var:rasen_exalt_bladed = { var:ac_aura_pressure >= 15000 }'))
    body.append(check('ap_outer_master', sect('c_thunderfall', 'story_owner = { var:ac_aura_pressure >= 3200 var:ac_aura_pressure <= 4000 }')))
    body.append(check('ap_inner_master', sect('c_gohara', 'story_owner = { var:ac_aura_pressure >= 6800 var:ac_aura_pressure <= 7200 }')))
    body.append(check('ap_outer_upper', sect('c_thunderfall', 'any_in_list = { variable = ac_members count >= 5 has_trait = ac_sect_upper_disciple '
                      'var:ac_aura_pressure >= 800 var:ac_aura_pressure <= 1600 }')))
    body.append(check('ap_outer_lower', sect('c_thunderfall', 'any_in_list = { variable = ac_members count >= 11 has_trait = ac_sect_lower_disciple '
                      'var:ac_aura_pressure >= 400 var:ac_aura_pressure <= 800 }')))
    body.append(check('ap_inner_lower', sect('c_gohara', 'any_in_list = { variable = ac_members count >= 18 has_trait = ac_sect_lower_disciple '
                      'var:ac_aura_pressure >= 1200 var:ac_aura_pressure <= 1600 }')))
    body.append(check('sect_frontier_roster', sect('c_thunderfall', 'var:ac_upper_count = 5 var:ac_lower_count = 11')))
    body.append(check('sect_great_roster', sect('c_gohara', 'var:ac_upper_count = 9 var:ac_lower_count = 18')))
    # Sect life: every event runs for a disciple and a master, a duel between sects counts for
    # the winner's sect, and renown lifts a Frontier Sect one standing.
    body.append('\ttitle:c_thunderfall.title_province.var:ac_province_sect = {\n'
                '\t\tsave_scope_as = qa_sect\n'
                '\t\tstory_owner = { save_scope_as = qa_master }\n'
                '\t\trandom_in_list = { variable = ac_members limit = { has_trait = ac_sect_upper_disciple } save_scope_as = qa_disciple }\n'
                '\t}\n'
                '\ttitle:c_ironrise.title_province.var:ac_province_sect.story_owner = { save_scope_as = qa_trader }\n'
                '\ttitle:c_nanhou.title_province.var:ac_province_sect.story_owner = { save_scope_as = qa_rival }\n')
    for n in (1, 2, 3, 4):
        body.append(f'\tscope:qa_disciple = {{ trigger_event = ac_sect_life.000{n} }}\n')
    body.append('\tscope:qa_master = { trigger_event = ac_sect_life.0005 trigger_event = ac_sect_life.0006 }\n'
                '\tscope:qa_trader = { trigger_event = ac_sect_life.0007 }\n'
                '\tscope:qa_sect = { set_variable = { name = ac_renown value = 0 } }\n'
                '\tscope:qa_rival = { save_scope_as = ac_duel_foe }\n'
                '\tscope:qa_master = { ac_duel_start_effect = { LETHAL = no } }\n')
    body.append(check('sect_duel_renown', 'OR = { scope:qa_sect.var:ac_renown = 2 scope:qa_rival.var:ac_sect.var:ac_renown >= 2 }'))
    body.append('\tscope:qa_sect = { set_variable = { name = ac_renown value = 70 } ac_sect_standing_effect = yes }\n')
    body.append(check('sect_rises', 'scope:qa_sect = { var:ac_tier = 2 var:ac_renown = 10 }'))
    body.append('\tscope:qa_sect = { set_variable = { name = ac_renown value = 500 } ac_sect_standing_effect = yes }\n')
    body.append(check('sect_rise_capped', 'scope:qa_sect = { var:ac_tier = 2 }'))
    body.append(check('sect_income', 'scope:qa_sect = { ac_sect_annual_income = 110 }'))
    # The Exalted Council: a session, then the decree.
    body.append('\trasen_council_session_effect = yes\n\trasen_council_enact_effect = yes\n')
    body.append(check('council_decree', 'has_global_variable = rasen_decree'))
    # The Clash of Auras between two AI Exalts (auto-resolved).
    body.append('\tglobal_var:rasen_exalt_wild = { save_scope_as = ac_duel_foe }\n'
                '\tglobal_var:rasen_exalt_mystic = { ac_duel_start_effect = { LETHAL = no } }\n')
    body.append(check('duel_resolved', 'global_var:rasen_exalt_mystic = { NOT = { has_variable = ac_duel_foe } }'))
    # The Akuma Lords recruit; an Ice Incursion begins.
    body.append('\trasen_shadows_yearly_effect = yes\n\trasen_begin_ice_incursion_effect = yes\n')
    body.append(check('ice_incursion', 'has_global_variable = rasen_ice_incursion_active'))
    # Every yearly system, three years running, as the yearly pulse would (the game starts paused).
    for year in range(1, 4):
        body.append('\trasen_council_yearly_effect = yes\n\trasen_shadows_yearly_effect = yes\n'
                    '\trasen_ice_incursion_yearly_effect = yes\n\tac_ascension_yearly_effect = yes\n'
                    '\tevery_in_global_list = { variable = ac_sects ac_sect_yearly_effect = yes }\n'
                    f'\tdebug_log = "RASEN_QA YEAR {year} DONE"\n')
    # Left for the years that follow (see the YEAR marks): a sect master dies.
    body.append('\ttitle:c_himiura.title_province.var:ac_province_sect = { set_global_variable = { name = qa_heir_sect value = this } '
                'story_owner = { set_global_variable = { name = qa_dead_master value = this } death = natural } }\n')
    body.append(check('council_countdown', 'has_global_variable = rasen_council_countdown'))
    body.append(check('trials_countdown', 'has_global_variable = ac_ascension_countdown'))
    # Governing (build_rasen_interactions.py): the Archonate fills, a nominee takes a vacated seat, and an
    # Outer county the hegemon holds goes to a noble of the Inner Kingdoms.
    body.append('\trandom_living_character = { limit = { has_trait = ac_cultivator is_ruler = no is_adult = yes NOT = { rasen_is_exalt_trigger = yes } } '
                'set_variable = { name = ac_aura_pressure value = 9000 } }\n')
    body.append('\trasen_governing_yearly_effect = yes\n')
    body.append(check('archon_raised', 'any_living_character = { has_trait = rasen_archon }'))
    body.append('\trandom_living_character = { limit = { rasen_exalt_candidate_trigger = { LAND = cursed } } save_scope_as = qa_nominee }\n'
                '\tset_global_variable = { name = rasen_exalt_designate_cursed value = scope:qa_nominee }\n'
                '\tglobal_var:rasen_exalt_cursed = { death = natural }\n'
                '\trasen_exalt_succession_effect = yes\n')
    body.append(check('nominee_seated', 'exists = scope:qa_nominee global_var:rasen_exalt_cursed = scope:qa_nominee'))
    body.append('\trandom_county_in_region = { region = world_rasen_outer limit = { holder = { highest_held_title_tier = tier_county } } save_scope_as = qa_outer }\n'
                '\ttitle:h_china.holder = { create_title_and_vassal_change = { type = granted save_scope_as = qa_change add_claim_on_loss = no } '
                'scope:qa_outer = { change_title_holder = { holder = title:h_china.holder change = scope:qa_change } } resolve_title_and_vassal_change = scope:qa_change }\n'
                '\trasen_governing_yearly_effect = yes\n')
    body.append(check('magistrate_from_inner', 'scope:qa_outer = { holder = { NOT = { this = title:h_china.holder } has_government = celestial_government } }'))
    body.append('\tdebug_log = "RASEN_QA COMPLETE"\n')
    return ('namespace = rasen_qa\n\nrasen_qa.0001 = {\n\ttype = character_event\n\thidden = yes\n\timmediate = {\n'
            + ''.join('\t' + line for line in ''.join(body).splitlines(True)) + '\t}\n}\n')


def main():
    overlay = OUT / 'qa-mod'
    files = {
        'common/on_action/rasen_qa.txt': ('on_game_start_after_lobby = { on_actions = { rasen_qa } }\n'
                                          'rasen_qa = { effect = { title:k_bladed.holder = { trigger_event = { id = rasen_qa.0001 days = 4 } } } }\n'
                                          # The game starts paused and cannot be unpaused unattended (launch flags
                                          # and an interface widget calling the pause button's action were both
                                          # tried). Once a person unpauses it, each year leaves these marks.
                                          'yearly_global_pulse = { on_actions = { rasen_qa_year } }\n'
                                          'rasen_qa_year = { effect = { debug_log = "RASEN_QA YEAR TICK" '
                                          'if = { limit = { has_global_variable = rasen_decree } debug_log = "RASEN_QA YEAR DECREE_SET" } '
                                          'if = { limit = { any_in_global_list = { variable = ac_sects count >= 23 '
                                          'exists = story_owner story_owner = { is_alive = yes has_trait = ac_sect_master } } } '
                                          'debug_log = "RASEN_QA YEAR SECTS_LED" } '
                                          'if = { limit = { any_in_global_list = { variable = ac_sects var:ac_renown > 0 } } '
                                          'debug_log = "RASEN_QA YEAR RENOWN_EARNED" } '
                                          'if = { limit = { any_in_global_list = { variable = ac_sects '
                                          'OR = { has_variable_list = ac_allies has_variable_list = ac_rivals } } } '
                                          'debug_log = "RASEN_QA YEAR SECT_TIES" } '
                                          'if = { limit = { rasen_seat_filled_trigger = { LAND = bladed } rasen_seat_filled_trigger = { LAND = sacred } '
                                          'rasen_seat_filled_trigger = { LAND = mystic } rasen_seat_filled_trigger = { LAND = cursed } '
                                          'rasen_seat_filled_trigger = { LAND = wild } } debug_log = "RASEN_QA YEAR EXALTS_SEATED" } '
                                          'if = { limit = { title:k_bladed.holder ?= { has_government = japan_feudal_government } } debug_log = "RASEN_QA YEAR SHOGUN_RULES" } '
                                          'if = { limit = { situation:dynastic_cycle ?= { any_participant_group = { count >= 3 var:movement_leader ?= { rasen_is_exalt_trigger = yes } } } } debug_log = "RASEN_QA YEAR EXALTS_LEAD" } '
                                          'if = { limit = { any_ruler = { highest_held_title_tier >= tier_duchy top_liege = title:h_china.holder NOT = { this = top_liege } save_temporary_scope_as = qa_lord any_character_war = { primary_attacker = scope:qa_lord NOR = { using_cb = depose_war using_cb = claimant_faction_war using_cb = independence_faction_war using_cb = liberty_faction_war using_cb = populist_war using_cb = peasant_war using_cb = nation_fracturing_faction_war } primary_defender = { highest_held_title_tier >= tier_duchy top_liege = title:h_china.holder NOT = { is_liege_or_above_of = scope:qa_lord } } } } } debug_log = "RASEN_QA YEAR GREAT_LORD_DECLARED_WAR" } '
                                          'if = { limit = { NOT = { exists = title:k_wild.holder } NOT = { exists = title:k_outer_west.holder } } debug_log = "RASEN_QA YEAR UNCROWNED" } '
                                          'if = { limit = { any_living_character = { has_trait = rasen_archon count >= 3 } } debug_log = "RASEN_QA YEAR ARCHONS" } '
                                          'if = { limit = { title:h_china.holder ?= { diarch ?= { rasen_is_exalt_trigger = yes } } } debug_log = "RASEN_QA YEAR CO_MONARCH" } '
                                          'if = { limit = { exists = situation:dynastic_cycle } debug_log = "RASEN_QA YEAR CYCLE_RUNNING" } '
                                          'if = { limit = { title:h_china.holder ?= { any_sub_realm_county = { count >= 250 } } } debug_log = "RASEN_QA YEAR HEGEMONY_HELD" } '
                                          'if = { limit = { global_var:qa_heir_sect = { story_owner = { is_alive = yes has_trait = ac_sect_master '
                                          'this != global_var:qa_dead_master } var:ac_estate_title.holder = story_owner } } '
                                          'debug_log = "RASEN_QA YEAR MASTER_SUCCEEDED" } '
                                          'if = { limit = { has_global_variable = ac_trials_opened } debug_log = "RASEN_QA YEAR TRIALS_OPENED" } '
                                          'if = { limit = { has_global_variable = ac_trial_examinees } debug_log = "RASEN_QA YEAR TRIAL_EXAMINEES" } '
                                          'if = { limit = { has_global_variable = ac_trials_judged } debug_log = "RASEN_QA YEAR TRIALS_JUDGED" } '
                                          'if = { limit = { has_global_variable = ac_trial_admissions } debug_log = "RASEN_QA YEAR TRIAL_ADMISSIONS" } '
                                          '} }\n'),
        'events/rasen_qa.txt': event(),
    }
    for relative, text in files.items():
        path = overlay / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8-sig', newline='\n')
    (OUT / 'mod').mkdir(parents=True, exist_ok=True)
    descriptor = (ROOT / 'AuraClash/descriptor.mod').read_text(encoding='utf-8-sig').rstrip()
    descriptors = {
        'aura_clash': f'{descriptor}\npath="{(ROOT / "AuraClash").as_posix()}"\n',
        'rasen_qa': f'name="Imperial Rasen QA"\npath="{overlay.as_posix()}"\nsupported_version="1.20.*"\n',
    }
    for name, text in descriptors.items():
        (OUT / 'mod' / f'{name}.mod').write_text(text, encoding='utf-8')
    (OUT / 'dlc_load.json').write_text(json.dumps({'enabled_mods': [f'mod/{n}.mod' for n in descriptors],
                                                   'disabled_dlcs': []}), encoding='utf-8')
    print(f'Prepared {OUT}. Launch with -debug_mode -skip -bookmark={BOOKMARK} -play={PLAY} -userdir="{OUT}"')
    print('Require RASEN_QA COMPLETE and no RASEN_QA FAIL in the logs under that user directory.')


if __name__ == '__main__':
    main()
