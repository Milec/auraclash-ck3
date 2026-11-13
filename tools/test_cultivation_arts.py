"""Transformations, Seals, Heavenly Gates and spirit fruit, and forged equipment."""
import re
import unittest

import build_equipment as equipment
import build_event_overrides as script
import build_heavenly_gates as gates
import build_seals as seals
import build_transformations as transformations

BUILDERS = (equipment, gates, seals, transformations)


class CultivationArtsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {b.__name__: b.render() for b in BUILDERS}

    def test_committed_output_is_current(self):
        for name, files in self.files.items():
            for relative, data in files.items():
                self.assertEqual((equipment.OUT / relative).read_bytes(), data, f'{name}: {relative}')

    def test_scripts_balance(self):
        for files in self.files.values():
            for relative, data in files.items():
                if relative.endswith(('.txt', '.gui')):
                    text = data.decode('utf-8-sig')
                    self.assertEqual(text.count('{'), text.count('}'), relative)
                    if relative.endswith('.txt') and not relative.startswith('gui/'):
                        script.fields(text)

    def test_localization_covers_interactions_and_events(self):
        loc = ''.join(d.decode('utf-8-sig') for files in self.files.values() for r, d in files.items() if r.endswith('.yml'))
        for name, files in self.files.items():
            for relative, data in files.items():
                text = data.decode('utf-8-sig')
                if 'character_interactions' in relative:
                    for key in re.findall(r'(?m)^(\w+_interaction) = \{', text):
                        self.assertIn(f' {key}:0 "', loc, key)
                if relative.startswith('events/'):
                    for key in re.findall(r'\b(?:title|desc|name) = (ac_\w+\.\d{4}\.\w+)', text):
                        self.assertIn(f' {key}:0 "', loc, key)

    def test_no_inline_values_where_ck3_wants_a_name(self):
        # CK3 reads durations, counts and scripted-effect parameters only as a number or a named
        # value; an inline { value = ... } there breaks the parse of the whole file.
        bad = re.compile(r'\b(?:months|years|days|count|CHI|AP) = \{ *value\b|\b(?:months|years|days) = scope:')
        for files in self.files.values():
            for relative, data in files.items():
                for n, line in enumerate(data.decode('utf-8-sig').splitlines(), 1):
                    self.assertIsNone(bad.search(line), f'{relative}:{n}')

    def test_built_on_ck3_systems_not_decisions(self):
        # Interactions, schemes, activities, artifacts, special buildings, story cycles and hooks; no decisions.
        made = {r for files in self.files.values() for r in files}
        self.assertFalse([r for r in made if r.startswith('common/decisions/')])
        for kind in ('common/schemes/', 'common/activities/', 'common/artifacts/', 'common/buildings/', 'common/story_cycles/',
                     'common/hook_types/', 'common/character_interactions/', 'common/scripted_guis/'):
            self.assertTrue([r for r in made if r.startswith(kind)], kind)

    def test_source_catalogues(self):
        # The Core Rulebook's Seals chapter: 5 Freestyle and 17 Style Seals.
        self.assertEqual(len(seals.SEALS), 22)
        self.assertEqual({s['school'] for s in seals.SEALS.values()}, {None, *seals.STYLES})
        # The IF's seven Transformations, one Style each plus Freestyle Limitbreaker.
        self.assertEqual(set(transformations.FORMS), {'limitbreaker', 'reaper', 'godhand', 'soul_domain', 'malocchio', 'titan', 'asura'})
        # The forgemaster's materials and prices, and the author's Core pairs.
        self.assertEqual({k: v[1] for k, v in equipment.MATERIALS.items()},
                         {'steel': 0, 'jade': 100, 'beastbone': 80, 'snowsteel': 120, 'truegold': 140})
        self.assertEqual(equipment.MATERIALS['jade'][3], ('soul', 'power'))
        self.assertEqual(equipment.MATERIALS['beastbone'][3], ('fortitude', 'agility'))
        # Rulebook: Gate levels run from 5 to 15.
        self.assertEqual(min(r[1] for r in gates.REGIONS.values()), 5)
        self.assertEqual(max(r[2] for r in gates.REGIONS.values()), 15)

    def test_forge_board_steps_resolve(self):
        effects = self.files['build_equipment']['common/scripted_effects/ac_equipment_effects.txt'].decode('utf-8-sig')
        triggers = self.files['build_equipment']['common/scripted_triggers/ac_equipment_triggers.txt'].decode('utf-8-sig')
        loc = self.files['build_equipment']['localization/english/ac_equipment_l_english.yml'].decode('utf-8-sig')
        for key in equipment.NODES:
            self.assertIn(f'flag:{key}', effects)
            self.assertIn(f'var:ac_forge_node = flag:{key}', triggers)
            self.assertIn(f' ac_forge_node_{key}:0 "', loc)
        for kind in equipment.KINDS:
            for mat in equipment.MATERIALS:
                for tier in equipment.TIERS:
                    self.assertIn(f'set_artifact_name = {equipment.name_key(kind, mat, tier)}', effects)
        gui = self.files['build_equipment']['gui/ac_forge_window.gui'].decode('utf-8-sig')
        guis = self.files['build_equipment']['common/scripted_guis/ac_forge_guis.txt'].decode('utf-8-sig')
        for used in set(re.findall(r"GetScriptedGui\('(\w+)'\)|StoryGui\w+\('(\w+)'\)", gui)):
            name = used[0] or used[1]
            self.assertRegex(guis, rf'(?m)^{name} = \{{', name)

    def test_transformations_reach_learning_paths(self):
        effects = self.files['build_transformations']['common/scripted_effects/ac_transformation_effects.txt'].decode('utf-8-sig')
        gate_events = self.files['build_heavenly_gates']['events/ac_heavenly_gate_events.txt'].decode('utf-8-sig')
        for key in transformations.FORMS:
            self.assertIn(f'ac_learn_tf_{key}_effect = {{', effects)
            self.assertIn(f'ac_learn_tf_{key}_effect = yes', gate_events)


if __name__ == '__main__':
    unittest.main()
