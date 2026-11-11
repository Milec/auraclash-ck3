"""The Clash of Auras: a turn-based cultivator duel."""
import re
import unittest

import build_duels as duels
import build_event_overrides as script


class DuelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = duels.render()
        cls.text = {k: v.decode('utf-8-sig') for k, v in cls.files.items()}

    def test_committed_output_is_current(self):
        for relative, data in self.files.items():
            self.assertEqual((duels.OUT / relative).read_bytes(), data, relative)

    def test_scripts_balance(self):
        for relative, text in self.text.items():
            if relative.endswith('.txt'):
                script.fields(text)

    def test_moves_form_a_counter_cycle(self):
        beats = {move: beat for move, _, beat, _ in duels.MOVES}
        self.assertEqual(sorted(beats.values()), sorted(beats))
        self.assertTrue(all(beats[beats[m]] != m for m in beats))

    def test_references_resolve(self):
        effects = self.text['common/scripted_effects/ac_duel_effects.txt']
        rest = effects + self.text['events/ac_duel_events.txt'] + self.text['common/character_interactions/ac_duel_interactions.txt']
        defined = set(re.findall(r'(?m)^(ac_duel_\w+_effect) = \{', effects))
        self.assertLessEqual(set(re.findall(r'\b(ac_duel_\w+_effect) = (?:yes|\{)', rest)), defined)
        values = self.text['common/script_values/ac_duel_values.txt']
        self.assertLessEqual(set(re.findall(r'\b(ac_duel_\w+(?:_base|_vitality|_part|_techniques))\b', rest)),
                             set(re.findall(r'(?m)^(ac_duel_\w+) = ', values)))
        base = '\n'.join(p.read_text(encoding='utf-8-sig') for p in (duels.OUT / 'common').rglob('ac_*.txt'))
        for helper in ('ac_surge_core_effect', 'ac_spend_chi_effect', 'ac_add_core_progress_effect', 'ac_core_power_surge_value',
                       'ac_chi_available', 'ac_aura_pressure_value', 'ac_core_soul_rating'):
            self.assertRegex(base, rf'(?m)^{helper} = ', helper)

    def test_attack_techniques_can_be_unleashed(self):
        self.assertGreaterEqual(len(duels.ATTACKS), 10)
        self.assertIn('cleave', duels.ATTACKS)
        effects = self.text['common/scripted_effects/ac_duel_effects.txt']
        triggers = self.text['common/scripted_triggers/ac_duel_triggers.txt']
        for key, (_, core) in duels.ATTACKS.items():
            self.assertIn(f'has_character_flag = ac_tech_{key} }} set_variable = {{ name = ac_duel_move value = flag:{duels.CORE_MOVE[core]} }}', effects)
            self.assertIn(f'ac_duel_first_attack_{key}_trigger = {{', triggers)
        used = set(re.findall(r'\b(ac_duel_\w+_trigger) = yes', effects + self.text['events/ac_duel_events.txt']))
        self.assertLessEqual(used, set(re.findall(r'(?m)^(ac_duel_\w+_trigger) = \{', triggers)))

    def test_localization(self):
        loc = self.text['localization/english/ac_duel_l_english.yml']
        rest = self.text['events/ac_duel_events.txt'] + self.text['common/character_interactions/ac_duel_interactions.txt']
        keys = set(re.findall(r'\b(?:title|desc|custom_tooltip|localization)\s*=\s*(ac_(?:duel|challenge)[\w.]*)', rest))
        keys |= set(re.findall(r'\bname\s*=\s*(ac_duel\.[\w.]+)', rest))
        keys |= set(re.findall(r'\btext\s*=\s*(ac_duel\.[\w.]+)', rest))
        keys.add('ac_challenge_duel_interaction')
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {re.escape(key)}:0 "', key)


if __name__ == '__main__':
    unittest.main()
