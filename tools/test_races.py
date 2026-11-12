"""Races of Aura Clash: Human, Oni, Lunargoth, Kitsune and five Yokai lineages (IF racial bonuses)."""
from pathlib import Path
import re
import unittest

import build_event_overrides as script

MOD = Path(__file__).resolve().parents[1]


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


class RaceTests(unittest.TestCase):
    def test_races_are_exclusive_and_localized(self):
        traits = read('AuraClash/common/traits/ac_race_traits.txt')
        script.fields(traits)
        keys = re.findall(r'(?m)^(ac_race_\w+) = \{', traits)
        self.assertEqual(len(keys), 9)
        loc = read('AuraClash/localization/english/ac_race_l_english.yml')
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ trait_{key}:0 "')
        # IF racial bonuses: Lore (Human), Deception (Oni), Craft (Lunargoth).
        body = lambda key: script.one('{' + traits + '}', key).body('{' + traits + '}')
        self.assertIn('learning = 1', body('ac_race_human'))
        self.assertIn('intrigue = 1', body('ac_race_oni'))
        self.assertIn('stewardship = 1', body('ac_race_lunargoth'))

    def test_inheritance_assignment_and_fox_charm(self):
        self.assertIn('ac_inherit_race_effect', read('AuraClash/common/on_action/ac_race_on_actions.txt'))
        self.assertIn('culture = culture:oni', read('AuraClash/common/scripted_effects/rasen_race_effects.txt'))
        self.assertIn("'has_trait = ac_race_kitsune'", read('tools/build_techniques.py'))
        chars = read('AuraClash/history/characters/rasen_characters.txt')
        self.assertEqual(chars.count('trait = ac_race_'), len(re.findall(r'(?m)^rasen_\d+ = \{', chars)))


if __name__ == '__main__':
    unittest.main()
