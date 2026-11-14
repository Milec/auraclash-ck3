"""Static checks for childhood chi nurture and the coming-of-age Spark of Chi."""
from pathlib import Path
import re
import unittest

import build_event_overrides as parser

MOD = Path(__file__).resolve().parents[1] / 'AuraClash'
FILES = ('common/scripted_triggers/ac_childhood_triggers.txt',
         'common/scripted_effects/ac_childhood_effects.txt',
         'common/script_values/ac_childhood_values.txt',
         'events/ac_childhood_events.txt',
         'tests/ac_childhood_tests.txt')


def read(relative):
    return (MOD / relative).read_text(encoding='utf-8-sig')


def block(source, key):
    wrapped = '{' + source + '}'
    return next(field.body(wrapped) for field in parser.fields(wrapped) if field.key == key)


class ChildhoodTests(unittest.TestCase):
    def test_scripts_balance(self):
        for relative in FILES:
            parser.fields(read(relative))  # raises on unbalanced braces

    def test_birthday_hooks_are_appended(self):
        actions = read('common/on_action/ac_cultivation_on_actions.txt')
        self.assertRegex(actions, r'on_birthday\s*=\s*\{\s*on_actions\s*=\s*\{\s*ac_childhood_nurture_pulse ac_childhood_spark_pulse\s*\}')
        self.assertIn('ac_childhood_nurture_effect = yes', block(actions, 'ac_childhood_nurture_pulse'))
        self.assertIn('ac_childhood_spark_effect = yes', block(actions, 'ac_childhood_spark_pulse'))

    def test_mentor_must_be_guardian_or_present_parent(self):
        mentor = block(read('common/scripted_triggers/ac_childhood_triggers.txt'), 'ac_childhood_mentor_trigger')
        self.assertIn('ac_cultivation_teacher_trigger = yes', mentor)
        self.assertIn('has_relation_guardian = $MENTOR$', mentor)
        self.assertIn('location = $MENTOR$.location', mentor)
        self.assertNotIn('is_courtier_of', mentor)

    def test_spark_is_free_shares_cooldown_and_consumes_nurture(self):
        effects = read('common/scripted_effects/ac_childhood_effects.txt')
        spark = block(effects, 'ac_childhood_awakening_effect')
        self.assertIn('flag = ac_awakening_cooldown years = 1', spark)
        self.assertIn('remove_variable = ac_chi_nurture', spark)
        self.assertNotRegex(spark, r'add_(prestige|piety|gold)\s*=')
        self.assertIn('increase_wounds_no_death_effect', spark)
        values = read('common/script_values/ac_childhood_values.txt')
        self.assertIn('max = 95', block(values, 'ac_childhood_awaken_success_chance'))
        eligible = block(read('common/scripted_triggers/ac_childhood_triggers.txt'), 'ac_childhood_spark_eligible_trigger')
        self.assertIn('ac_awakening_ready_trigger = yes', eligible)

    def test_event_localization_is_present(self):
        events = read('events/ac_childhood_events.txt')
        loc = read('localization/english/ac_childhood_l_english.yml')
        keys = set(re.findall(r'\b(?:title|desc|name|custom_tooltip)\s*=\s*(ac_[\w.]+)', events))
        keys |= set(re.findall(r'custom_tooltip\s*=\s*(ac_\w+)', read('common/scripted_effects/ac_childhood_effects.txt')))
        self.assertTrue(keys)
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {re.escape(key)}:0 "', key)
        for event in ('ac_child.0001', 'ac_child.0010'):
            start = events.index(event + ' = {')
            body = events[start:parser.close_brace(events, events.index('{', start))]
            self.assertIn('\ttrigger =', body, event)


if __name__ == '__main__':
    unittest.main()
