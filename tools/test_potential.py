"""Check Potential's generated balance table and production integrations."""
from pathlib import Path
import unittest
import build_potential as potential
import build_event_overrides as script

ROOT = Path(__file__).resolve().parents[1]


class PotentialTests(unittest.TestCase):
    def test_distribution_and_innate_ranges(self):
        self.assertEqual(sum(potential.WEIGHTS),1000)
        self.assertEqual(sum(potential.WEIGHTS[:3]),860)
        self.assertEqual(sum(potential.WEIGHTS[3:6]),130)
        self.assertEqual(sum(potential.WEIGHTS[6:]),10)
        self.assertEqual(len(potential.BLOCKS),9)
        self.assertEqual(len(potential.THRESHOLDS),9)
        self.assertEqual(potential.THRESHOLDS[-1],100)
        self.assertEqual(potential.BLOCKS[0],8)
        self.assertEqual(list(potential.BLOCKS),sorted(potential.BLOCKS))

    def test_price_boundaries_and_limit_advantage(self):
        for level,interval in enumerate(potential.BLOCKS):
            prices=[100*(1+dots//interval) for dots in range(81)]
            self.assertEqual(prices[interval-1],100)
            self.assertEqual(prices[interval],200)
            self.assertEqual(prices[2*interval],300)
            if level:
                self.assertTrue(all(price<=100*(1+dots//potential.BLOCKS[level-1]) for dots,price in enumerate(prices)))

    def test_generated_content_is_current_and_parses(self):
        for relative,expected in potential.outputs().items():
            source=(ROOT/'AuraClash'/relative).read_text(encoding='utf-8-sig')
            self.assertEqual(source,expected,relative)
            if relative.endswith('.txt'):
                script.fields('{'+source+'}')

    def test_all_paid_paths_use_shared_cost_and_free_seed_progress_remains(self):
        effects=(ROOT/'AuraClash/common/scripted_effects/ac_cultivation_effects.txt').read_text(encoding='utf-8-sig')
        training=next(f.body('{'+effects+'}') for f in script.fields('{'+effects+'}') if f.key=='ac_train_core_effect')
        self.assertIn('ac_can_train_core_trigger = { CORE = $CORE$ }',training)
        self.assertIn('add_prestige = { value = ac_core_formation_cost multiply = -1 }',training)
        self.assertLess(training.index('add_prestige'),training.index('add_trait_xp'))
        self.assertIn('prestige >= { value = ac_core_formation_cost add = 200 }',effects)
        trigger=(ROOT/'AuraClash/common/scripted_triggers/ac_cultivation_triggers.txt').read_text(encoding='utf-8-sig')
        self.assertIn('prestige >= ac_core_formation_cost',trigger)

    def test_genes_are_distinct_from_cultivation_and_track_xp(self):
        output=potential.outputs()
        effects=output['common/scripted_effects/ac_potential_effects.txt']
        self.assertNotIn('add_trait = ac_cultivator',effects)
        self.assertIn('exists = real_father',effects)
        self.assertNotIn('scope:father',effects)
        self.assertIn('ac_revealing_potential',effects)
        self.assertIn('NOT = { has_variable = ac_potential_limit_gene }',effects)
        self.assertIn('NOT = { has_variable = ac_potential_talent_gene }',effects)

    def test_only_new_rewards_receive_talent_multiplier(self):
        source=(ROOT/'AuraClash/common/scripted_effects/ac_lifestyle_effects.txt').read_text(encoding='utf-8-sig')
        self.assertEqual(source.count('multiply = ac_potential_talent_xp_factor'),3)
        migration=next(f.body('{'+source+'}') for f in script.fields('{'+source+'}') if f.key=='ac_migrate_cultivation_lifestyles_effect')
        self.assertNotIn('multiply',migration)


if __name__=='__main__':unittest.main()
