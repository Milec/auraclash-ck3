"""Prepare native XP, perk spending, save-compatibility and lifestyle UI checks."""
from pathlib import Path
import json
import shutil

from prepare_sect_engine_checks import test_body

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/lifestyle-runtime'


def main():
    overlay = OUT / 'qa-mod'
    source = (ROOT / 'AuraClash/tests/ac_lifestyle_tests.txt').read_text(encoding='utf-8-sig')
    checks = test_body('lifestyles', source.replace('root.', 'scope:ac_lifestyle_host.'))
    checks = checks.replace('title:k_england', 'scope:ac_lifestyle_host')
    files = {
        'common/on_action/ac_lifestyle_qa.txt': '''
on_game_start_after_lobby = { on_actions = { ac_lifestyle_qa } }
ac_lifestyle_qa = { effect = { title:k_england.holder = { trigger_event = ac_lifestyle_qa.0001 } } }
''',
        'events/ac_lifestyle_qa.txt': '''namespace = ac_lifestyle_qa
ac_lifestyle_qa.0001 = { type = character_event hidden = yes immediate = {
save_scope_as = ac_lifestyle_host
''' + checks + '''
debug_log = "AC_LIFESTYLE_QA COMPLETE"
add_trait = ac_style_akakiru
add_trait = ac_element_water
add_trait = ac_element_wind
add_ac_cultivation_lifestyle_perk_points = 3
add_ac_martial_styles_lifestyle_perk_points = 3
add_ac_elements_lifestyle_perk_points = 3
set_variable = { name = ac_ui_craft_before value = ac_cultivation_lifestyle_perk_points }
set_variable = { name = ac_ui_style_before value = ac_martial_styles_lifestyle_perk_points }
set_variable = { name = ac_ui_element_before value = ac_elements_lifestyle_perk_points }
} }
ac_lifestyle_qa.0002 = { type = character_event hidden = yes immediate = {
 if = {
  limit = {
   has_perk = ac_4_element_water_a_perk
   ac_elements_lifestyle_perk_points = { value = var:ac_ui_element_before subtract = 1 }
   ac_cultivation_lifestyle_perk_points = var:ac_ui_craft_before
   ac_martial_styles_lifestyle_perk_points = var:ac_ui_style_before
  }
  debug_log = "AC_LIFESTYLE_UI PASS element_purchase_uses_only_its_own_pool"
 } else = { debug_log = "AC_LIFESTYLE_UI FAIL element_purchase_uses_only_its_own_pool" }
} }
''',
        'common/scripted_guis/ac_lifestyle_qa.txt': '''
ac_lifestyle_qa_audit = { scope = character effect = { trigger_event = ac_lifestyle_qa.0002 } }
''',
        'gui/ac_lifestyle_qa.gui': '''window = { name = "ac_lifestyle_qa" layer = windows_layer
 parentanchor = bottom|hcenter size = { 340 35 } position = { 0 -10 }
 button_standard = { size = { 340 35 } raw_text = "Audit Elements purchase (QA only)"
 onclick = "[GetScriptedGui('ac_lifestyle_qa_audit').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]" }
}''',
        'gui/scripted_widgets/ac_lifestyle_qa.txt': 'gui/ac_lifestyle_qa.gui = ac_lifestyle_qa\n',
    }
    for relative, text in files.items():
        path = overlay / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8-sig')
    (OUT / 'mod').mkdir(parents=True, exist_ok=True)
    for name, path in [('ac_lifestyle', ROOT / 'AuraClash'), ('ac_lifestyle_qa', overlay)]:
        (OUT / 'mod' / (name + '.mod')).write_text(
            f'name="{name}"\npath="{path.as_posix()}"\nsupported_version="1.20.*"\n', encoding='utf-8')
    (OUT / 'dlc_load.json').write_text(json.dumps({
        'enabled_mods': ['mod/ac_lifestyle.mod', 'mod/ac_lifestyle_qa.mod'], 'disabled_dlcs': []}), encoding='utf-8')
    baseline = ROOT / 'output/awakening-runtime'
    if not (OUT / 'pdx_settings.txt').exists():
        shutil.copy2(baseline / 'pdx_settings.txt', OUT / 'pdx_settings.txt')
    if not (OUT / 'shadercache').exists():
        shutil.copytree(baseline / 'shadercache', OUT / 'shadercache')
    print(f'Prepared {OUT}. Launch -debug_mode -skip -bookmark=bm_1066_hastings -play=k_england -userdir="{OUT}"')
    print('Require COMPLETE, no failed assertions and no script errors. Inspect all three tabs and buy Healing Waters, then use the audit button.')


if __name__ == '__main__':
    main()
