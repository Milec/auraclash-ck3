"""Invariants accompanying the native population/rank fixture."""
from pathlib import Path
import re
import unittest

from build_cultivation_population import PROFILES

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


class PopulationTests(unittest.TestCase):
    def test_strength_ranges_are_ordered_and_respect_existing_track_caps(self):
        previous = -1
        for name in ('upper', 'master', 'grandmaster'):
            cores, foundation = PROFILES[name]
            self.assertGreater(min(cores), previous)
            self.assertLessEqual(max(cores), 100)
            self.assertTrue(all(x % 5 == 0 for x in cores + foundation))
            previous = max(cores)
        self.assertTrue(all(50 <= x < 75 for x in PROFILES['upper'][1]))
        self.assertTrue(all(75 <= x < 100 for x in PROFILES['master'][1]))
        self.assertEqual(PROFILES['grandmaster'][1], (100,))

    def test_all_existing_rank_transition_sites_apply_the_baseline(self):
        for relative in ('common/scripted_effects/ac_sect_core_effects.txt',
                         'common/scripted_effects/ac_sect_trial_effects.txt',
                         'common/character_interactions/ac_sect_interactions.txt',
                         'events/ac_sect_events.txt'):
            source = (MOD / relative).read_text(encoding='utf-8-sig')
            matches = list(re.finditer(r'add_trait = ac_sect_(?:master|upper_disciple)\b', source))
            self.assertTrue(matches, relative)
            for match in matches:
                self.assertIn('ac_sect_develop_rank_effect = yes', source[match.end():match.end() + 350], relative)
        source = (MOD / 'common/scripted_effects/ac_sect_identity_effects.txt').read_text(encoding='utf-8-sig')
        self.assertIn('ac_sect_develop_rank_effect = yes', source)

    def test_migration_and_replacement_have_persistent_guards(self):
        actions = (MOD / 'common/on_action/ac_roaming_on_actions.txt').read_text(encoding='utf-8-sig')
        self.assertIn('has_global_variable = ac_sects_initialized', actions)
        self.assertIn('NOT = { has_global_variable = ac_cultivation_population_v1 }', actions)
        self.assertIn('yearly_global_pulse', actions)
        roaming = (MOD / 'common/scripted_effects/ac_roaming_master_effects.txt').read_text(encoding='utf-8-sig')
        self.assertIn('NOT = { var:ac_roaming_master ?= { is_alive = yes } }', roaming)
        self.assertIn('is_pool_character = yes', roaming)
        self.assertIn('NOT = { has_variable = ac_sect }', roaming)
        self.assertNotIn('change_title_holder', roaming)
        self.assertNotIn('set_government', roaming)


if __name__ == '__main__':
    unittest.main()
