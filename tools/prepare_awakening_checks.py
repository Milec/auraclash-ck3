"""Prepare an isolated game exercising targeted requests and paid searches."""
from pathlib import Path
import argparse
import json
import shutil

from prepare_sect_engine_checks import test_body

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/awakening-runtime'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ui', action='store_true', help='Prepare a teacher portrait and an audit button for a real request.')
    args = parser.parse_args()
    overlay = OUT / 'qa-mod'
    startup = overlay / 'common/on_action/ac_awakening_qa.txt'
    startup.parent.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'AuraClash/tests/ac_awakening_tests.txt').read_text(encoding='utf-8-sig')
    body = source + '\n' + (ROOT / 'AuraClash/tests/ac_ai_awakening_tests.txt').read_text(encoding='utf-8-sig')
    # The shared harness normally runs in title scope; these tests use a character.
    checks = test_body('awakening', body.replace('root.', 'scope:ac_qa_learner.')).replace('title:k_england', 'scope:ac_qa_learner')
    startup.write_text('''on_game_start_after_lobby = { on_actions = { ac_awakening_qa } }
ac_awakening_qa = { effect = { title:k_england.holder = { trigger_event = ac_awakening_qa.0001 } } }
''', encoding='utf-8-sig')
    event = overlay / 'events/ac_awakening_qa.txt'
    event.parent.mkdir(parents=True, exist_ok=True)
    finish = ''
    if args.ui:
        finish = '''
 remove_trait = ac_cultivator
 remove_character_flag = ac_awakening_cooldown
 if = { limit = { NOT = { has_relation_friend = scope:ac_qa_teacher } } set_relation_friend = scope:ac_qa_teacher }
 set_variable = { name = ac_qa_ui_teacher value = scope:ac_qa_teacher }
 set_variable = { name = ac_qa_ui_prestige value = prestige }
 trigger_event = ac_awakening_qa.0002
'''
    event.write_text('''namespace = ac_awakening_qa
ac_awakening_qa.0001 = { type = character_event hidden = yes immediate = {
 save_scope_as = ac_qa_learner
''' + checks + '\n debug_log = "AC_AWAKENING_QA COMPLETE"\n' + finish + '''} }
ac_awakening_qa.0002 = {
 type = character_event
 theme = learning
 title = ac_awakening_qa_title
 desc = ac_awakening_qa_desc
 right_portrait = { character = scope:ac_qa_teacher }
 option = { name = ac_awakening_qa_close }
}
ac_awakening_qa.0003 = { type = character_event hidden = yes immediate = {
 if = {
  limit = { var:ac_qa_ui_teacher = { has_trait = ac_cultivator } has_character_flag = ac_awakening_cooldown prestige = { value = var:ac_qa_ui_prestige subtract = 100 } }
  debug_log = "AC_AWAKENING_QA PASS actual_request_spends_prestige_and_sets_cooldown"
 } else = { debug_log = "AC_AWAKENING_QA FAIL actual_request_spends_prestige_and_sets_cooldown" }
} }
''', encoding='utf-8-sig')
    gui = overlay / 'common/scripted_guis/ac_awakening_qa.txt'
    gui.parent.mkdir(parents=True, exist_ok=True)
    gui.write_text('''ac_awakening_qa_audit = { scope = character effect = { trigger_event = ac_awakening_qa.0003 } }
''', encoding='utf-8-sig')
    gui = overlay / 'gui/ac_awakening_qa.gui'
    gui.parent.mkdir(parents=True, exist_ok=True)
    gui.write_text('''window = { name = "ac_awakening_qa" layer = windows_layer
 parentanchor = bottom|hcenter size = { 340 40 } position = { 0 -45 }
 button_standard = { size = { 340 40 } raw_text = "Audit actual request (test only)"
 onclick = "[GetScriptedGui('ac_awakening_qa_audit').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]" }
}''', encoding='utf-8-sig')
    widget = overlay / 'gui/scripted_widgets/ac_awakening_qa.txt'
    widget.parent.mkdir(parents=True, exist_ok=True)
    widget.write_text('gui/ac_awakening_qa.gui = ac_awakening_qa\n' if args.ui else '', encoding='utf-8-sig')
    loc = overlay / 'localization/english/ac_awakening_qa_l_english.yml'
    loc.parent.mkdir(parents=True, exist_ok=True)
    loc.write_text('''l_english:
 ac_awakening_qa_title:0 "Cultivation Request QA"
 ac_awakening_qa_desc:0 "Click the teacher portrait to open their character panel, close this event, then right-click the teacher and send Request Cultivation Training. Use the audit button afterward."
 ac_awakening_qa_close:0 "Continue"
''', encoding='utf-8-sig')
    (OUT / 'mod').mkdir(parents=True, exist_ok=True)
    for name, directory in [('ac_awakening', ROOT / 'AuraClash'), ('ac_awakening_qa', overlay)]:
        (OUT / 'mod' / (name + '.mod')).write_text(
            f'name="{name}"\npath="{directory.as_posix()}"\nsupported_version="1.20.*"\n', encoding='utf-8')
    (OUT / 'dlc_load.json').write_text(json.dumps({
        'enabled_mods': ['mod/ac_awakening.mod', 'mod/ac_awakening_qa.mod'], 'disabled_dlcs': []}), encoding='utf-8')
    if not args.ui:
        event.write_text(event.read_text(encoding='utf-8-sig').split('ac_awakening_qa.0002 = {')[0], encoding='utf-8-sig')
        for relative in ('common/scripted_guis/ac_awakening_qa.txt', 'gui/ac_awakening_qa.gui'):
            (overlay / relative).write_text('', encoding='utf-8-sig')
    baseline = ROOT / 'output/sect-layout-ui'
    if not (OUT / 'pdx_settings.txt').exists() and (baseline / 'pdx_settings.txt').exists():
        shutil.copy2(baseline / 'pdx_settings.txt', OUT / 'pdx_settings.txt')
    if not (OUT / 'shadercache').exists() and (baseline / 'shadercache').exists():
        shutil.copytree(baseline / 'shadercache', OUT / 'shadercache')
    print(f'Prepared {OUT}. Launch with -debug_mode -skip -bookmark=bm_1066_hastings -play=k_england -userdir="{OUT}"')
    print('Require COMPLETE, no AC_SECT_QA FAIL, and no production script errors.')


if __name__ == '__main__':
    main()
