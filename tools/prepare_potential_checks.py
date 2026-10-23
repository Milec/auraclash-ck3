"""Prepare disposable native CK3 checks for prices, reveal and two-axis inheritance."""
from pathlib import Path
import json
import shutil
from build_potential import BLOCKS, THRESHOLDS, XP
from prepare_sect_engine_checks import test_body

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/potential-runtime'


def fixture():
    lines = ['potential = { effect = { save_scope_as = ac_potential_test_host']
    for name, sex, age in [('student', 'male', 25), ('mother', 'female', 40), ('father', 'male', 40), ('child', 'male', 0)]:
        lines += [f'create_character = {{ age = {age} gender = {sex} random_traits = no culture = root.culture faith = root.faith employer = root save_scope_as = ac_test_{name} }}']
    lines += ['scope:ac_test_child = { set_mother = scope:ac_test_mother set_father = scope:ac_test_father } }']
    def effect(s): lines.append('effect = { ' + s + ' }')
    def check(s): lines.append('assert = { ' + s + ' }')
    effect('scope:ac_test_student = { ac_initialize_potential_effect = yes set_variable = { name = ac_test_saved_limit value = var:ac_potential_limit_gene } set_variable = { name = ac_test_saved_talent value = var:ac_potential_talent_gene } ac_initialize_potential_effect = yes }')
    check('scope:ac_test_student = { NOT = { has_trait = ac_potential } var:ac_potential_limit_gene = var:ac_test_saved_limit var:ac_potential_talent_gene = var:ac_test_saved_talent }')
    effect('scope:ac_test_student = { add_trait = ac_cultivator }')
    check('scope:ac_test_student = { has_trait = ac_potential var:ac_potential_limit_gene = var:ac_test_saved_limit var:ac_potential_talent_gene = var:ac_test_saved_talent }')
    effect('scope:ac_test_student = { remove_trait = ac_cultivator }')
    check('scope:ac_test_student = { NOT = { has_trait = ac_potential } }')
    effect('scope:ac_test_student = { add_trait = ac_cultivator ac_reveal_potential_effect = yes ac_reveal_potential_effect = yes }')
    check('scope:ac_test_student = { has_trait = ac_potential var:ac_potential_limit_gene = var:ac_test_saved_limit var:ac_potential_talent_gene = var:ac_test_saved_talent }')
    for level, (block, threshold, xp) in enumerate(zip(BLOCKS, THRESHOLDS, XP), 1):
        effect(f'scope:ac_test_student = {{ set_variable = {{ name = ac_potential_limit_gene value = {level} }} set_variable = {{ name = ac_potential_talent_gene value = {level} }} ac_reveal_potential_effect = yes }}')
        check(f'scope:ac_test_student = {{ ac_core_cost_interval = {block} ac_potential_talent_xp_factor = {1+xp} has_trait_xp = {{ trait = ac_potential track = ac_potential_limit value = {threshold} }} has_trait_xp = {{ trait = ac_potential track = ac_potential_talent value = {threshold} }} }}')
    # Full dot count across all tracks, including exact step boundaries.
    for dots in (0, 7, 8, 15, 16, 23, 24, 31, 32, 63, 64, 79, 80):
        effect('scope:ac_test_student = { set_variable = { name = ac_potential_limit_gene value = 1 } ac_reveal_potential_effect = yes ' + ' '.join(f'add_trait_xp = {{ trait = ac_cultivator track = ac_core_{c} value = -100 }} add_trait_xp = {{ trait = ac_cultivator track = ac_core_{c} value = {max(0,min(20,dots-i*20))*5} }}' for i,c in enumerate(('soul','agility','power','fortitude'))) + ' }')
        check(f'scope:ac_test_student = {{ ac_core_dots = {dots} ac_core_formation_cost = {100*(1+dots//8)} }}')
    # One actual purchase crossing a price band, then cooldown and insufficient-fund guards.
    effect('scope:ac_test_student = { '+ ' '.join(f'add_trait_xp = {{ trait = ac_cultivator track = ac_core_{c} value = -100 }}' for c in ('soul','agility','power','fortitude')) + ' add_trait_xp = { trait = ac_cultivator track = ac_core_soul value = 35 } add_prestige = { value = prestige multiply = -1 } add_prestige = 1000 remove_character_flag = ac_core_training_cooldown ac_train_core_effect = { CORE = soul } }')
    check('scope:ac_test_student = { prestige = 900 ac_core_dots = 8 ac_core_formation_cost = 200 has_character_flag = ac_core_training_cooldown }')
    effect('scope:ac_test_student = { ac_train_core_effect = { CORE = soul } }')
    check('scope:ac_test_student = { prestige = 900 ac_core_dots = 8 }')
    effect('scope:ac_test_student = { remove_character_flag = ac_core_training_cooldown add_prestige = -701 ac_train_core_effect = { CORE = soul } }')
    check('scope:ac_test_student = { prestige = 199 ac_core_dots = 8 NOT = { has_character_flag = ac_core_training_cooldown } }')
    effect('scope:ac_test_student = { set_variable = { name = ac_potential_talent_gene value = 9 } ac_reveal_potential_effect = yes ac_gain_cultivation_study_xp_effect = { XP = 300 } }')
    check('scope:ac_test_student = { ac_cultivation_lifestyle_xp = 250 ac_martial_styles_lifestyle_xp = 250 ac_elements_lifestyle_xp = 250 }')
    effect('scope:ac_test_student = { add_prestige = 1001 add_character_flag = ac_core_training_auto set_variable = { name = ac_core_last value = flag:soul } ac_core_auto_train_effect = yes }')
    check('scope:ac_test_student = { prestige = 1000 ac_core_dots = 9 }')
    effect('scope:ac_test_student = { remove_character_flag = ac_core_training_auto remove_character_flag = ac_core_training_cooldown add_character_flag = ac_path_study_cooldown ac_ai_yearly_cultivation_effect = yes }')
    check('scope:ac_test_student = { prestige = 800 ac_core_dots = 10 }')
    for parents, expected in [(1,4),(3,6),(4,7),(6,9),(9,9)]:
        effect(' '.join(f'scope:ac_test_{p} = {{ set_variable = {{ name = ac_potential_limit_gene value = {parents} }} set_variable = {{ name = ac_potential_talent_gene value = {parents} }} }}' for p in ('mother','father')) + ' scope:ac_test_child = { ac_reinforce_potential_limit_effect = yes ac_reinforce_potential_talent_effect = yes }')
        check(f'scope:ac_test_child = {{ var:ac_potential_limit_gene = {expected} var:ac_potential_talent_gene = {expected} NOT = {{ has_trait = ac_cultivator }} NOT = {{ has_trait = ac_potential }} }}')
    effect('scope:ac_test_child = { trigger_event = { on_action = ac_potential_birth } }')
    check('scope:ac_test_child = { var:ac_potential_limit_gene = 9 var:ac_potential_talent_gene = 9 NOT = { has_trait = ac_potential } }')
    effect('scope:ac_test_child = { add_trait = ac_cultivator }')
    check('scope:ac_test_child = { has_trait = ac_potential has_trait_xp = { trait = ac_potential track = ac_potential_limit value = 100 } has_trait_xp = { trait = ac_potential track = ac_potential_talent value = 100 } }')
    effect('scope:ac_test_child = { set_variable = { name = ac_test_mortal value = 0 } set_variable = { name = ac_test_earthly value = 0 } set_variable = { name = ac_test_heavenly value = 0 } while = { count = 10000 limit = { always = yes } ac_roll_potential_limit_effect = yes if = { limit = { var:ac_potential_limit_gene <= 3 } change_variable = { name = ac_test_mortal add = 1 } } else_if = { limit = { var:ac_potential_limit_gene <= 6 } change_variable = { name = ac_test_earthly add = 1 } } else = { change_variable = { name = ac_test_heavenly add = 1 } } } }')
    check('scope:ac_test_child = { var:ac_test_mortal >= 8000 var:ac_test_mortal <= 9200 var:ac_test_earthly >= 800 var:ac_test_earthly <= 1800 var:ac_test_heavenly >= 25 var:ac_test_heavenly <= 200 }')
    effect('scope:ac_test_mother = { set_variable = { name = ac_potential_limit_gene value = 1 } } scope:ac_test_father = { set_variable = { name = ac_potential_limit_gene value = 1 } } scope:ac_test_child = { set_variable = { name = ac_test_reinforced value = 0 } while = { count = 1000 limit = { always = yes } ac_inherit_potential_limit_effect = yes if = { limit = { var:ac_potential_limit_gene >= 4 var:ac_potential_limit_gene <= 6 } change_variable = { name = ac_test_reinforced add = 1 } } } }')
    check('scope:ac_test_child = { var:ac_test_reinforced >= 15 var:ac_test_reinforced <= 130 }')
    lines.append('}')
    return '\n'.join(lines)


