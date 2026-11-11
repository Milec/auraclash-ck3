"""Techniques, Focus slots, Chi Pool and Surge values, following the Aura Clash IF."""
from pathlib import Path
import re
import unittest

import build_event_overrides as script
import build_techniques as tech

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


class TechniqueTests(unittest.TestCase):
    def test_generated_files_are_current_and_balanced(self):
        for relative, text in tech.outputs().items():
            self.assertEqual((MOD / relative).read_bytes(), ('﻿' + text).encode('utf-8'), relative)
            if relative.endswith('.txt'):
                script.fields('{' + text + '}')

    def test_catalogue_follows_the_if(self):
        self.assertEqual(tech.MAX_KNOWN, 25)
        for key, (name, core, focus, passive, req, desc) in tech.CATALOGUE.items():
            self.assertIn(core, tech.CORES, key)
            self.assertIn(focus, ('surge', 'core', 'chi'), key)
        # Every Core has Techniques to Focus, plus its Innate Technique.
        for core in tech.CORES:
            self.assertTrue(any(v[1] == core for v in tech.CATALOGUE.values()), core)
            self.assertTrue(any(v[1] == core for v in tech.INNATE.values()), core)
        self.assertEqual({v[0] for v in tech.INNATE.values()}, {'Thunderfall', 'Iron Body', 'Flash Step', 'Energy Tide'})

    def test_one_focus_slot_per_core(self):
        effects = read('common/scripted_effects/ac_combat_technique_effects.txt')
        for key, value in tech.CATALOGUE.items():
            body = script.one('{' + effects + '}', f'ac_focus_tech_{key}_effect').body('{' + effects + '}')
            self.assertIn(f'ac_unfocus_{value[1]}_effect = yes', body)

    def test_chi_pool_surge_and_core_bonus_are_used(self):
        values = read('common/script_values/ac_combat_technique_values.txt')
        self.assertIn('value = ac_core_soul_rating\n\tdivide = 2', values)
        trials = read('events/ac_ascension_events.txt')
        self.assertIn('BONUS = ac_core_power_surge_value', trials)
        self.assertIn('BONUS = ac_core_agility_surge_value', trials)
        aura = read('common/script_values/ac_aura_values.txt')
        for core in tech.CORES:
            self.assertIn(f'add = ac_core_{core}_focus_bonus', aura)
        exertion = read('common/scripted_effects/ac_event_effects.txt')
        self.assertIn('ac_chi_available >= 1', exertion)
        self.assertIn('ac_spend_chi_effect', exertion)
        self.assertIn('remove_variable = ac_chi_spent', read('common/scripted_effects/ac_aura_effects.txt'))


if __name__ == '__main__':
    unittest.main()
