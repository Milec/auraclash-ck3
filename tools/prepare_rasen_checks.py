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
    for land in ('bladed', 'sacred', 'mystic', 'cursed', 'wild', 'azuma'):
        body.append(check(f'{land}_ruled', f'exists = title:k_{land}.holder'))
    body.append(check('exalt_cultivator', 'title:k_bladed.holder = { has_trait = ac_cultivator has_trait = ac_immortal_core }'))
    body.append(check('exalt_race', 'title:k_bladed.holder = { has_trait = ac_race_human }'))
    body.append(check('exalt_faith', 'title:k_bladed.holder = { faith = faith:ancestral_rites }'))
    body.append(check('exalt_culture', 'title:k_bladed.holder = { culture = culture:zenshin }'))
    body.append(check('keiko', 'title:k_bladed.holder = { any_child = { has_trait = lifestyle_physician } }'))
    body.append(check('divine_general', 'any_living_character = { has_trait = rasen_divine_general }'))
    body.append(check('akuma_seeded', 'any_in_global_list = { variable = rasen_akuma_members count >= 5 }'))
    body.append(check('capital_holding', 'title:c_azuma.title_province = { has_holding = yes }'))
    # The realm: the High Steward holds the hegemony for the Council, the Exalts are its kings, and
    # appointed Magistrates govern the Outer duchies and counties.
    body.append(check('hegemony', 'title:h_rasen.holder = { this = title:k_azuma.holder has_government = meritocratic_government }'))
    body.append(check('exalt_liege', 'title:k_bladed.holder = { liege = title:h_rasen.holder }'))
    body.append(check('exalt_feudal', 'title:k_bladed.holder = { has_government = feudal_government }'))
    body.append(check('magistrate_liege', 'title:d_kohara.holder = { liege = title:h_rasen.holder }'))
    body.append(check('magistrate_merit', 'title:d_kohara.holder = { has_government = meritocratic_government }'))
    body.append(check('county_magistrates', 'title:k_outer_west = { any_de_jure_county = { count >= 20 holder = { '
                      'has_government = meritocratic_government highest_held_title_tier = tier_county } } }'))
    body.append(check('steward_estate', 'title:h_rasen.holder = { has_domicile = yes any_held_title = { is_noble_family_title = yes } }'))
    body.append(check('magistrate_estate', 'title:d_kohara.holder = { has_domicile = yes }'))
    body.append(check('county_magistrate_families', 'title:k_outer_west = { any_de_jure_county = { count >= 20 holder = { '
                      'highest_held_title_tier = tier_county any_held_title = { is_noble_family_title = yes } } } }'))
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
    body.append('\ttitle:k_wild.holder = { save_scope_as = ac_duel_foe }\n'
                '\ttitle:k_mystic.holder = { ac_duel_start_effect = { LETHAL = no } }\n')
    body.append(check('duel_resolved', 'title:k_mystic.holder = { NOT = { has_variable = ac_duel_foe } }'))
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
    body.append('\tdebug_log = "RASEN_QA COMPLETE"\n')
    return ('namespace = rasen_qa\n\nrasen_qa.0001 = {\n\ttype = character_event\n\thidden = yes\n\timmediate = {\n'
            + ''.join('\t' + line for line in ''.join(body).splitlines(True)) + '\t}\n}\n')


def main():
    overlay = OUT / 'qa-mod'
    files = {
        'common/on_action/rasen_qa.txt': ('on_game_start_after_lobby = { on_actions = { rasen_qa } }\n'
                                          'rasen_qa = { effect = { title:k_bladed.holder = { trigger_event = rasen_qa.0001 } } }\n'
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
                                          'if = { limit = { title:k_bladed.holder = { is_alive = yes } } debug_log = "RASEN_QA YEAR EXALT_ALIVE" } '
                                          'if = { limit = { global_var:qa_heir_sect = { story_owner = { is_alive = yes has_trait = ac_sect_master '
                                          'this != global_var:qa_dead_master } var:ac_estate_title.holder = story_owner } } '
                                          'debug_log = "RASEN_QA YEAR MASTER_SUCCEEDED" } '
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
