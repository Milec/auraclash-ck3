"""Guard independent cultivation pools and prerequisite-safe NPC spending."""
from pathlib import Path
import re
import unittest

import build_event_overrides as parser

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


class LifestyleTests(unittest.TestCase):
    def test_every_perk_belongs_to_its_discipline_and_parents_stay_in_that_pool(self):
        perks = {}
        for path in (MOD / 'common/lifestyle_perks').glob('ac_*_perks.txt'):
            text = path.read_text(encoding='utf-8-sig')
            for field in parser.fields('{' + text + '}'):
                body = field.body('{' + text + '}')
                lifestyle = re.search(r'\blifestyle = (\w+)', body)[1]
                expected = ('ac_martial_styles_lifestyle' if field.key.startswith('ac_3_') else
                            'ac_elements_lifestyle' if field.key.startswith('ac_4_') else
                            'ac_cultivation_lifestyle')
                self.assertEqual(lifestyle, expected, field.key)
                perks[field.key] = (lifestyle, re.findall(r'\bparent = (\w+)', body))
        self.assertEqual(len(perks), 150)
        for perk, (lifestyle, parents) in perks.items():
            for parent in parents:
                self.assertEqual(perks[parent][0], lifestyle, (perk, parent))

    def test_npc_grants_and_available_perks_match(self):
        text = (MOD / 'common/scripted_effects/ac_lifestyle_ai_perks.txt').read_text(encoding='utf-8-sig')
        for field in parser.fields('{' + text + '}'):
            body = field.body('{' + text + '}')
            expected = 'ac_3_' if 'style' in field.key else 'ac_4_' if 'element' in field.key else None
            grants = re.findall(r'\badd_perk = (\w+)', body)
            self.assertEqual(len(grants), 50 if expected == 'ac_3_' else 80 if expected == 'ac_4_' else 20)
            for grant in grants:
                if expected:
                    self.assertTrue(grant.startswith(expected), grant)
                else:
                    self.assertTrue(grant.startswith(('ac_1_', 'ac_2_')), grant)

    def test_focuses_cover_all_three_pools(self):
        text = (MOD / 'common/focuses/ac_cultivation_focuses.txt').read_text(encoding='utf-8-sig')
        self.assertCountEqual(re.findall(r'\blifestyle = (\w+)', text),
                              ['ac_cultivation_lifestyle', 'ac_martial_styles_lifestyle', 'ac_elements_lifestyle'])

    def test_lifestyle_and_focus_art_has_native_default_filenames(self):
        # CK3 uses the database key for these paths even when an icon override is set.
        for key in ('ac_cultivation_lifestyle', 'ac_martial_styles_lifestyle', 'ac_elements_lifestyle'):
            for folder in ('icons/lifestyles', 'illustrations/lifestyles_background'):
                self.assertTrue((MOD / 'gfx/interface' / folder / (key + '.dds')).is_file(), (folder, key))
        for key in ('ac_deep_meditation_focus', 'ac_physical_training_focus', 'ac_elemental_attunement_focus'):
            self.assertTrue((MOD / 'gfx/interface/icons/focuses' / (key + '.dds')).is_file(), key)

    def test_new_native_scripts_balance(self):
        for relative in ('common/lifestyles/ac_cultivation_lifestyle.txt',
                         'common/scripted_effects/ac_lifestyle_effects.txt',
                         'common/scripted_effects/ac_lifestyle_ai_perks.txt',
                         'tests/ac_lifestyle_tests.txt'):
            text = (MOD / relative).read_text(encoding='utf-8-sig')
            parser.fields('{' + text + '}')


if __name__ == '__main__':
    unittest.main()
