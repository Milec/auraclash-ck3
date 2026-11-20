import re
import unittest

import build_rasen_council as council
import build_rasen_interactions as governing


class GoverningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {k: v.decode('utf-8-sig') for k, v in governing.render().items()}

    def test_generated_files_are_current(self):
        for relative, text in self.text.items():
            self.assertEqual((governing.OUT / relative).read_text(encoding='utf-8-sig'), text, relative)

    def test_each_lands_ruler_nominates_its_next_exalt(self):
        interactions = self.text['common/character_interactions/rasen_governing_interactions.txt']
        for land in governing.LANDS:
            block = interactions[interactions.index(f'rasen_nominate_{land}_exalt_interaction = {{'):]
            self.assertIn(f'rasen_rules_{land}_trigger = yes', block)
            self.assertIn(f'rasen_exalt_candidate_trigger = {{ LAND = {land} }}', block)
            self.assertIn(f'name = rasen_exalt_designate_{land}', block)
        # The Council's succession prefers the nominee, then forgets them.
        effects = council.effects()
        for land in governing.LANDS:
            self.assertIn(f'global_var:rasen_exalt_designate_{land} = {{ rasen_seat_exalt_effect = {{ LAND = {land} }} }}', effects)
            self.assertIn(f'remove_global_variable = rasen_exalt_designate_{land}', effects)
        # The Wild Lands have no ruler: any Mao may nominate.
        self.assertIn('has_government = tribal_government', self.text['common/scripted_triggers/rasen_governing_triggers.txt'])

    def test_archons_and_magistrates(self):
        triggers = self.text['common/scripted_triggers/rasen_governing_triggers.txt']
        self.assertIn(f'ac_aura_pressure_value >= {governing.ARCHON_MIN_AP}', triggers)
        self.assertIn(f'count >= {governing.ARCHON_LIMIT}', triggers)
        magistrate = triggers[triggers.index('rasen_magistrate_candidate_trigger = {'):]
        self.assertIn('geographical_region = world_rasen_inner', magistrate)
        effects = self.text['common/scripted_effects/rasen_governing_effects.txt']
        self.assertIn('geographical_region = world_rasen_outer', effects)
        self.assertIn('change_government = celestial_government', effects)
        self.assertIn('rasen_archon = {', self.text['common/traits/rasen_archon_traits.txt'])

    def test_everything_is_localized_and_resolves(self):
        loc = self.text['localization/english/rasen_governing_l_english.yml']
        interactions = self.text['common/character_interactions/rasen_governing_interactions.txt']
        decisions = self.text['common/decisions/rasen_governing_decisions.txt']
        keys = re.findall(r'(?m)^(rasen_\w+) = \{', interactions + decisions)
        self.assertEqual(len(keys), len(governing.LANDS) + 3)
        for key in keys:
            self.assertIn(f' {key}:0 "', loc)
        for key in re.findall(r'(?:desc|text|custom_tooltip|selection_tooltip|confirm_text) = (rasen_\w+)', interactions + decisions):
            self.assertIn(f' {key}:0 "', loc)
        defined = set(re.findall(r'(?m)^(rasen_\w+_trigger) = \{', self.text['common/scripted_triggers/rasen_governing_triggers.txt']))
        council_triggers = council.triggers()
        for used in set(re.findall(r'(rasen_\w+_trigger) = ', interactions + decisions + self.text['common/scripted_effects/rasen_governing_effects.txt'])):
            self.assertTrue(used in defined or f'{used} = {{' in council_triggers, used)


if __name__ == '__main__':
    unittest.main()
