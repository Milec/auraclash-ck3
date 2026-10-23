"""Prepare an isolated game exercising awakening access and real decision costs."""
from pathlib import Path
import json
import shutil

from prepare_sect_engine_checks import test_body

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/awakening-runtime'


def main():
    overlay = OUT / 'qa-mod'
    startup = overlay / 'common/on_action/ac_awakening_qa.txt'
    startup.parent.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'AuraClash/tests/ac_awakening_tests.txt').read_text(encoding='utf-8-sig')
    body = source
    # The shared harness normally runs in title scope; these tests use a character.
    checks = test_body('awakening', body.replace('root.', 'scope:ac_qa_learner.')).replace('title:k_england', 'scope:ac_qa_learner')
    startup.write_text('''on_game_start_after_lobby = { on_actions = { ac_awakening_qa } }
ac_awakening_qa = { effect = { title:k_england.holder = { trigger_event = ac_awakening_qa.0001 } } }
''', encoding='utf-8-sig')
    event = overlay / 'events/ac_awakening_qa.txt'
    event.parent.mkdir(parents=True, exist_ok=True)
    event.write_text('''namespace = ac_awakening_qa
ac_awakening_qa.0001 = { type = character_event hidden = yes immediate = {
 save_scope_as = ac_qa_learner
''' + checks + '\n debug_log = "AC_AWAKENING_QA COMPLETE"\n} }\n', encoding='utf-8-sig')
    (OUT / 'mod').mkdir(parents=True, exist_ok=True)
    for name, directory in [('ac_awakening', ROOT / 'AuraClash'), ('ac_awakening_qa', overlay)]:
        (OUT / 'mod' / (name + '.mod')).write_text(
            f'name="{name}"\npath="{directory.as_posix()}"\nsupported_version="1.20.*"\n', encoding='utf-8')
    (OUT / 'dlc_load.json').write_text(json.dumps({
        'enabled_mods': ['mod/ac_awakening.mod', 'mod/ac_awakening_qa.mod'], 'disabled_dlcs': []}), encoding='utf-8')
    baseline = ROOT / 'output/sect-layout-ui'
    if not (OUT / 'pdx_settings.txt').exists() and (baseline / 'pdx_settings.txt').exists():
        shutil.copy2(baseline / 'pdx_settings.txt', OUT / 'pdx_settings.txt')
    if not (OUT / 'shadercache').exists() and (baseline / 'shadercache').exists():
        shutil.copytree(baseline / 'shadercache', OUT / 'shadercache')
    print(f'Prepared {OUT}. Launch with -debug_mode -skip -bookmark=bm_1066_hastings -play=k_england -userdir="{OUT}"')
    print('Require COMPLETE, no AC_SECT_QA FAIL, and no production script errors.')


if __name__ == '__main__':
    main()
