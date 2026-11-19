"""Imperial Rasen's road network (CK3 1.21) stays current, connected and drawable."""
import re
import unittest

import build_rasen_roads as roads
import rasen_map_graph as graph


class RasenRoadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = roads.render()
        cls.roads = roads.build()

    def test_generated_file_is_current(self):
        for relative, data in self.files.items():
            self.assertEqual((roads.MOD / relative).read_bytes(), data, relative)

    def test_descriptor_replaces_vanilla_roads(self):
        # Vanilla roads name Earth provinces beyond the map, which crashes the game after history loads.
        for descriptor in (roads.MOD / 'descriptor.mod', roads.MOD.parent / 'AuraClash.mod'):
            self.assertIn('replace_path="common/roads/road_types"', descriptor.read_text(encoding='utf-8-sig'))

    def test_shipped_splines_match_these_roads(self):
        # The road graphics are generated in the game; regenerate them whenever the roads change
        # (python tools/prepare_rasen_checks.py --splines, then copy the user folder's splnet).
        import hashlib
        import json
        record = json.loads((roads.MOD.parent / 'tools/rasen_road_splines.json').read_text(encoding='utf-8'))
        splnet = roads.MOD / 'gfx/map/spline_network/spline_network.splnet'
        self.assertEqual(hashlib.sha256(self.files[roads.OUTPUT]).hexdigest(), record['roads_sha256'])
        self.assertEqual(hashlib.sha256(splnet.read_bytes()).hexdigest(), record['splnet_sha256'])

    def test_keys_are_unique(self):
        keys = [r['key'] for r in self.roads]
        self.assertEqual(len(keys), len(set(keys)))
        text = self.files[roads.OUTPUT].decode('utf-8-sig')
        self.assertEqual(len(re.findall(r'^\w+ = \{', text, re.M)), len(keys))

    def test_each_step_joins_neighbouring_provinces(self):
        near, water = graph.neighbours(), graph.water_ids()
        for road in self.roads:
            path = road['path']
            self.assertEqual(len(path), len(set(path)), road['key'])
            for a, b in zip(path, path[1:]):
                self.assertIn(b, near[a], road['key'])
            self.assertNotIn(path[0], water, road['key'])
            self.assertNotIn(path[-1], water, road['key'])
            if road['sea']:
                self.assertTrue(any(p in water for p in path), road['key'])
                self.assertFalse(set(path) & graph.impassable_seas(), road['key'])
            else:
                self.assertFalse(set(path) & water, road['key'])

    def test_roads_join_duchy_markets_into_one_network(self):
        # CK3 1.21: a road must start and end at a trade market, one per duchy at the capital's seat.
        titles, counties = graph.titles(), graph.counties()
        markets = {counties[info['capital']]['provinces'][0] for info in titles.values()
                   if info['tier'] == 'd' and info['capital'] in counties}
        links: dict[int, set[int]] = {m: set() for m in markets}
        for r in self.roads:
            self.assertIn(r['path'][0], markets, r['key'])
            self.assertIn(r['path'][-1], markets, r['key'])
            links[r['path'][0]].add(r['path'][-1])
            links[r['path'][-1]].add(r['path'][0])
        start = min(markets)
        reached, stack = {start}, [start]
        while stack:
            for n in links[stack.pop()]:
                if n not in reached:
                    reached.add(n)
                    stack.append(n)
        self.assertEqual(reached, markets)

    def test_imperial_way_links_every_realm_to_azuma(self):
        titles = graph.titles()
        seat = {k: v['provinces'][0] for k, v in graph.counties().items()}
        built: dict[int, set[int]] = {}
        for r in self.roads:
            if r['tier'] == 1:
                a, b = r['path'][0], r['path'][-1]
                built.setdefault(a, set()).add(b)
                built.setdefault(b, set()).add(a)
        hub = seat[titles[roads.CAPITAL]['capital']]
        reached, stack = {hub}, [hub]
        while stack:
            for n in built.get(stack.pop(), ()):
                if n not in reached:
                    reached.add(n)
                    stack.append(n)
        for key, info in titles.items():
            if info['tier'] == 'k' and key != roads.CAPITAL:
                self.assertIn(seat[info['capital']], reached, key)


if __name__ == '__main__':
    unittest.main()
