"""Honor and Ruthless (0-100, start 50) and their Style harmonies, following the IF."""
from pathlib import Path
import unittest

import build_event_overrides as script

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


class ConductTests(unittest.TestCase):
    def test_scales_start_at_fifty_and_are_clamped(self):
        values = read('common/script_values/ac_conduct_values.txt')
        self.assertIn('ac_honor_value = { value = 50', values)
        self.assertIn('ac_ruthless_value = { value = 50', values)
        effects = read('common/scripted_effects/ac_conduct_effects.txt')
        script.fields(effects)
        for stat in ('honor', 'ruthless'):
            body = script.one('{' + effects + '}', f'ac_change_{stat}_effect').body('{' + effects + '}')
            self.assertIn(f'var:ac_{stat} > 100', body)
            self.assertIn(f'var:ac_{stat} < 0', body)

    def test_if_style_harmonies_feed_aura_pressure(self):
        values = read('common/script_values/ac_conduct_values.txt')
        for needle in ('ac_style_akakiru ac_honor_value >= 70', 'ac_style_aoyusumu ac_ruthless_value <= 30',
                       'ac_element_light ac_ruthless_value <= 35', 'ac_element_fire ac_ruthless_value >= 75'):
            self.assertIn(needle, values)
        self.assertIn('add = ac_conduct_ap_harmony', read('common/script_values/ac_aura_values.txt'))

    def test_trial_judgements_move_conduct(self):
        effects = read('common/scripted_effects/ac_conduct_effects.txt')
        for land in ('bladed', 'sacred', 'mystic', 'cursed', 'wild'):
            self.assertIn(f'ac_conduct_from_land_{land}_effect = {{', effects)
        self.assertIn('ac_conduct_from_land_$LAND$_effect = yes', read('common/scripted_effects/ac_ascension_effects.txt'))


if __name__ == '__main__':
    unittest.main()
