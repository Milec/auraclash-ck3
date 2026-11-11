"""Prepare disposable native CK3 checks for Mortal Limits, Aura Pressure, reveal and two-axis inheritance."""
from pathlib import Path
import json
import shutil
from build_potential import LIMITS, THRESHOLDS, XP
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
    for level, (limit, threshold, xp) in enumerate(zip(LIMITS, THRESHOLDS, XP), 1):
        effect(f'scope:ac_test_student = {{ set_variable = {{ name = ac_potential_limit_gene value = {level} }} set_variable = {{ name = ac_potential_talent_gene value = {level} }} ac_reveal_potential_effect = yes }}')
        check(f'scope:ac_test_student = {{ ac_mortal_limit_base = {limit} ac_mortal_limit = {limit} ac_potential_talent_xp_factor = {1+xp} has_trait_xp = {{ trait = ac_potential track = ac_potential_limit value = {threshold} }} has_trait_xp = {{ trait = ac_potential track = ac_potential_talent value = {threshold} }} }}')
    S = 'scope:ac_test_student = { '
    reset = ' '.join(f'add_trait_xp = {{ trait = ac_cultivator track = ac_core_{c} value = -100 }}' for c in ('soul','agility','power','fortitude'))
    clear = ' '.join(f'remove_variable = {v}' for v in ('ac_aura_pressure', 'ac_allocated_ap', 'ac_immortal_cores', 'ac_core_soul_progress', 'ac_core_agility_progress', 'ac_core_soul_spent'))
    # Earthly I limit (1,500 AP) and a 1.5x Talent keep every expected gain an integer.
    effect(S + 'set_variable = { name = ac_potential_limit_gene value = 4 } set_variable = { name = ac_potential_talent_gene value = 6 } ac_reveal_potential_effect = yes ' + reset + ' ' + clear + ' remove_trait = ac_immortal_core remove_trait = ac_immortal_method remove_trait = intellect_good_3 add_trait = ac_foundation_dragon remove_character_flag = ac_core_training_cooldown add_trait_xp = { trait = ac_cultivator track = ac_core_soul value = 35 } ac_init_aura_effect = yes }')
    check(S + 'ac_core_soul_rating = 7 ac_aura_pressure_value = 700 ac_allocated_ap_value = 700 ac_free_ap = 0 ac_mortal_limit = 1500 }')
    # Mortal training raises Cores until eight Mortal Cores in total; the yearly cooldown blocks a repeat.
    effect(S + 'ac_mortal_core_train_effect = { CORE = soul } ac_mortal_core_train_effect = { CORE = soul } }')
    check(S + 'ac_core_soul_rating = 8 ac_core_dots = 8 ac_aura_pressure_value = 715 ac_core_soul_progress = 10 has_character_flag = ac_core_training_cooldown }')
    effect(S + 'remove_character_flag = ac_core_training_cooldown ac_mortal_core_train_effect = { CORE = agility } }')
    check(S + 'ac_core_agility_rating = 0 ac_core_dots = 8 ac_aura_pressure_value = 730 ac_allocated_ap_value = 700 }')
    # The Immortal Core Method must be learned: from a master with a bond, a sect, or genius.
    effect('create_character = { age = 50 gender = female random_traits = no culture = root.culture faith = root.faith employer = root trait = ac_cultivator save_scope_as = ac_test_master } scope:ac_test_master = { add_trait = ac_immortal_core } ' + S + 'set_variable = { name = ac_aura_pressure value = 1000 } }')
    check(S + 'ac_immortal_method_requirements_trigger = yes ac_can_learn_immortal_method_trigger = yes NOT = { ac_immortal_method_master_trigger = { TEACHER = scope:ac_test_master } } ac_immortal_method_genius_trigger = no }')
    effect(S + 'set_relation_friend = scope:ac_test_master add_trait = intellect_good_3 }')
    check(S + 'ac_immortal_method_master_trigger = { TEACHER = scope:ac_test_master } ac_immortal_method_genius_trigger = yes }')
    effect(S + 'ac_learn_immortal_method_effect = yes }')
    check(S + 'has_trait = ac_immortal_method ac_knows_immortal_method_trigger = yes ac_can_learn_immortal_method_trigger = no }')
    # Binding AP requires Immortal Core Advancement; progress discounts the cost.
    effect(S + 'ac_advance_core_effect = { CORE = soul } }')
    check(S + 'ac_core_soul_rating = 8 ac_allocated_ap_value = 700 NOT = { ac_can_advance_core_trigger = { CORE = soul } } }')
    effect(S + 'add_trait = ac_immortal_core ac_advance_core_effect = { CORE = soul } }')
    check(S + 'ac_core_soul_rating = 9 ac_allocated_ap_value = 790 ac_core_soul_progress = 0 ac_free_ap = 210 ac_immortal_core_count = 1 ac_mortal_core_count = 8 has_trait_xp = { trait = ac_immortal_core track = ac_immortal_cores value = 1 } }')
    effect(S + 'ac_advance_core_effect = { CORE = soul } }')
    check(S + 'ac_core_soul_rating = 10 ac_allocated_ap_value = 890 ac_free_ap = 110 ac_immortal_core_count = 2 }')
    # Mortal Limit: halved above 1,500 AP, quartered above 2,250 AP.
    effect(S + 'set_variable = { name = ac_aura_pressure value = 1600 } ac_gain_aura_pressure_effect = { AP = 20 } }')
    check(S + 'ac_aura_pressure_value = 1615 }')
    effect(S + 'set_variable = { name = ac_aura_pressure value = 2300 } ac_gain_aura_pressure_effect = { AP = 40 } }')
    check(S + 'ac_aura_pressure_value = 2315 }')
    # Cycling Shards at 990 AP costs 100 gold and grants (16 + Soul 10) x 1.5 = 39 AP.
    effect(S + 'set_variable = { name = ac_aura_pressure value = 990 } add_gold = 500 set_variable = { name = ac_test_gold value = gold } ac_cycle_shards_effect = yes }')
    check(S + 'ac_aura_pressure_value = 1029 gold = { value = var:ac_test_gold subtract = 100 } }')
    # Surging spends a Core charge and earns progress; quarterly meditation restores it.
    effect(S + 'ac_surge_core_effect = { CORE = soul } }')
    check(S + 'ac_core_soul_available = 9 ac_core_soul_progress = 10 }')
    effect(S + 'ac_restore_cores_effect = yes }')
    check(S + 'ac_core_soul_available = 10 }')
    # Auto-advance binds 139 free AP: 90 (progress 10), leaving 49.
    effect(S + 'add_character_flag = ac_core_advance_auto set_variable = { name = ac_core_last_advanced value = flag:soul } ac_core_auto_advance_effect = yes }')
    check(S + 'ac_core_soul_rating = 11 ac_allocated_ap_value = 980 ac_free_ap = 49 ac_immortal_core_count = 3 }')
    # Seeded masters hold dozens of Immortal Cores: every Core beyond the eighth.
    effect('create_character = { age = 60 gender = male random_traits = no culture = root.culture faith = root.faith employer = root trait = ac_cultivator save_scope_as = ac_test_sect_master } scope:ac_test_sect_master = { ac_develop_master_effect = yes set_variable = { name = ac_test_expected_ap value = { value = ac_core_dots multiply = 100 } } }')
    check('scope:ac_test_sect_master = { has_trait = ac_immortal_core ac_core_dots >= 48 ac_immortal_core_count >= 40 ac_mortal_core_count = 8 ac_aura_pressure_value = var:ac_test_expected_ap ac_free_ap = 0 has_trait_xp = { trait = ac_immortal_core track = ac_immortal_cores value >= 40 } }')
    effect('create_character = { age = 30 gender = female random_traits = no culture = root.culture faith = root.faith employer = root trait = ac_cultivator save_scope_as = ac_test_upper } scope:ac_test_upper = { ac_develop_upper_effect = yes }')
    check('scope:ac_test_upper = { has_trait = ac_immortal_core ac_immortal_core_count >= 16 ac_immortal_core_count <= 32 }')
    # Techniques: learning grants passives, one Focus slot per Core, Chi pays for exertion.
    effect(S + 'ac_learn_tech_cleave_effect = yes ac_learn_tech_spiritwell_effect = yes }')
    check(S + 'has_character_flag = ac_tech_cleave ac_known_technique_count = 2 has_character_modifier = ac_tech_cleave_modifier ac_can_learn_tech_apex_hunter_trigger = no ac_core_power_surge_value = 2 }')
    effect(S + 'ac_focus_tech_cleave_effect = yes }')
    check(S + 'ac_core_power_surge_value = 3 }')
    effect(S + 'ac_focus_tech_spiritwell_effect = yes }')
    check(S + 'var:ac_focus_power = flag:spiritwell ac_core_power_surge_value = 3 }')
    effect(S + 'ac_restore_cores_effect = yes set_variable = { name = ac_test_chi value = { value = ac_chi_available subtract = 1 } } ac_event_exertion_effect = yes }')
    check(S + 'ac_chi_available = var:ac_test_chi NOT = { has_character_modifier = ac_event_chi_exertion_modifier } }')
    effect(S + 'ac_restore_cores_effect = yes }')

    effect(S + 'remove_character_flag = ac_core_advance_auto set_variable = { name = ac_potential_talent_gene value = 9 } ac_reveal_potential_effect = yes ac_gain_cultivation_study_xp_effect = { XP = 300 } }')
    check(S + 'ac_cultivation_lifestyle_xp = 250 ac_martial_styles_lifestyle_xp = 250 ac_elements_lifestyle_xp = 250 ac_aura_pressure_value = 1189 }')
    effect(S + 'remove_character_flag = ac_core_training_cooldown add_character_flag = ac_path_study_cooldown ac_ai_yearly_cultivation_effect = yes }')
    check(S + 'has_character_flag = ac_core_training_cooldown ac_aura_pressure_value > 1189 }')
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
    (ROOT / 'AuraClash/tests/ac_potential_tests.txt').write_text(source+'\n',encoding='utf-8-sig',newline='\n')
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
        if not (OUT/name).exists() and (baseline/name).exists():shutil.copy2(baseline/name,OUT/name)
    if not (OUT/'shadercache').exists() and (baseline/'shadercache').exists():shutil.copytree(baseline/'shadercache',OUT/'shadercache')
    print(f'Prepared {OUT}')


if __name__ == '__main__':main()
