"""Guard the awakening routes that the isolated native fixture exercises."""
from pathlib import Path
import re
import unittest

import build_event_overrides as parser

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


def block(source, key):
    wrapped = '{' + source + '}'
    return next(field.body(wrapped) for field in parser.fields(wrapped) if field.key == key)


class AwakeningTests(unittest.TestCase):
    def test_access_and_ambition_are_distinct_routes_with_a_shared_attempt(self):
        decisions = read('common/decisions/ac_cultivation_decisions.txt')
        normal = block(decisions, 'ac_awaken_cultivation_decision')
        seeking = block(decisions, 'ac_seek_cultivation_decision')
        self.assertIn('ac_has_cultivation_access_trigger = yes', block(normal, 'is_valid_showing_failures_only'))
        self.assertIn('has_trait = ambitious', block(seeking, 'is_valid_showing_failures_only'))
        for decision in (normal, seeking):
            self.assertIn('ac_awakening_ready_trigger = yes', block(decision, 'is_valid_showing_failures_only'))
            self.assertIn('ac_attempt_awakening_effect = yes', block(decision, 'effect'))
        self.assertEqual(dict(re.findall(r'(gold|prestige|piety)\s*=\s*(\d+)', block(seeking, 'cost'))),
                         {'gold': '100', 'prestige': '250', 'piety': '250'})

    def test_fame_and_random_creation_do_not_bypass_access(self):
        effect = block(read('common/scripted_effects/ac_cultivation_effects.txt'), 'ac_fame_cultivation_effect')
        self.assertIn('has_trait = ac_cultivator', block(block(effect, 'if'), 'limit'))
        self.assertNotIn('add_trait = ac_cultivator', effect)
        trait = block(read('common/traits/ac_cultivation_traits.txt'), 'ac_cultivator')
        self.assertRegex(trait, r'\bbirth = 0\b')
        self.assertRegex(trait, r'\brandom_creation = 0\b')

    def test_training_does_not_use_court_or_vassal_status_as_access(self):
        interaction = read('common/character_interactions/ac_train_cultivation_interaction.txt')
        self.assertIn('ac_can_receive_cultivation_training_trigger', interaction)
        self.assertNotIn('is_courtier_of', interaction)
        self.assertNotIn('is_vassal_or_below_of', interaction)
        self.assertNotIn('is_child_of', interaction)

    def test_mod_on_action_references_have_definitions(self):
        sources = [parser.masked(path.read_text(encoding='utf-8-sig'))
                   for path in (MOD / 'common/on_action').glob('*.txt')]
        definitions = set(re.findall(r'(?m)^\s*(ac_\w+)\s*=\s*\{', '\n'.join(sources)))
        for source in sources:
            for body in re.findall(r'\bon_actions\s*=\s*\{([^{}]*)\}', source):
                for key in re.findall(r'\bac_\w+\b', body):
                    self.assertIn(key, definitions)

    def test_new_scripts_balance_and_localization_is_present(self):
        for relative in ('common/scripted_triggers/ac_awakening_triggers.txt',
                         'common/scripted_effects/ac_awakening_effects.txt',
                         'tests/ac_awakening_tests.txt'):
            depth = 0
            for char in parser.masked(read(relative)):
                depth += (char == '{') - (char == '}')
                self.assertGreaterEqual(depth, 0, relative)
            self.assertEqual(depth, 0, relative)
        loc = read('localization/english/ac_cultivation_l_english.yml')
        for key in ('ac_awakening_access_tt', 'ac_awakening_cooldown_tt',
                    'ac_seek_cultivation_decision', 'ac_seek_cultivation_decision_desc',
                    'ac_seek_cultivation_decision_tooltip', 'ac_seek_cultivation_decision_confirm'):
            self.assertRegex(loc, rf'(?m)^ {key}:0 "')


if __name__ == '__main__':
    unittest.main()
