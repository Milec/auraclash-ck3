"""The packed heightmap round-trips to the source heightmap within the packing tolerance."""
import re
import unittest

import numpy as np
from PIL import Image

import pack_heightmap as pack


class PackedHeightmapTests(unittest.TestCase):
    def test_committed_files_are_current(self):
        files, _, _ = pack.render()
        self.assertEqual((pack.MAP / 'heightmap.heightmap').read_bytes(), files['heightmap.heightmap'])
        for name in ('packed_heightmap.png', 'indirection_heightmap.png'):
            self.assertTrue(np.array_equal(np.asarray(Image.open(pack.MAP / name)), files[name][0]), name)

    def test_round_trip(self):
        desc = (pack.MAP / 'heightmap.heightmap').read_text(encoding='utf-8-sig')
        offsets = [int(y) for _, y in re.findall(r'\{ (\d+) (\d+) \}', desc.split('level_offsets=')[1].split('max_')[0])]
        packed = np.asarray(Image.open(pack.MAP / 'packed_heightmap.png'))
        indirection = np.asarray(Image.open(pack.MAP / 'indirection_heightmap.png'))
        rebuilt = pack.unpack(offsets, packed, indirection)
        source = pack.load_heightmap().astype(np.float64)
        self.assertLessEqual(np.abs(rebuilt - source).max(), pack.MAX_ERROR + 1)
        self.assertIn('topology = "heightmap.heightmap"', (pack.MAP / 'default.map').read_text(encoding='utf-8-sig'))


if __name__ == '__main__':
    unittest.main()
