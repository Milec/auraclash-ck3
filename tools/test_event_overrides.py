"""Regression checks for option preservation, fatal gates and mod references.

These checks inspect CK3 scripts; they do not replace an in-game playtest.
"""
import json
from pathlib import Path
import re
import unittest

import build_event_overrides as builder
from event_option_specs import LOCALIZATION, SPECS


def normalized(text):
    return re.sub(r'\s+', '', builder.masked(text))


def event_from_file(path, event_id):
    text = path.read_text(encoding='utf-8-sig')
    match = re.search(r'^' + re.escape(event_id) + r'\s*=\s*\{', text, re.M)
    assert match, event_id
    return text[match.start():builder.close_brace(text, text.index('{', match.start()))]


class ScriptParserTests(unittest.TestCase):
    def test_braces_in_text_and_comments_are_not_structure(self):
        text = 'test.1 = {\n desc = "A { and escaped \\" bracket" # }\n option = { name = first nested = { value = 1 } }\n\toption = { name = second }\n after = { }\n}'
        self.assertEqual([field.key for field in builder.fields(text)], ['option', 'option', 'after'])

    def test_unbalanced_scripts_are_rejected(self):
        with self.assertRaises(ValueError):
            builder.fields('test.1 = { option = { }')


class EventRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vanilla = {}
        cls.generated = {}
        for event_id, group, options in SPECS:
            cls.vanilla[event_id] = builder.load_event(builder.DEFAULT_GAME, event_id)[0]
            cls.generated[event_id] = event_from_file(builder.ROOT / f'AuraClash/events/ac_vanilla_{group}_options.txt', event_id)

    def test_all_generated_files_are_current(self):
        for path, data in builder.render(builder.DEFAULT_GAME).items():
            self.assertEqual(path.read_bytes(), data, str(path))

    def test_reviewed_events_and_required_resolvers_are_overridden(self):
        self.assertEqual(len(self.generated), 56)
        self.assertEqual(len(self.generated), len(SPECS))
        for text in self.generated.values():
            self.assertEqual(text.count('id_override_priority = 10'), 1)

    def test_vanilla_options_remain_byte_for_byte_unchanged(self):
        for event_id, group, _ in SPECS:
            if group == 'fatal':
                continue
            before = [self.vanilla[event_id][field.start:field.end] for field in builder.fields(self.vanilla[event_id]) if field.key == 'option']
            after = [self.generated[event_id][field.start:field.end] for field in builder.fields(self.generated[event_id]) if field.key == 'option']
            original_after = [option for option in after if not re.search(r'\bname\s*=\s*ac_event_', builder.masked(option))]
            self.assertEqual(before, original_after, event_id)

    def test_normal_event_setup_and_cleanup_are_unchanged(self):
        for event_id, group, _ in SPECS:
            for key in ('trigger', 'after', 'immediate'):
                if key == 'immediate' and (group == 'fatal' or event_id == 'contest_events.1132'):
                    continue
                before = [self.vanilla[event_id][field.start:field.end] for field in builder.fields(self.vanilla[event_id]) if field.key == key]
                after = [self.generated[event_id][field.start:field.end] for field in builder.fields(self.generated[event_id]) if field.key == key]
                self.assertEqual(before, after, f'{event_id}: {key}')

    def test_cultivation_choices_are_before_normal_choices(self):
        for event_id, group, choices in SPECS:
            if not choices:
                continue  # Outcome-only overrides do not add a choice.
            text = self.generated[event_id]
            first = next(field for field in builder.fields(text) if field.key == 'option')
            self.assertRegex(builder.masked(text[first.start:first.end]), r'\bname\s*=\s*ac_event_')

    def test_bridge_includes_midorikatai_and_other_distinct_paths(self):
        text = self.generated['travel_events.3070']
        for key in ('bridge_mido', 'bridge_akakiru', 'bridge_storm', 'bridge_darkness'):
            self.assertIn('name = ac_event_' + key, text)
        self.assertIn('ABILITY = bridge_mido', text)

    def test_storm_deaths_only_run_in_the_ineligible_branch_before_choice(self):
        text = self.generated['travel_danger_events.6020']
        immediate = builder.one(text, 'immediate').body(text)
        # Wrapping the body lets the same parser inspect its direct children.
        wrapper = 'wrapper = {' + immediate + '}'
        condition = next(field for field in builder.fields(wrapper) if field.key == 'if')
        fallback = next(field for field in builder.fields(wrapper) if field.key == 'else')
        self.assertIn('ABILITY = sea_rescue', wrapper[condition.start:condition.end])
        self.assertNotRegex(builder.masked(wrapper[condition.start:condition.end]), r'\bdeath\s*=')
        original_fatal = self.vanilla['travel_danger_events.6020'].split('# For correct order', 1)[1].split('\n\toption =', 1)[0]
        # The original immediate's final closing brace is outside the copied body.
        original_fatal = original_fatal[:original_fatal.rfind('}')]
        self.assertEqual(normalized(fallback.body(wrapper)), normalized(original_fatal))

    def test_poison_death_and_success_log_stay_in_ineligible_branch(self):
        text = self.generated['host_dinner_events.1091']
        immediate = builder.one(text, 'immediate').body(text)
        wrapper = 'wrapper = {' + immediate + '}'
        condition = next(field for field in builder.fields(wrapper) if field.key == 'if')
        fallback = next(field for field in builder.fields(wrapper) if field.key == 'else')
        self.assertIn('ac_event_poison_survival_trigger', wrapper[condition.start:condition.end])
        self.assertNotIn('i_was_murdered_log', wrapper[condition.start:condition.end])
        self.assertEqual(normalized(fallback.body(wrapper)), normalized(builder.one(self.vanilla['host_dinner_events.1091'], 'immediate').body(self.vanilla['host_dinner_events.1091'])))

    def test_declining_fatal_rescues_still_executes_original_death(self):
        for event_id in ('travel_danger_events.6020', 'host_dinner_events.1091'):
            text = self.generated[event_id]
            options = [text[field.start:field.end] for field in builder.fields(text) if field.key == 'option']
            self.assertNotRegex(builder.masked(options[0]), r'\bdeath\s*=')
            self.assertIn('death = {', options[-1])
            self.assertIn('_rescue_pending', options[-1])

    def test_hunt_rescue_uses_safe_existing_follow_up(self):
        text = self.generated['hunt.4007']
        first = next(field for field in builder.fields(text) if field.key == 'option')
        option = text[first.start:first.end]
        self.assertIn('save_scope_as = rampant_scare', option)
        self.assertNotIn('save_scope_as = rampant_hunter', option)
        self.assertIn('id = hunt.4900', builder.one(text, 'after').body(text))

    def test_healing_never_removes_infection_or_gangrene(self):
        for event_id in ('health.4000', 'health.4001', 'health.4002'):
            text = self.generated[event_id]
            field = next(field for field in builder.fields(text) if field.key == 'option')
            option = text[field.start:field.end]
            self.assertIn('ac_heal_one_wound_effect = yes', option)
            self.assertNotIn('remove_character_modifier', option)
            self.assertIn('ac_event_chi_healing_cooldown_effect', option)

    def test_healing_interaction_and_events_share_cooldown(self):
        trigger = (builder.ROOT / 'AuraClash/common/scripted_triggers/ac_event_triggers.txt').read_text()
        interaction = (builder.ROOT / 'AuraClash/common/character_interactions/ac_cultivation_interactions.txt').read_text(encoding='utf-8-sig')
        self.assertIn('NOT = { has_character_flag = ac_chi_healing_cooldown }', trigger)
        self.assertIn('NOT = { has_character_flag = ac_chi_healing_cooldown }', interaction)
        self.assertIn('ac_event_chi_healing_cooldown_effect = yes', interaction)

    def test_all_custom_references_and_dynamic_abilities_exist(self):
        common = '\n'.join(path.read_text(encoding='utf-8-sig') for path in (builder.ROOT / 'AuraClash/common').rglob('*.txt'))
        definitions = set(re.findall(r'^(ac_\w+)\s*=\s*\{', common, re.M))
        text = common + '\n' + '\n'.join(self.generated.values())
        for ability in re.findall(r'\bABILITY\s*=\s*(\w+)', text):
            self.assertIn('ac_event_' + ability + '_trigger', definitions)
        for reference in re.findall(r'\b(ac_\w+_(?:trigger|effect))\s*=', text):
            self.assertIn(reference, definitions)
        for reference in re.findall(r'\bhas_(?:perk|trait)\s*=\s*(ac_\w+)', text):
            self.assertIn(reference, definitions)

    def test_generated_localization_has_bom_and_all_option_labels(self):
        path = builder.ROOT / 'AuraClash/localization/english/ac_event_options_l_english.yml'
        self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))
        loc = path.read_text(encoding='utf-8-sig')
        keys = re.findall(r'^\s+(\w+):0', loc, re.M)
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(set(keys), set(LOCALIZATION))
        for text in self.generated.values():
            for reference in re.findall(r'\b(?:name|custom_tooltip|desc|title|flavor)\s*=\s*(ac_event_\w+)', text):
                if reference in {'ac_event_sea_rescue_pending', 'ac_event_poison_rescue_pending', 'ac_event_contest_resolved'}:
                    continue  # Names of saved scope values, not localization keys.
                self.assertIn(reference, keys)

    def test_added_event_references_are_live_installed_definitions(self):
        live = builder.event_sources(builder.DEFAULT_GAME)
        for event_id, group, choices in SPECS:
            for reference in re.findall(r'(?:trigger_event\s*=|\bid\s*=)\s*(\w+\.\d+)', choices):
                self.assertIn(reference, live, f'{event_id}: {reference}')

    def test_all_new_modifiers_have_names_and_descriptions(self):
        path = builder.ROOT / 'AuraClash/common/modifiers/ac_event_expansion_modifiers.txt'
        for key in re.findall(r'^(ac_\w+)\s*=\s*\{', path.read_text(encoding='utf-8-sig'), re.M):
            self.assertIn(key, LOCALIZATION)
            self.assertIn(key + '_desc', LOCALIZATION)

    def test_captive_choices_do_not_use_the_free_character_gate(self):
        text = (builder.ROOT / 'AuraClash/common/scripted_triggers/ac_event_expansion_triggers.txt').read_text()
        captive = text[text.index('ac_event_captive_trigger ='):]
        self.assertIn('is_imprisoned = yes', captive)
        self.assertNotIn('ac_event_practitioner_trigger = yes', captive)
        self.assertIn('escape_from_prison_effect = yes', self.generated['prison.9501'])
        self.assertIn('prison.9499', self.generated['prison.9501'])

    def test_frostbite_treatment_updates_native_severity_before_cleanup(self):
        options = next(choices for event, _, choices in SPECS if event == 'travel_danger_events.1011')
        self.assertIn('name = frostbite_severity subtract = 6', options)
        self.assertIn('change_frostbite_modifier_with_severity_effect', options)
        for permanent in ('maimed', 'one_legged', 'disfigured'):
            self.assertNotIn('remove_trait = ' + permanent, options)

    def test_tournament_intervention_guards_the_delayed_lethal_roll(self):
        vanilla = self.vanilla['contest_events.1132']
        generated = self.generated['contest_events.1132']
        wrapper = 'wrapper = {' + builder.one(generated, 'immediate').body(generated) + '}'
        first = next(f for f in builder.fields(wrapper) if f.key == 'hidden_effect')
        branches = 'wrapper = {' + first.body(wrapper) + '}'
        fallback = builder.one(branches, 'else').body(branches)
        vanilla_wrap = 'wrapper = {' + builder.one(vanilla, 'immediate').body(vanilla) + '}'
        original = builder.one(vanilla_wrap, 'hidden_effect').body(vanilla_wrap)
        self.assertEqual(normalized(fallback), normalized(original))
        # Both injury and explicit death live under the same negative guard.
        start = generated.index('\t\tscope:agency_loser = {')
        opening = generated.index('{', start)
        loser = generated[opening:builder.close_brace(generated, opening)]
        guard = builder.one('wrapper = ' + loser, 'if')
        guarded = guard.body('wrapper = ' + loser)
        self.assertIn('NOT = { exists = scope:ac_event_contest_resolved }', guarded)
        self.assertIn('increase_wounds_effect', guarded)
        self.assertIn('death = {', guarded)
        self.assertIn('trigger_event = contest_events.1133', loser[guard.end - len('wrapper = '):])

    def test_archery_scores_directly_without_arming_a_second_roll(self):
        options = next(choices for event, _, choices in SPECS if event == 'contest_events.0710')
        self.assertIn('SCORE = increase_major', options)
        self.assertIn('success_pivotal_flag', options)
        self.assertNotIn('add_character_flag = prowess_', options)

    def test_named_mending_uses_shared_healing_cooldown(self):
        for event in ('health.4000', 'health.4001', 'health.4002'):
            options = next(choices for eid, _, choices in SPECS if eid == event)
            self.assertIn('name = ac_event_kiihakai_mend_wounds', options)
            self.assertIn('ac_event_kiihakai_mending_trigger = yes', options)
            self.assertIn('ac_event_chi_healing_cooldown_effect = yes', options)

    def test_meditation_relieves_stress_without_adding_exertion(self):
        choices = next(choices for event, _, choices in SPECS if event == 'stress_threshold.2311')
        self.assertIn('add_stress = -40', choices)
        self.assertIn('ac_event_meditation_cooldown years = 3', choices)
        self.assertNotIn('ac_event_exertion_effect', choices)

    def test_poison_response_receives_its_sender_and_cremation_checks_faith(self):
        gift = next(choices for event, _, choices in SPECS if event == 'intrigue_scheme_ongoing.5005')
        self.assertLess(gift.index('save_scope_as = owner'), gift.index('trigger_event = intrigue_scheme_ongoing.5006'))
        burials = next(choices for event, _, choices in SPECS if event == 'epidemic_events.1110')
        self.assertIn('faith = { has_doctrine = doctrine_funeral_cremation }', burials)

    def test_precognition_is_a_real_defense_in_both_attack_events(self):
        for event in ('hunt.4010', 'contest_events.1131'):
            choices = next(choices for eid, _, choices in SPECS if eid == event)
            self.assertIn('ac_event_precognition_trigger = yes', choices)
        follow_up = self.generated['contest_events.1132']
        for who in ('contest_opponent_a', 'contest_opponent_b'):
            self.assertIn('scope:' + who + ' = { remove_character_flag = ac_event_contest_safe }', follow_up)

    def test_travel_helpers_cannot_be_recruited_remotely(self):
        text = (builder.ROOT / 'AuraClash/common/scripted_triggers/ac_event_triggers.txt').read_text()
        self.assertIn('any_entourage_character', text)
        self.assertNotIn('any_courtier', text)
        self.assertNotIn('any_living_character', text)


if __name__ == '__main__':
    unittest.main()
