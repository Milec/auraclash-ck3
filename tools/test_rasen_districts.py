"""Imperial Rasen's starting districts (CK3 1.21) match each province's holding, rank and goods."""
import re
import unittest

import rasen_districts as districts
import rasen_map_graph as graph

HISTORY = graph.MOD / 'history/provinces/rasen_provinces.txt'


class RasenDistrictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = HISTORY.read_text(encoding='utf-8-sig')
        cls.entries = {int(m.group(1)): m.group(2) for m in re.finditer(r'^(\d+) = \{\n(.*?)^\}', text, re.S | re.M)}

    def test_history_lists_each_holding_district_first(self):
        for province, body in self.entries.items():
            holding = re.search(r'holding = (\w+)', body).group(1)
            kinds = re.findall(r'type = (\w+)', body)
            if holding in districts.HOLDING_DISTRICT:
                self.assertEqual(kinds[0], districts.HOLDING_DISTRICT[holding], province)
                self.assertEqual(len(kinds), len(set(kinds)), province)
            else:
                self.assertEqual(kinds, [], province)

    def test_resource_districts_match_the_county_goods(self):
        allowed = {}
        for good, kind in districts.RESOURCE_DISTRICT.items():
            allowed.setdefault(kind, set()).add(good)
        goods, county = districts.goods(), districts.county_of()
        for province, body in self.entries.items():
            for kind in re.findall(r'type = (\w+)', body):
                if kind in allowed:
                    self.assertTrue(allowed[kind] & goods[county[province]], (province, kind))

    def test_entrepots_are_coastal_markets(self):
        coastal, ranks = graph.coastal_provinces(), districts.ranks()
        found = [p for p, body in self.entries.items() if 'entrepot_location_district' in body]
        self.assertEqual(sorted(found), sorted(districts.entrepots()))
        self.assertEqual(len(found), districts.ENTREPOTS)
        for p in found:
            self.assertIn(p, coastal)
            self.assertIn(ranks[p], ('duchy', 'realm', 'hub'))

    def test_port_districts_are_coastal_county_seats(self):
        coastal, ranks = graph.coastal_provinces(), districts.ranks()
        for province, body in self.entries.items():
            if 'port_district' in body:
                self.assertIn(province, coastal)
                self.assertIn(province, ranks)

    def test_hub_is_the_largest_city(self):
        hub = graph.counties()[graph.titles()['k_azuma']['capital']]['provinces'][0]
        self.assertIn('province_size = 8', self.entries[hub])
        self.assertIn('market_district', self.entries[hub])

    def test_entrepot_locators_are_current_and_offshore(self):
        # Without a locator CK3 logs "Could not find locator transform for entrepot" every frame it draws one.
        for relative, data in districts.render().items():
            self.assertEqual((graph.MOD / relative).read_bytes(), data, relative)
        positions = districts.entrepot_positions()
        for province in districts.entrepots():
            self.assertIn(province, positions)
        grid, water = graph._grid(), graph.water_ids()
        height = grid.shape[0]
        coastal = [positions[p] for p in graph.coastal_provinces() if p in positions]
        offshore = sum(int(grid[height - 1 - int(z), int(x)]) in water for x, z in coastal)
        self.assertGreater(offshore / len(coastal), 0.9)
        self.assertEqual(len(positions), len(districts.county_of()))


if __name__ == '__main__':
    unittest.main()
