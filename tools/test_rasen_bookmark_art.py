"""Bookmark art exists for the bookmark and every featured Exalt, and stays in sync with the map."""
import re
import unittest

from PIL import Image

import build_rasen_bookmark_art as art


class BookmarkArtTests(unittest.TestCase):
    def test_every_bookmark_character_has_art(self):
        bookmark = (art.ROOT / 'AuraClash/common/bookmarks/bookmarks/rasen_bookmarks.txt').read_text(encoding='utf-8-sig')
        names = set(re.findall(r'name = "?(bm_rasen_\w+)"?', bookmark))
        self.assertEqual(names, {f'bm_rasen_{land}' for land in art.LANDS})
        for name in ['bm_rasen_trials.dds'] + [f'bm_rasen_trials_{n}.dds' for n in names]:
            image = Image.open(art.OUT / name)
            self.assertEqual(image.size, art.SIZE, name)

    def test_land_images_centre_on_their_kingdom(self):
        centres = art.kingdom_centres()
        for land, (x, y) in centres.items():
            sx, sy = art.to_source(x, y)
            self.assertTrue(0 <= sx <= 2576 and 0 <= sy <= 1717, land)


if __name__ == '__main__':
    unittest.main()
