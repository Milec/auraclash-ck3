"""Create a disposable CK3 startup fixture for rank development and roamers."""
from pathlib import Path
import json
import shutil

from build_cultivation_population import CORES
from prepare_sect_engine_checks import test_body

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/cultivation-population-runtime'


def core_range(low, high):
    return ' '.join(f'has_trait_xp = {{ trait = ac_cultivator track = ac_core_{core} value >= {low} }} '
                    f'NOT = {{ has_trait_xp = {{ trait = ac_cultivator track = ac_core_{core} value > {high} }} }}'
                    for core in CORES)


def main():
    overlay = OUT / 'qa-mod'
    source = ['population = { effect = { save_scope_as = ac_population_test_host']
    for name in ('upper', 'strong', 'grandmaster'):
        source += [f'''create_character = {{ age = 40 gender_female_chance = 50
        culture = root.culture faith = root.faith location = root.location
        trait = ac_cultivator trait = ac_foundation_snake trait = ac_style_aoyusumu
        trait = ac_element_light trait = ac_element_water save_scope_as = ac_test_{name} }}''']
    source += ['scope:ac_test_upper = { add_trait = ac_sect_upper_disciple ac_sect_develop_rank_effect = yes } }',
               f'assert = {{ scope:ac_test_upper = {{ {core_range(30, 50)} ac_foundation_xp_trigger = {{ XP = 50 }} NOT = {{ ac_foundation_xp_trigger = {{ XP = 75 }} }} }} }}',
               'assert = { scope:ac_test_upper = { has_trait = ac_foundation_snake has_trait = ac_style_aoyusumu has_trait = ac_element_light has_trait = ac_element_water ac_element_count = 2 } }',
               'effect = { scope:ac_test_upper = { set_variable = { name = ac_test_dots value = ac_core_dots } ac_sect_develop_rank_effect = yes } }',
               'assert = { scope:ac_test_upper = { ac_core_dots = var:ac_test_dots } }',
               'effect = { scope:ac_test_upper = { remove_trait = ac_sect_upper_disciple add_trait = ac_sect_master ac_sect_develop_rank_effect = yes } }',
               f'assert = {{ scope:ac_test_upper = {{ {core_range(60, 80)} has_trait = ac_immortal_core ac_foundation_xp_trigger = {{ XP = 75 }} NOT = {{ ac_foundation_xp_trigger = {{ XP = 100 }} }} }} }}',
               'effect = { scope:ac_test_upper = { set_variable = { name = ac_test_dots value = ac_core_dots } ac_sect_develop_rank_effect = yes } }',
               'assert = { scope:ac_test_upper = { ac_core_dots = var:ac_test_dots } }',
               'effect = { scope:ac_test_strong = { add_trait = ac_sect_master']
    for core in CORES:
        source += [f'add_trait_xp = {{ trait = ac_cultivator track = ac_core_{core} value = 95 }}']
    source += ['ac_gain_foundation_xp_effect = { XP = 100 } ac_sect_develop_rank_effect = yes } }',
               f'assert = {{ scope:ac_test_strong = {{ {core_range(95, 95)} ac_foundation_xp_trigger = {{ XP = 100 }} }} }}',
               'effect = { scope:ac_test_grandmaster = { ac_develop_grandmaster_effect = yes } }',
               f'assert = {{ scope:ac_test_grandmaster = {{ {core_range(85, 100)} ac_foundation_xp_trigger = {{ XP = 100 }} has_trait = ac_immortal_core }} }}',
               # Check actual founders and roster, not only synthetic profiles.
               '''effect = { set_global_variable = { name = ac_population_invalid value = 0 }
                 every_in_global_list = { variable = ac_sects
                  story_owner = { if = { limit = { NOT = { has_trait_xp = { trait = ac_cultivator track = ac_core_soul value >= 60 } ac_foundation_xp_trigger = { XP = 75 } } } change_global_variable = { name = ac_population_invalid add = 1 } } }
                  every_in_list = { variable = ac_members limit = { has_trait = ac_sect_upper_disciple }
                   if = { limit = { NOT = { has_trait_xp = { trait = ac_cultivator track = ac_core_power value >= 30 } ac_foundation_xp_trigger = { XP = 50 } } } change_global_variable = { name = ac_population_invalid add = 1 } }
                  }
                 }
               }''',
               'assert = { global_var:ac_population_invalid = 0 any_in_global_list = { variable = ac_sects count >= 10 } }',
               '''effect = { set_global_variable = { name = ac_population_invalid value = 0 }
                every_kingdom = { limit = { ac_roaming_origin_eligible_trigger = yes }
                 if = { limit = { NOT = { var:ac_roaming_master ?= { is_alive = yes has_trait = ac_roaming_master has_trait = ac_cultivator NOT = { has_variable = ac_sect } ac_element_count = 2 ac_has_martial_style_trigger = yes } } } change_global_variable = { name = ac_population_invalid add = 1 } }
                }
               }''',
               'assert = { global_var:ac_population_invalid = 0 any_in_global_list = { variable = ac_roaming_masters count >= 10 } }',
               'effect = { set_global_variable = { name = ac_population_invalid value = 0 } every_in_global_list = { variable = ac_roaming_masters']
    for grade, low, high, foundation in ((1, 30, 50, 50), (2, 60, 80, 75), (3, 85, 100, 100)):
        source += [f'''if = {{ limit = {{ var:ac_roaming_grade = {grade} NOT = {{ {core_range(low, high)} ac_foundation_xp_trigger = {{ XP = {foundation} }} }} }} change_global_variable = {{ name = ac_population_invalid add = 1 }} }}''']
    source += ['} }', 'assert = { global_var:ac_population_invalid = 0 }',
               '''effect = {
                 title:k_wales.var:ac_roaming_master = { save_scope_as = ac_test_original_roamer }
                 scope:ac_population_test_host = { add_courtier = scope:ac_test_original_roamer }
                 ac_roaming_world_maintenance_effect = yes
               }''',
               'assert = { title:k_wales.var:ac_roaming_master = scope:ac_test_original_roamer scope:ac_test_original_roamer = { is_courtier_of = scope:ac_population_test_host } }',
               'effect = { scope:ac_test_original_roamer = { death = natural } ac_roaming_world_maintenance_effect = yes }',
               'assert = { NOT = { title:k_wales.var:ac_roaming_master = scope:ac_test_original_roamer } title:k_wales.var:ac_roaming_master = { is_alive = yes has_trait = ac_roaming_master } NOT = { any_in_global_list = { variable = ac_roaming_masters is_alive = no } } }',
               '}']
    # Diagnose world-distribution metadata individually as well as in aggregate.
    diagnostics = []
    for label, condition in (
        ('living', 'is_alive = yes'), ('role', 'has_trait = ac_roaming_master'),
        ('cultivator', 'has_trait = ac_cultivator'),
        ('independent', 'NOT = { has_variable = ac_sect }'),
        ('elements', 'ac_element_count = 2'), ('style', 'ac_has_martial_style_trigger = yes')):
        diagnostics += [f'''effect = {{ debug_log = "AC_POPULATION_CHECK {label}"
          set_global_variable = {{ name = ac_population_invalid value = 0 }}
          every_kingdom = {{ limit = {{ ac_roaming_origin_eligible_trigger = yes }}
           if = {{ limit = {{ NOT = {{ var:ac_roaming_master ?= {{ {condition} }} }} }}
            change_global_variable = {{ name = ac_population_invalid add = 1 }}
           }}
          }}
        }}''', 'assert = { global_var:ac_population_invalid = 0 }']
    diagnostics += ['assert = { any_in_global_list = { variable = ac_roaming_masters count >= 10 OR = { is_pool_character = yes is_pool_guest = yes } } }']
    source[-1:-1] = diagnostics
    checks = test_body('population', '\n'.join(source))
    (overlay / 'common/on_action/ac_population_qa.txt').unlink(missing_ok=True)
    startup = overlay / 'common/on_action/zz_ac_population_qa.txt'
    startup.parent.mkdir(parents=True, exist_ok=True)
    startup.write_text('''on_game_start_after_lobby = { on_actions = { ac_population_qa } }
ac_population_qa = { effect = { title:k_england.holder = { trigger_event = { id = ac_population_qa.0001 days = 1 } } } }
''', encoding='utf-8-sig')
    event = overlay / 'events/ac_population_qa.txt'
    event.parent.mkdir(parents=True, exist_ok=True)
    event.write_text('namespace = ac_population_qa\nac_population_qa.0001 = { type = character_event hidden = yes immediate = {\n'
                     + checks + '\n debug_log = "AC_POPULATION_QA COMPLETE"\n} }\n', encoding='utf-8-sig')
    (OUT / 'mod').mkdir(parents=True, exist_ok=True)
    for name, path in [('ac_population', ROOT / 'AuraClash'), ('ac_population_qa', overlay)]:
        (OUT / 'mod' / (name + '.mod')).write_text(f'name="{name}"\npath="{path.as_posix()}"\nsupported_version="1.20.*"\n', encoding='utf-8')
    (OUT / 'dlc_load.json').write_text(json.dumps({'enabled_mods': ['mod/ac_population.mod', 'mod/ac_population_qa.mod'], 'disabled_dlcs': []}), encoding='utf-8')
    baseline = ROOT / 'output/awakening-runtime'
    if not (OUT / 'pdx_settings.txt').exists():
        shutil.copy2(baseline / 'pdx_settings.txt', OUT / 'pdx_settings.txt')
    if not (OUT / 'shadercache').exists():
        shutil.copytree(baseline / 'shadercache', OUT / 'shadercache')
    print('Unpause the disposable game for one day so native pool caches are initialized.')
    print(f'Prepared {OUT}. Launch with -debug_mode -skip -bookmark=bm_1066_hastings -play=k_england -userdir="{OUT}"')


if __name__ == '__main__':
    main()
