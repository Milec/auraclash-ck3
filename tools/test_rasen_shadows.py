"""The Akuma Lords and Ryugujo (chapter 9 of the IF), and the canon cast that seeds them."""
import re
import unittest

import build_event_overrides as script
import build_rasen_shadows as shadows
import build_rasen_world as world


class ShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = shadows.render()
        cls.text = {k: v.decode('utf-8-sig') for k, v in cls.files.items()}
        cls.all = '\n'.join(cls.text.values())

    def test_committed_output_is_current(self):
        for relative, data in self.files.items():
            self.assertEqual((shadows.OUT / relative).read_bytes(), data, relative)

    def test_scripts_balance(self):
        for relative, text in self.text.items():
            if relative.endswith('.txt'):
                script.fields(text)

    def test_references_resolve(self):
        effects = self.text['common/scripted_effects/rasen_shadow_effects.txt']
        events = self.text['events/rasen_shadow_events.txt']
        council = (shadows.OUT / 'common/scripted_triggers/rasen_council_triggers.txt').read_text(encoding='utf-8-sig')
        defined = set(re.findall(r'(?m)^(rasen_\w+_effect) = \{', effects))
        self.assertLessEqual(set(re.findall(r'\b(rasen_\w+_effect) = yes', effects + events)), defined)
        self.assertIn('rasen_is_exalt_trigger = {', council)
        ids = set(re.findall(r'(?m)^(rasen_shadows\.\d{4}) = \{', events))
        self.assertLessEqual(set(re.findall(r'(rasen_shadows\.\d{4})', effects)), ids)
        traits = set(re.findall(r'(?m)^(rasen_\w+) = \{', self.text['common/traits/rasen_shadow_traits.txt']))
        for canon in world.CANON_CAST:
            for trait in canon['traits']:
                if trait.startswith('rasen_'):
                    self.assertIn(trait, traits, canon['key'])

    def test_localization(self):
        loc = self.text['localization/english/rasen_shadows_l_english.yml']
        keys = set(re.findall(r'\b(?:title|desc|name)\s*=\s*(rasen_shadows\.[\w.]+)', self.text['events/rasen_shadow_events.txt']))
        for relative in ('common/modifiers/rasen_shadow_modifiers.txt', 'common/secret_types/rasen_secret_types.txt'):
            keys |= set(re.findall(r'(?m)^(rasen_\w+) = \{', self.text[relative]))
        keys |= {'trait_' + t for t in re.findall(r'(?m)^(rasen_\w+) = \{', self.text['common/traits/rasen_shadow_traits.txt'])}
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {re.escape(key)}:0 "', key)


class CanonCastTests(unittest.TestCase):
    def test_keiko_is_the_bladed_exalts_daughter_at_his_court(self):
        chars = (world.OUT / 'history/characters/rasen_characters.txt').read_text(encoding='utf-8-sig')
        titles = (world.OUT / 'history/titles/rasen_titles.txt').read_text(encoding='utf-8-sig')
        masaru = re.search(r'(?ms)^k_bladed = \{.*?holder = (rasen_\d+)', titles).group(1)
        self.assertRegex(chars, rf'(?m)^{masaru} = \{{\n\tname = "Masaru"')
        keiko = re.search(r'(?ms)^rasen_\d+ = \{\n\tname = "Keiko"(.*?)^\}', chars).group(1)
        self.assertIn(f'father = {masaru}', keiko)
        self.assertIn('mother = rasen_', keiko)
        self.assertIn(f'employer = {masaru}', keiko)
        self.assertIn('dynasty = dynasty_rasen_ryuuzan', keiko)

    def test_the_cult_is_seeded(self):
        chars = (world.OUT / 'history/characters/rasen_characters.txt').read_text(encoding='utf-8-sig')
        self.assertEqual(chars.count('trait = rasen_akuma_lord'), 3)
        self.assertIn('culture = ryugujin', chars)
        self.assertEqual(chars.count('rasen_join_akuma_effect = yes'), sum(1 for c in world.CANON_CAST if c.get('akuma')))


if __name__ == '__main__':
    unittest.main()
