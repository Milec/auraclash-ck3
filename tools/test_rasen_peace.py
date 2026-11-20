from pathlib import Path
import unittest

import build_rasen_peace as peace

ROOT = Path(__file__).resolve().parents[1]


class PeaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {k: v.decode('utf-8-sig') for k, v in peace.render().items()}

    def test_generated_files_are_current(self):
        for relative, text in self.text.items():
            self.assertEqual((peace.OUT / relative).read_text(encoding='utf-8-sig'), text, relative)

    def test_the_peace_is_the_default_celestial_law_and_only_the_hegemon_may_lift_it(self):
        groups = self.text['common/law_groups/rasen_peace_law_groups.txt']
        laws = self.text['common/laws/rasen_peace_laws.txt']
        self.assertIn('required_government_flag = { government_is_celestial }', groups)
        self.assertIn('default = rasen_council_peace_law', groups)
        peace_law = laws[:laws.index('rasen_council_war_law = {')]
        self.assertIn(f'flag = {peace.PEACE_FLAG}', peace_law)
        lifted = laws[laws.index('rasen_council_war_law = {'):]
        self.assertNotIn(peace.PEACE_FLAG, lifted)
        self.assertIn('this = title:h_china.holder', lifted)
        loc = self.text['localization/english/rasen_peace_l_english.yml']
        for key in ('rasen_peace_laws', 'rasen_council_peace_law', 'rasen_council_war_law', 'rasen_azuma_protected_tt'):
            self.assertIn(f' {key}:0 "', loc)

    def test_the_rules_patch_vanilla_war_triggers(self):
        hook, azuma, governors = peace.PEACE_EDITS
        self.assertIn(f"NOT = {{ has_realm_law_flag = {peace.PEACE_FLAG} }}", governors[1])
        # Great lords need a hook on their liege; counts are exempt.
        self.assertIn(f'top_liege = {{ has_realm_law_flag = {peace.PEACE_FLAG} }}', hook[1])
        self.assertIn('highest_held_title_tier >= tier_duchy', hook[1])
        self.assertIn('scope:recipient = { highest_held_title_tier >= tier_duchy }', hook[1])
        self.assertIn('geographical_region = world_rasen_azuma', azuma[1])
        patched = ROOT / 'AuraClash/common/scripted_triggers/00_war_and_peace_triggers.txt'
        if patched.exists():
            text = patched.read_text(encoding='utf-8-sig')
            self.assertIn(hook[1], text)
            self.assertIn(azuma[1], text)


if __name__ == '__main__':
    unittest.main()
