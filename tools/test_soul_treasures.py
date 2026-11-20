"""Soul Treasures and Advancement Elixirs, following the Aura Clash IF."""
from pathlib import Path
import unittest

import build_event_overrides as script
import build_soul_treasures as st

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


class SoulTreasureTests(unittest.TestCase):
    def test_generated_files_are_current_and_balanced(self):
        for relative, text in st.outputs().items():
            self.assertEqual((MOD / relative).read_bytes(), ('﻿' + text).encode('utf-8'), relative)
            if relative.endswith('.txt'):
                script.fields('{' + text + '}')

    def test_elixir_follows_the_if_formula(self):
        values = st.outputs()['common/script_values/ac_soul_treasure_values.txt']
        elixir = script.one('{' + values + '}', 'ac_soul_treasure_1_elixir').body('{' + values + '}')
        for needle in ('subtract = ac_aura_pressure_value', 'multiply = 0.11', 'max = 100', 'multiply = 3 add = 10'):
            self.assertIn(needle, elixir)
        effects = st.outputs()['common/scripted_effects/ac_soul_treasure_effects.txt']
        self.assertIn('ac_alchemy_rank >= 4', effects)
        self.assertIn('multiply = ac_mortal_limit_factor', effects)
        self.assertEqual(st.FISHBONE[3], 75)


if __name__ == '__main__':
    unittest.main()
