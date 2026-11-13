import re
import unittest

import build_event_overrides as builder
import build_rasen_character_stubs as stubs


@unittest.skipUnless(builder.GAME_AVAILABLE, 'CK3 game files not installed')
class CharacterStubTests(unittest.TestCase):
    def test_stubs_are_current_and_cover_every_named_earth_character(self):
        files, count = stubs.render(builder.DEFAULT_GAME)
        for relative, data in files.items():
            self.assertEqual((stubs.OUT / relative).read_bytes(), data, relative)
        text = files[stubs.TARGET].decode('utf-8-sig')
        defined = set(re.findall(r'(?m)^([A-Za-z0-9_]+) = \{', text))
        self.assertEqual(len(defined), count)
        self.assertGreater(count, 900)
        # Every stub was born and died long before the bookmark, so no living character changes.
        for line in text.splitlines()[2:]:
            self.assertIn('1.1.1 = { birth = yes } 2.1.1 = { death = yes }', line)
        # None shadows one of the mod's own characters.
        self.assertFalse(defined & stubs.ours())


if __name__ == '__main__':
    unittest.main()
