"""Every vanilla key the mods name must exist in the installed CK3."""
import unittest

import build_event_overrides as builder

if not builder.GAME_AVAILABLE:
    raise unittest.SkipTest('CK3 game files not found; set CK3_GAME_ROOT to run these checks')
import verify_vanilla_keys as keys


class VanillaKeyTests(unittest.TestCase):
    def test_every_reference_is_defined(self):
        self.assertEqual({f'{label}: {key}' for label, key in keys.check(builder.DEFAULT_GAME)}, set())

    def test_religion_uses_the_1_20_folders(self):
        for mod in keys.MODS:
            for old in ('common/religion/religions', 'common/religion/holy_sites'):
                self.assertFalse((mod / old).exists(), mod / old)


if __name__ == '__main__':
    unittest.main()
