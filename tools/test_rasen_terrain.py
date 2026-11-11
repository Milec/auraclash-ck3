"""Imperial Rasen's ground textures are current, well-formed and name real vanilla materials."""
import io
import re
import unittest

import numpy as np
from PIL import Image

import build_event_overrides as builder
import build_rasen_terrain as terrain


class TerrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = terrain.render()

    def test_images_are_current(self):
        for name, data in self.files.items():
            committed = np.asarray(Image.open(terrain.OUT / name))
            self.assertTrue(np.array_equal(committed, np.asarray(Image.open(io.BytesIO(data)))), name)

    def test_detail_maps_cover_the_map_and_weights_sum_to_255(self):
        index = np.asarray(Image.open(io.BytesIO(self.files['detail_index.tga'])))
        intensity = np.asarray(Image.open(io.BytesIO(self.files['detail_intensity.tga'])))
        size = (terrain.rasen.MAP_HEIGHT, terrain.rasen.MAP_WIDTH, 4)
        self.assertEqual(index.shape, size)
        self.assertEqual(intensity.shape, size)
        self.assertTrue((intensity.astype(np.int32).sum(axis=2) == 255).all())
        self.assertLessEqual(set(np.unique(index).tolist()), set(terrain.MATERIAL_INDEX.values()))
        # Open ocean is sea-floor sand; the continent is not.
        self.assertEqual(index[0, 0, 0], terrain.MATERIAL_INDEX[terrain.WATER])
        self.assertGreater((index[..., 0] != terrain.MATERIAL_INDEX[terrain.WATER]).mean(), 0.1)

    def test_every_terrain_has_a_material_and_tint(self):
        kinds = set(re.findall(r'^\d+=(\w+)$', terrain.TERRAIN.read_text(encoding='utf-8-sig'), re.M))
        self.assertLessEqual(kinds, set(terrain.TERRAIN_MATERIAL))
        self.assertEqual(set(terrain.TINT), set(terrain.MATERIAL_INDEX))

    @unittest.skipUnless(builder.GAME_AVAILABLE, 'CK3 game files not found; set CK3_GAME_ROOT')
    def test_material_indices_match_the_game(self):
        settings = (builder.DEFAULT_GAME / 'gfx/map/terrain/materials.settings').read_text(encoding='utf-8-sig')
        names = re.findall(r'name\s*=\s*"([^"]+)"', settings)
        for name, position in terrain.MATERIAL_INDEX.items():
            self.assertEqual(names.index(name), position, name)


if __name__ == '__main__':
    unittest.main()
