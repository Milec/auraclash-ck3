"""The Exalted Council: five Inner Kingdom seats voting on decrees, and Trial patronage."""
import re
import unittest

import build_event_overrides as script
import build_rasen_council as council


class CouncilTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = council.render()
        cls.text = {k: v.decode('utf-8-sig') for k, v in cls.files.items()}

    def test_committed_output_is_current(self):
        for relative, data in self.files.items():
            self.assertEqual((council.OUT / relative).read_bytes(), data, relative)

    def test_scripts_balance(self):
        for relative, text in self.text.items():
            if relative.endswith('.txt'):
                script.fields(text)

    def test_every_seat_votes_and_every_decree_is_enacted(self):
        effects = self.text['common/scripted_effects/rasen_council_effects.txt']
        for land, decree, *_ in council.LANDS:
            # Exalts hold no land: each seat is a global variable, refilled from the land when it falls vacant.
            self.assertIn(f'global_var:rasen_exalt_{land} = {{', effects)
            self.assertIn(f'rasen_exalt_candidate_trigger = {{ LAND = {land} }}', effects)
            self.assertIn(f'modifier = {{ add = global_var:rasen_votes_{land} }}', effects)
            self.assertIn(f'rasen_decree_{decree}_effect = {{', effects)
        self.assertNotIn('title:k_bladed', effects)
        seat = effects[effects.index('rasen_seat_exalt_effect = {'):]
        self.assertIn('create_noble_family_effect = { GOVERNMENT_GIVER = title:h_china.holder }', seat)
        self.assertIn(f'subtract = {council.EXALT_TERM_YEARS}', effects)

    def test_effects_and_events_resolve(self):
        effects = self.text['common/scripted_effects/rasen_council_effects.txt']
        events = self.text['events/rasen_council_events.txt']
        defined = set(re.findall(r'(?m)^(rasen_\w+_effect) = \{', effects))
        used = set(re.findall(r'\b(rasen_\w+_effect) = yes', effects + events))
        self.assertLessEqual(used, defined)
        event_ids = set(re.findall(r'(?m)^(rasen_council\.\d{4}) = \{', events))
        self.assertLessEqual(set(re.findall(r'(rasen_council\.\d{4})', effects)), event_ids)
        opinions = set(re.findall(r'(?m)^(\w+_opinion) = \{', self.text['common/opinion_modifiers/rasen_council_opinions.txt']))
        self.assertLessEqual(set(re.findall(r'modifier = (rasen_\w+_opinion)', effects + events)), opinions)
        # The base mod's Trials and Path Manual hooks that the Council relies on.
        base = (council.ROOT / 'AuraClash/common/scripted_effects/ac_ascension_effects.txt').read_text(encoding='utf-8-sig')
        self.assertIn('ac_favor_change_effect = {', base)
        values = (council.ROOT / 'AuraClash/common/script_values/ac_combat_technique_values.txt').read_text(encoding='utf-8-sig')
        self.assertIn('has_global_variable = rasen_archives_open', values)

    def test_localization(self):
        events = self.text['events/rasen_council_events.txt']
        loc = self.text['localization/english/rasen_council_l_english.yml']
        script_text = events + self.text['common/scripted_effects/rasen_council_effects.txt']
        keys = set(re.findall(r'\b(?:title|desc|custom_tooltip)\s*=\s*(rasen_[\w.]+)', script_text))
        keys |= set(re.findall(r'\bname\s*=\s*(rasen_council\.[\w.]+)', script_text))
        keys |= set(re.findall(r'(?m)^(rasen_\w+) = \{', self.text['common/modifiers/rasen_council_modifiers.txt']))
        keys |= set(re.findall(r'(?m)^(rasen_\w+) = \{', self.text['common/opinion_modifiers/rasen_council_opinions.txt']))
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {re.escape(key)}:0 "', key)


if __name__ == '__main__':
    unittest.main()
