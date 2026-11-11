"""Static checks for the Heavenly Ascension Trials and the Archonate."""
from pathlib import Path
import re
import unittest

import build_event_overrides as parser

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


class AscensionTests(unittest.TestCase):
    def setUp(self):
        self.events = read('events/ac_ascension_events.txt')
        self.loc = read('localization/english/ac_ascension_l_english.yml')

    def test_files_balance(self):
        for relative in ('events/ac_ascension_events.txt', 'common/scripted_effects/ac_ascension_effects.txt',
                         'common/scripted_triggers/ac_ascension_triggers.txt', 'common/script_values/ac_ascension_values.txt',
                         'common/on_action/ac_ascension_on_actions.txt', 'common/traits/ac_archonate_traits.txt'):
            parser.fields(read(relative))

    def test_every_scheduled_event_exists(self):
        sources = '\n'.join(read(p) for p in ('events/ac_ascension_events.txt', 'common/scripted_effects/ac_ascension_effects.txt'))
        defined = set(re.findall(r'(?m)^(ac_ascend\.\d+) = \{', self.events))
        for target in set(re.findall(r'\bac_ascend\.\d+', sources)):
            self.assertIn(target, defined)

    def test_localization_is_present(self):
        keys = set(re.findall(r'\b(?:title|desc|name|custom_tooltip)\s*=\s*(ac_[\w.]+)', self.events))
        keys |= {'trait_ac_archonate_disciple', 'trait_ac_archonate_disciple_desc'}
        for key in keys:
            self.assertRegex(self.loc, rf'(?m)^ {re.escape(key)}:0 "', key)

    def test_three_zodiac_trials_scored_zero_to_seven_with_an_eighth_point(self):
        for trial in ('tiger', 'rabbit', 'dragon'):
            self.assertIn(f'TRIAL = {trial}', self.events)
        values = read('common/script_values/ac_ascension_values.txt')
        self.assertIn('ac_trial_max_score = 7', values)
        effects = read('common/scripted_effects/ac_ascension_effects.txt')
        score = parser.one('{' + effects + '}', 'ac_trial_score_effect').body('{' + effects + '}')
        self.assertIn('value = 8', score)
        self.assertIn('has_variable = ac_trial_impressed', score)
        # Tiger tests Power/Fortitude, Rabbit Agility/Soul, Dragon measures Aura Pressure.
        self.assertIn('ac_core_power_rating', values.split('ac_trial_tiger_base')[1].split('}')[0])
        self.assertIn('ac_core_agility_rating', values.split('ac_trial_rabbit_base')[1].split('}')[0])
        self.assertIn('ac_aura_pressure_value', values.split('ac_trial_dragon_base')[1].split('ac_trial_grip')[0])

    def test_draft_eligibility_and_five_land_favor(self):
        values = read('common/script_values/ac_ascension_values.txt')
        self.assertIn('ac_ascension_max_age = 24', values)
        trigger = read('common/scripted_triggers/ac_ascension_triggers.txt')
        self.assertIn('exists = dynasty', trigger)
        for land in ('bladed', 'sacred', 'mystic', 'cursed', 'wild'):
            self.assertIn(f'ac_favor_impress_effect = {{ LAND = {land} }}', self.events)
            self.assertRegex(self.loc, rf'(?m)^ ac_favor_{land}_up_tt:0 "')
            self.assertRegex(self.loc, rf'(?m)^ ac_eighth_point_{land}:0 "')
        self.assertNotIn('gold >= ac_ascension_entry_gold', self.events)

    def test_admission_is_guarded_and_cleaned_up(self):
        effects = read('common/scripted_effects/ac_ascension_effects.txt')
        self.assertIn('NOT = { has_trait = ac_archonate_disciple }', effects)
        self.assertIn('ac_ascension_finish_effect = yes', self.events)
        self.assertIn('ac_ascension_total >= ac_ascension_pass_total', self.events)
        self.assertIn('yearly_global_pulse = { on_actions = { ac_ascension_yearly } }', read('common/on_action/ac_ascension_on_actions.txt'))


if __name__ == '__main__':
    unittest.main()
