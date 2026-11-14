"""Imperial Rasen's map object locators cover every province and sit inside it."""
import re
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

import build_rasen_map as rasen

ROOT = Path(__file__).resolve().parents[1] / 'AuraClash'


class LocatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        a = np.asarray(Image.open(ROOT / 'map_data/provinces.png')).astype(np.uint32)
        cls.key = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
        cls.colour = {}
        for line in (ROOT / 'map_data/definition.csv').read_text(encoding='utf-8-sig').splitlines()[1:]:
            p = line.split(';')
            cls.colour[int(p[0])] = (int(p[1]) << 16) | (int(p[2]) << 8) | int(p[3])
        summary = (ROOT / 'map_data/rasen_summary.json').read_text(encoding='utf-8')
        cls.land = int(re.search(r'"land_provinces": (\d+)', summary).group(1))

    def test_every_locator_file_covers_its_provinces_from_inside(self):
        h = self.key.shape[0]
        for filename, (name, _, _, land_only, _) in rasen.LOCATORS.items():
            text = (ROOT / f'gfx/map/map_object_data/{filename}.txt').read_text(encoding='utf-8-sig')
            self.assertIn(f'name="{name}"', text)
            found = re.findall(r'id=(\d+)\s*position=\{ ([\d.]+) [\d.]+ ([\d.]+) \}', text)
            ids = [int(i) for i, _, _ in found]
            self.assertEqual(ids, sorted(set(ids)), filename)
            self.assertEqual(len(ids), self.land if land_only else len(self.colour) + 1, filename)
            for pid, x, z in found:
                if pid == '0':
                    continue
                pixel = self.key[h - 1 - int(float(z)), int(float(x))]
                self.assertEqual(pixel, self.colour[int(pid)], f'{filename} id {pid}')


if __name__ == '__main__':
    unittest.main()
