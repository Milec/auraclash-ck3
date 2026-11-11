"""RasenMap's patched copies of vanilla files stay current and change only what they must."""
import unittest

import build_event_overrides as builder

if not builder.GAME_AVAILABLE:
    raise unittest.SkipTest('CK3 game files not found; set CK3_GAME_ROOT to run these checks')
import build_rasen_vanilla_patches as patches


class VanillaPatchTests(unittest.TestCase):
    def test_patched_files_are_current_and_minimal(self):
        _, standin = patches.map_limits()
        allowed = ('Imperial Rasen', f'province:{standin}', f'= {patches.SITE_COUNTY}', f'= {patches.SITE_BARONY}')
        for relative, data in patches.render(builder.DEFAULT_GAME).items():
            self.assertEqual((patches.OUT / relative).read_bytes(), data, relative)
            vanilla = (builder.DEFAULT_GAME / relative).read_text(encoding='utf-8-sig').replace('\r\n', '\n').split('\n')
            ours = data.decode('utf-8-sig').split('\n')[3:]
            self.assertEqual(len(vanilla), len(ours), relative)
            changed = [b for a, b in zip(vanilla, ours) if a != b]
            self.assertTrue(changed, relative)
            for line in changed:
                self.assertTrue(any(mark in line for mark in allowed), f'{relative}: {line}')


if __name__ == '__main__':
    unittest.main()
