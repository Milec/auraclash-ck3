"""Castes of Imperial Rasen (Noble, Warrior, Merchant, Laborer/Clanless), following the IF."""
from pathlib import Path
import unittest

import build_event_overrides as script

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


class CasteTests(unittest.TestCase):
    def test_castes_follow_clans(self):
        triggers = read('common/scripted_triggers/ac_caste_triggers.txt')
        script.fields(triggers)
        body = lambda key: script.one('{' + triggers + '}', key).body('{' + triggers + '}')
        self.assertIn('exists = dynasty', body('ac_caste_noble_trigger'))
        self.assertIn('NOT = { exists = dynasty }', body('ac_caste_laborer_trigger'))
        self.assertIn('has_character_flag = ac_elevated_warrior_caste', body('ac_caste_warrior_trigger'))

    def test_trials_require_warrior_caste_and_elevation_exists(self):
        self.assertIn('ac_warrior_caste_or_above_trigger = yes', read('common/scripted_triggers/ac_ascension_triggers.txt'))
        interaction = read('common/character_interactions/ac_caste_interactions.txt')
        script.fields(interaction)
        self.assertIn('add_character_flag = ac_elevated_warrior_caste', interaction)
        self.assertIn('ac_warrior_caste_or_above_trigger = yes', read('common/script_values/ac_conduct_values.txt'))


if __name__ == '__main__':
    unittest.main()
