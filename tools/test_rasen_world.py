"""Cross-reference checks for Imperial Rasen's peoples, faiths and history."""
from pathlib import Path
import re
import unittest

import build_event_overrides as parser
import build_rasen_world as world

OUT = world.OUT


def read(relative):
    return (OUT / relative).read_text(encoding='utf-8-sig')


class RasenWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.people = world.render()
        cls.text = {k: v.decode('utf-8-sig') for k, v in cls.files.items()}
        cls.loc = '\n'.join(v for k, v in cls.text.items() if k.endswith('.yml'))

    def test_committed_output_is_current(self):
        for relative, data in self.files.items():
            self.assertEqual((OUT / relative).read_bytes(), data, relative)

    def test_scripts_balance(self):
        for relative, text in self.text.items():
            if relative.endswith('.txt'):
                parser.fields(text)

    def test_history_uses_defined_cultures_and_faiths(self):
        cultures = set(re.findall(r'(?m)^(\w+) = \{', self.text['common/culture/cultures/rasen_cultures.txt']))
        faiths = set(re.findall(r'(?m)^\t\t(\w+) = \{', self.text['common/religion/religions/rasen_religions.txt']))
        for relative in ('history/provinces/rasen_provinces.txt', 'history/characters/rasen_characters.txt'):
            self.assertLessEqual(set(re.findall(r'culture = (\w+)', self.text[relative])), cultures, relative)
            self.assertLessEqual(set(re.findall(r'religion = (\w+)', self.text[relative])), faiths, relative)

    def test_every_county_and_province_has_history(self):
        titles = read('common/landed_titles/00_rasen_titles.txt')
        counties = set(re.findall(r'(?m)^\t\t\t(c_\w+) = \{', titles))
        held = set(re.findall(r'(?m)^(c_\w+) = \{', self.text['history/titles/rasen_titles.txt']))
        self.assertEqual(counties, held)
        provinces = set(re.findall(r'province = (\d+)', titles))
        self.assertEqual(provinces, set(re.findall(r'(?m)^(\d+) = \{', self.text['history/provinces/rasen_provinces.txt'])))

    def test_holders_and_dynasties_exist(self):
        characters = set(re.findall(r'(?m)^(rasen_\d+) = \{', self.text['history/characters/rasen_characters.txt']))
        self.assertLessEqual(set(re.findall(r'holder = (rasen_\d+)', self.text['history/titles/rasen_titles.txt'])), characters)
        dynasties = set(re.findall(r'(?m)^(dynasty_\w+) = \{', self.text['common/dynasties/rasen_dynasties.txt']))
        self.assertLessEqual(set(re.findall(r'dynasty = (dynasty_\w+)', self.text['history/characters/rasen_characters.txt'])), dynasties)

    def test_holy_sites_exist_and_faiths_have_at_most_five(self):
        sites = set(re.findall(r'(?m)^(rasen_\w+) = \{', self.text['common/religion/holy_sites/rasen_holy_sites.txt']))
        religions = self.text['common/religion/religions/rasen_religions.txt']
        self.assertLessEqual(set(re.findall(r'holy_site = (\w+)', religions)), sites)
        for faith in world.FAITHS.values():
            self.assertLessEqual(len(faith['holy_sites']), 5)

    def test_localization_covers_keys(self):
        keys = set(re.findall(r'= (rasen_\w+_religion_\w+)$', self.text['common/religion/religions/rasen_religions.txt'], re.M))
        keys |= set(world.CULTURES) | set(world.FAITHS) | set(world.RELIGIONS)
        keys |= set(re.findall(r'(?m)^(dynasty_\w+) = \{', self.text['common/dynasties/rasen_dynasties.txt']))
        keys |= {f'holy_site_{s}_name' for s in world.HOLY_SITES}
        for key in keys:
            self.assertRegex(self.loc, rf'(?m)^ {re.escape(key)}:0 "', key)

    def test_rulers_have_families_and_ordered_history(self):
        chars = self.text['history/characters/rasen_characters.txt']
        ids = set(re.findall(r'(?m)^(rasen_\d+) = \{', chars))
        spouses = re.findall(r'add_(?:matrilineal_)?spouse = (rasen_\d+)', chars)
        self.assertGreater(len(spouses), 80)
        self.assertLessEqual(set(spouses) | set(re.findall(r'(?:father|mother) = (rasen_\d+)', chars)), ids)
        for body in re.findall(r'(?ms)^rasen_\d+ = \{(.*?)^\}', chars):
            dates = [tuple(map(int, d.split('.'))) for d in re.findall(r'(?m)^\t(\d+\.\d+\.\d+) =', body)]
            self.assertEqual(dates, sorted(dates))
            personality = [t for t in re.findall(r'trait = (\w+)', body) if any(t in g for g in world.TRAIT_GROUPS)]
            self.assertLessEqual(len(personality), 3, body)
        for culture in world.CULTURES:
            self.assertIn('join_era = culture_era_early_medieval', self.text[f'history/cultures/{culture}.txt'])

    def test_exalts_rule_the_inner_kingdoms_at_the_bookmark(self):
        bookmark = self.text['common/bookmarks/bookmarks/rasen_bookmarks.txt']
        for region in ('bladed', 'sacred', 'mystic', 'cursed', 'wild'):
            self.assertIn(f'title = k_{region}', bookmark)
        self.assertIn('START_DATE = "3000.3.1"', self.text['common/defines/rasen_defines.txt'])


if __name__ == '__main__':
    unittest.main()
