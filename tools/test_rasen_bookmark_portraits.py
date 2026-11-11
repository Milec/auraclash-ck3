"""Each featured bookmark character has a current portrait of the right gender."""
import re
import unittest

import build_event_overrides as builder

if not builder.GAME_AVAILABLE:
    raise unittest.SkipTest('CK3 game files not found; set CK3_GAME_ROOT to run these checks')
import build_rasen_bookmark_portraits as portraits

BOOKMARKS = portraits.ROOT / 'RasenMap/common/bookmarks/bookmarks'


class BookmarkPortraitTests(unittest.TestCase):
    def test_portraits_are_current_and_match_characters(self):
        files = portraits.render(builder.DEFAULT_GAME)
        text = ''.join(p.read_text(encoding='utf-8-sig') for p in BOOKMARKS.glob('*.txt'))
        featured = re.findall(r'name = "(bm_rasen_\w+)"', text)
        self.assertEqual(sorted(featured), sorted(portraits.SOURCES))
        for key in featured:
            data = files[f'{key}.txt']
            self.assertEqual((portraits.OUT / f'{key}.txt').read_bytes(), data, key)
            body = data.decode('utf-8-sig')
            self.assertIn(f'\n{key}={{', body)
            block = text[text.index(f'name = "{key}"'):]
            block = block[:block.index('\n\t}')]
            female = 'type = female' in block
            self.assertEqual('type=female' in body, female, key)


if __name__ == '__main__':
    unittest.main()
