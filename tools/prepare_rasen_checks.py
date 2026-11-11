"""Prepare an in-game QA run of Imperial Rasen (no menus needed).

Writes a separate CK3 user directory under output/rasen-runtime with its own mod list
(AuraClash, RasenMap and a small QA overlay), so the player's own settings are untouched.
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
                    f'\tdebug_log = "RASEN_QA YEAR {year} DONE"\n')
    body.append(check('council_countdown', 'has_global_variable = rasen_council_countdown'))
    body.append(check('trials_countdown', 'has_global_variable = ac_ascension_countdown'))
    body.append('\tdebug_log = "RASEN_QA COMPLETE"\n')
    return ('namespace = rasen_qa\n\nrasen_qa.0001 = {\n\ttype = character_event\n\thidden = yes\n\timmediate = {\n'
            + ''.join('\t' + line for line in ''.join(body).splitlines(True)) + '\t}\n}\n')


def main():
    overlay = OUT / 'qa-mod'
    files = {
        'common/on_action/rasen_qa.txt': ('on_game_start_after_lobby = { on_actions = { rasen_qa } }\n'
                                          'rasen_qa = { effect = { title:k_bladed.holder = { trigger_event = rasen_qa.0001 } } }\n'),
        'events/rasen_qa.txt': event(),
    }
    for relative, text in files.items():
        path = overlay / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8-sig', newline='\n')
    (OUT / 'mod').mkdir(parents=True, exist_ok=True)
    rasen_descriptor = (ROOT / 'RasenMap/descriptor.mod').read_text(encoding='utf-8-sig').rstrip()
    descriptors = {
        'aura_clash': f'name="Aura Clash"\npath="{(ROOT / "AuraClash").as_posix()}"\nsupported_version="1.20.*"\n',
        'imperial_rasen': f'{rasen_descriptor}\npath="{(ROOT / "RasenMap").as_posix()}"\n',
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
