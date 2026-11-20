"""Rasen's county trade goods (CK3 1.21) stay current and cover the map."""
from collections import Counter
import re
import unittest

import build_rasen_trade as trade


class RasenTradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = trade.render()
        cls.text = cls.files[trade.OUTPUT].decode('utf-8-sig')
        cls.lists = {good: body.split() for good, body in
                     re.findall(r'^trade_good_(\w+) = \{\s*counties = \{([^}]*)\}', cls.text, re.M)}

    def test_generated_file_is_current(self):
        for relative, data in self.files.items():
            self.assertEqual((trade.MOD / relative).read_bytes(), data, relative)

    def test_every_good_has_counties(self):
        self.assertEqual(sorted(self.lists), sorted(trade.GOODS))
        for good, counties in self.lists.items():
            self.assertGreaterEqual(len(counties), 2, good)

    def test_every_county_is_real_and_has_goods(self):
        counties = trade.parse_counties()
        per_county = Counter(c for listed in self.lists.values() for c in listed)
        self.assertEqual(set(per_county), set(counties))
        self.assertGreaterEqual(min(per_county.values()), trade.MINIMUM)

    def test_treasure_materials_stay_rare(self):
        for good in ('jade', 'gold', 'gems', 'ivory', 'amber', 'alum'):
            self.assertLessEqual(len(self.lists[good]), 12, good)


if __name__ == '__main__':
    unittest.main()
