"""The Ice Incursions of Outer North (Imperial Rasen content)."""
from pathlib import Path
import re
import unittest

import build_event_overrides as script

ROOT = Path(__file__).resolve().parents[1] / 'AuraClash'
FILES = ('common/on_action/rasen_ice_incursion_on_actions.txt', 'common/scripted_effects/rasen_ice_incursion_effects.txt',
         'common/scripted_triggers/rasen_ice_incursion_triggers.txt', 'common/modifiers/rasen_ice_incursion_modifiers.txt',
         'common/script_values/rasen_ice_incursion_values.txt', 'events/rasen_ice_incursion_events.txt', 'common/traits/rasen_traits.txt')


def read(relative):
    return (ROOT / relative).read_text(encoding='utf-8-sig')


class IceIncursionTests(unittest.TestCase):
    def test_files_balance(self):
        for relative in FILES:
            script.fields(read(relative))

    def test_generational_cycle_and_region(self):
        effects = read('common/scripted_effects/rasen_ice_incursion_effects.txt')
        self.assertIn('value = 20 }', effects)
        self.assertIn('value = 30 }', effects)
        self.assertIn('region = world_rasen_outer_north', effects)
        self.assertIn('world_rasen_outer_north = {', read('map_data/geographical_regions/rasen_geographical_regions.txt'))

    def test_events_and_localization(self):
        events = read('events/rasen_ice_incursion_events.txt')
        sources = events + read('common/scripted_effects/rasen_ice_incursion_effects.txt')
        defined = set(re.findall(r'(?m)^(rasen_ice\.\d+) = \{', events))
        self.assertLessEqual(set(re.findall(r'\brasen_ice\.\d{4}\b', sources)), defined)
        loc = read('localization/english/rasen_ice_incursion_l_english.yml')
        keys = set(re.findall(r'\b(?:title|desc|custom_tooltip)\s*=\s*(rasen_[\w.]+)', sources))
        keys |= set(re.findall(r'\bname\s*=\s*(rasen_\w+\.[\w.]+)', sources))
        keys |= {'trait_rasen_divine_general', 'rasen_ice_incursion_county_modifier', 'rasen_ice_war_veteran_modifier'}
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {re.escape(key)}:0 "', key)

    def test_divine_general_rules_in_the_north(self):
        chars = read('history/characters/rasen_characters.txt')
        self.assertIn('trait = rasen_divine_general', chars)
        self.assertIn('culture = lunargoth', chars)


if __name__ == '__main__':
    unittest.main()