def main():
    source = fixture()
    (ROOT / 'AuraClash/tests/ac_potential_tests.txt').write_text(source+'\n',encoding='utf-8-sig')
    checks = test_body('potential',source.replace('root.', 'scope:ac_potential_test_host.')).replace('title:k_england','scope:ac_potential_test_host')
    lifestyle = (ROOT/'AuraClash/tests/ac_lifestyle_tests.txt').read_text(encoding='utf-8-sig')
    checks += '\nsave_scope_as = ac_lifestyle_host\n' + test_body('potential_lifestyle_regression',lifestyle.replace('root.', 'scope:ac_lifestyle_host.')).replace('title:k_england','scope:ac_lifestyle_host')
    files = {
        'common/on_action/ac_potential_qa.txt': 'on_game_start_after_lobby = { on_actions = { ac_potential_qa } }\nac_potential_qa = { effect = { title:k_england.holder = { trigger_event = ac_potential_qa.0001 } } }',
        'events/ac_potential_qa.txt': 'namespace = ac_potential_qa\nac_potential_qa.0001 = { type = character_event hidden = yes immediate = {\n'+checks+'\ndebug_log = "AC_POTENTIAL_QA COMPLETE"\nadd_trait = ac_cultivator\nset_variable = { name = ac_potential_limit_gene value = 5 } set_variable = { name = ac_potential_talent_gene value = 8 } ac_reveal_potential_effect = yes\n} }',
    }
    overlay = OUT/'qa-mod'
    for relative,text in files.items():
        path=overlay/relative; path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8-sig')
    (OUT/'mod').mkdir(parents=True,exist_ok=True)
    for name,path in [('ac_potential',ROOT/'AuraClash'),('ac_potential_qa',overlay)]:
        (OUT/'mod'/f'{name}.mod').write_text(f'name="{name}"\npath="{path.as_posix()}"\nsupported_version="1.20.*"\n',encoding='utf-8')
    (OUT/'dlc_load.json').write_text(json.dumps({'enabled_mods':['mod/ac_potential.mod','mod/ac_potential_qa.mod'],'disabled_dlcs':[]}),encoding='utf-8')
    baseline=ROOT/'output/awakening-runtime'
    for name in ('pdx_settings.txt',):
        if not (OUT/name).exists():shutil.copy2(baseline/name,OUT/name)
    if not (OUT/'shadercache').exists():shutil.copytree(baseline/'shadercache',OUT/'shadercache')
    print(f'Prepared {OUT}')


if __name__ == '__main__':main()
