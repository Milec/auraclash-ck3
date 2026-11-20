"""Consistency checks for the generated Imperial Rasen map data (fast; no regeneration)."""
from pathlib import Path
import re
import unittest

import numpy as np
from PIL import Image

import build_event_overrides as parser
import build_rasen_map as rasen

ROOT = Path(__file__).resolve().parents[1] / 'AuraClash'


class RasenMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rows = (ROOT / 'map_data/definition.csv').read_text(encoding='utf-8').splitlines()
        cls.defs = [r.split(';') for r in rows[1:]]
        cls.titles = (ROOT / 'common/landed_titles/00_rasen_titles.txt').read_text(encoding='utf-8-sig')
        cls.default = (ROOT / 'map_data/default.map').read_text(encoding='utf-8')

    def test_definitions_are_sequential_with_unique_colours(self):
        ids = [int(r[0]) for r in self.defs]
        self.assertEqual(ids, list(range(1, len(ids) + 1)))
        colours = {tuple(r[1:4]) for r in self.defs}
        self.assertEqual(len(colours), len(ids))

    def test_provinces_png_uses_exactly_the_defined_colours(self):
        image = np.asarray(Image.open(ROOT / 'map_data/provinces.png').convert('RGB'))
        self.assertEqual(image.shape[:2], (rasen.MAP_HEIGHT, rasen.MAP_WIDTH))
        packed = (image[..., 0].astype(np.int64) << 16) | (image[..., 1].astype(np.int64) << 8) | image[..., 2]
        used = set(np.unique(packed).tolist())
        defined = {(int(r) << 16) | (int(g) << 8) | int(b) for _, r, g, b, *_ in self.defs}
        self.assertEqual(used, defined)

    def test_every_land_province_has_exactly_one_barony(self):
        provinces = [int(p) for p in re.findall(r'province = (\d+)', self.titles)]
        self.assertEqual(len(provinces), len(set(provinces)))
        sea = set()
        for a, b in re.findall(r'(?:sea_zones|impassable_seas) = RANGE \{ (\d+) (\d+) \}', self.default):
            sea |= set(range(int(a), int(b) + 1))
        self.assertEqual(set(provinces) | sea, set(range(1, len(self.defs) + 1)))
        self.assertFalse(set(provinces) & sea)

    def test_titles_balance_and_are_localized(self):
        parser.fields(self.titles)
        keys = set(re.findall(r'^\s*([ekdcb]_\w+) = \{', self.titles, re.M))
        loc = (ROOT / 'localization/replace/english/rasen_titles_l_english.yml').read_text(encoding='utf-8-sig')
        for key in keys:
            self.assertRegex(loc, rf'(?m)^ {key}:0 "', key)
        for capital in re.findall(r'capital = (c_\w+)', self.titles):
            self.assertIn(capital, keys)

    def test_every_land_province_has_terrain_and_rivers_use_ck3_indices(self):
        terrain = (ROOT / 'common/province_terrain/00_rasen_province_terrain.txt').read_text(encoding='utf-8')
        assigned = {int(p) for p in re.findall(r'(?m)^(\d+)=\w+$', terrain)}
        provinces = {int(p) for p in re.findall(r'province = (\d+)', self.titles)}
        self.assertEqual(assigned, provinces)
        valid = {'plains', 'farmlands', 'hills', 'mountains', 'desert', 'desert_mountains', 'oasis', 'jungle', 'forest',
                 'taiga', 'wetlands', 'steppe', 'floodplains', 'drylands'}
        self.assertLessEqual(set(re.findall(r'(?m)^\d+=(\w+)$', terrain)), valid)
        rivers = Image.open(ROOT / 'map_data/rivers.png')
        self.assertEqual((rivers.mode, rivers.size), ('P', (rasen.MAP_WIDTH, rasen.MAP_HEIGHT)))
        self.assertLessEqual(set(np.unique(np.asarray(rivers)).tolist()), {0, 1, 3, 4, 5, 6, 9, 254, 255})

    def test_rivers_are_well_formed(self):
        # CK3 rivers: 1-pixel 4-connected lines; a source (0) starts each, and each ends at the sea
        # or at a merge (1) beside the river it joins. Rivers never run side by side.
        index = np.asarray(Image.open(ROOT / 'map_data/rivers.png'))
        river, water = index < 254, index == 254
        near = np.zeros(index.shape, int)
        wet = np.zeros(index.shape, int)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            near += np.roll(river, (dy, dx), (0, 1))
            wet += np.roll(water, (dy, dx), (0, 1))
        sources, merges = (index == 0).sum(), (index == 1).sum()
        self.assertGreater(sources, 300)
        self.assertTrue((near[index == 0] == 1).all())
        self.assertTrue((near[index == 1] == 2).all())
        ends = river & (near == 1) & (index != 0)
        self.assertTrue(wet[ends].all())
        self.assertEqual(int(ends.sum()) + int(merges), int(sources))
        # Only mouths touch water, and only joins (beside a merge) have three river neighbours.
        self.assertEqual(int((river & (wet > 0)).sum()), int(ends.sum()))
        merge_next = np.zeros(index.shape, bool)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            merge_next |= np.roll(index == 1, (dy, dx), (0, 1))
        self.assertFalse((river & (near > 2) & ~merge_next).any())

    def test_heightmap_matches_canvas(self):
        height = Image.open(ROOT / 'map_data/heightmap.png')
        self.assertEqual((height.mode, height.size), ('L', (rasen.MAP_WIDTH, rasen.MAP_HEIGHT)))


if __name__ == '__main__':
    unittest.main()
