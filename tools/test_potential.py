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
        self.assertEqual(len(potential.LIMITS),9)
        self.assertEqual(len(potential.THRESHOLDS),9)
        self.assertEqual(potential.THRESHOLDS[-1],100)
        self.assertEqual(potential.LIMITS[0],800)  # Outer West's Mortal Limit in Aura Clash
        self.assertEqual(list(potential.LIMITS),sorted(set(potential.LIMITS)))

    def test_mortal_limit_values_are_generated_for_each_grade(self):
        values=potential.outputs()['common/script_values/ac_potential_values.txt']
        for limit in potential.LIMITS:
            self.assertIn(f'value = {limit} }}',values)
        self.assertNotIn('ac_core_formation_cost',values)

    def test_generated_content_is_current_and_parses(self):
        for relative,expected in potential.outputs().items():
            source=(ROOT/'AuraClash'/relative).read_text(encoding='utf-8-sig')
            self.assertEqual(source,expected,relative)
            if relative.endswith('.txt'):
                script.fields('{'+source+'}')

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
