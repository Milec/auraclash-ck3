"""Static checks for Aura Pressure and Combat Cores (Mortal and Immortal Core Advancement)."""
from pathlib import Path
import re
import unittest

import build_event_overrides as script

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'
CORES = ('soul', 'agility', 'power', 'fortitude')


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


def block(source, key):
    wrapped = '{' + source + '}'
    return next(f.body(wrapped) for f in script.fields(wrapped) if f.key == key)


class AuraTests(unittest.TestCase):
    def setUp(self):
        self.values = read('common/script_values/ac_aura_values.txt')
        self.effects = read('common/scripted_effects/ac_aura_effects.txt')
        self.triggers = read('common/scripted_triggers/ac_aura_triggers.txt')

    def test_files_balance(self):
        for relative in ('common/script_values/ac_aura_values.txt', 'common/scripted_effects/ac_aura_effects.txt',
                         'common/scripted_triggers/ac_aura_triggers.txt', 'events/ac_cultivation_events.txt',
                         'common/decisions/ac_cultivation_decisions.txt', 'tests/ac_potential_tests.txt'):
            script.fields('{' + read(relative) + '}')

    def test_prestige_no_longer_buys_cores(self):
        for path in MOD.rglob('*.txt'):
            text = path.read_text(encoding='utf-8-sig')
            for stale in ('ac_core_formation_cost', 'ac_core_cost_interval', 'ac_train_core_effect', 'ac_can_train_core_trigger'):
                self.assertNotIn(stale, text, f'{stale} in {path}')

    def test_advancement_costs_100_less_progress_and_needs_immortal_core(self):
        for core in CORES:
            self.assertIn(f'ac_core_{core}_advance_cost = {{ value = ac_ap_per_core_dot subtract = ac_core_{core}_progress min = 0 }}', self.values)
        trigger = block(self.triggers, 'ac_can_advance_core_trigger')
        self.assertIn('has_trait = ac_immortal_core', trigger)
        self.assertIn('ac_free_ap >= ac_core_$CORE$_advance_cost', trigger)
        effect = block(self.effects, 'ac_advance_core_effect')
        self.assertLess(effect.index('change_variable = { name = ac_allocated_ap'), effect.index('add = -100'))

    def test_mortal_limit_halves_then_quarters(self):
        gain = block(self.values, 'ac_ap_gain_multiplier')
        self.assertIn('multiply = 1.5', gain)
        self.assertIn('multiply = 0.25', gain)
        self.assertIn('multiply = 0.5', gain)
        self.assertLess(gain.index('multiply = 0.25'), gain.index('multiply = 0.5'))
        self.assertIn('ac_mortal_limit = { value = ac_mortal_limit_base add = ac_mortal_limit_region_bonus }', self.values)

    def test_mortal_training_caps_and_immortal_core_requires_ap(self):
        self.assertIn('ac_mortal_core_cap = 3', self.values)
        self.assertIn('ac_immortal_core_ap_requirement = 300', self.values)
        decisions = read('common/decisions/ac_cultivation_decisions.txt')
        self.assertIn('ac_aura_pressure_value >= ac_immortal_core_ap_requirement', block(decisions, 'ac_immortal_core_advancement_decision'))
        self.assertIn('ac_aura_pressure_value >= ac_immortal_core_ap_requirement', read('common/scripted_effects/ac_cultivation_effects.txt'))
        self.assertIn('trigger_event = ac_cult.0005', block(decisions, 'ac_advance_core_decision'))
        self.assertIn('gold >= ac_shard_cycle_cost', block(decisions, 'ac_cycle_shards_decision'))

    def test_progress_sources_are_hooked(self):
        actions = read('common/on_action/ac_cultivation_on_actions.txt')
        self.assertIn('ac_battle_core_progress_effect', actions)
        self.assertIn('ac_aura_yearly_pulse', actions)
        self.assertIn('ac_restore_cores_effect = yes', actions)
        self.assertIn('ac_hunt_core_progress', read('common/on_action/ac_hunt_on_actions.txt'))
        self.assertIn('ac_gain_aura_pressure_effect', read('common/scripted_effects/ac_lifestyle_effects.txt'))

    def test_trials_surges_spend_cores(self):
        events = read('events/ac_ascension_events.txt')
        self.assertEqual(len(re.findall(r'ac_surge_core_effect = \{ CORE = \w+ \}', events)), 4)

    def test_localization_present(self):
        loc = '\n'.join(p.read_text(encoding='utf-8-sig') for p in (MOD / 'localization/english').glob('*.yml'))
        keys = set(k for pair in re.findall(r'\b(?:text|custom_tooltip|title|desc|selection_tooltip|confirm_text)\s*=\s*(ac_[\w.]+)|\bname\s*=\s*(ac_\w+\.[\w.]+)',
                              self.effects + self.triggers + read('events/ac_cultivation_events.txt') + read('common/decisions/ac_cultivation_decisions.txt')) for k in pair if k)
        keys |= {'ac_advance_core_decision', 'ac_cycle_shards_decision', 'ac_ascend.0010.surge'}
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {re.escape(key)}:\d+ "', key)


if __name__ == '__main__':
    unittest.main()
