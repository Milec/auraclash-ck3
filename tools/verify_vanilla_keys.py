"""Check that every vanilla key the mods reference is defined by CK3 or the mods.

The overhaul scripts name vanilla traditions, doctrines, innovations, graphics
sets, terrain types, modifier icons and so on. This collects those references
from RasenMap/ and AuraClash/ and looks each one up in the game's own files.

Usage: python tools/verify_vanilla_keys.py [--game-root <game>]
Needs CK3_GAME_ROOT (or --game-root); exits 1 when a key is undefined.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import build_event_overrides as overrides

ROOT = Path(__file__).resolve().parents[1]
MODS = (ROOT / 'RasenMap', ROOT / 'AuraClash')

# Reference patterns: (label, regex over a mod file, group holding the key).
REFERENCES = [
    ('tradition', r'\b(tradition_\w+)'),
    ('ethos', r'\b(ethos_\w+)'),
    ('martial custom', r'\b(martial_custom_\w+)'),
    ('doctrine', r'\bdoctrine\s*=\s*(\w+)'),
    ('tenet', r'\b(tenet_\w+)'),
    ('doctrine', r'\bdoctrines\s*=\s*\{([^}]*)\}'),
    ('innovation', r'\b(innovation_\w+)'),
    ('culture era', r'\b(culture_era_\w+)'),
    ('graphics set', r'\b(\w+_(?:coa|building|clothing|unit)_gfx)\b'),
    ('ethnicity', r'ethnicities\s*=\s*\{([^}]*)\}'),
    ('religion family', r'\bfamily\s*=\s*(rf_\w+)'),
    ('graphical faith', r'\bgraphical_faith\s*=\s*"?(\w+)'),
    ('piety icon group', r'\bpiety_icon_group\s*=\s*"?(\w+)'),
    ('terrain', r'^\s*\d+\s*=\s*(\w+)\s*$'),
    ('modifier icon', r'\bicon\s*=\s*(\w+)'),
    ('event theme', r'\btheme\s*=\s*(\w+)'),
    ('men-at-arms', r'\bholy_order_maa\s*=\s*\{([^}]*)\}'),
    ('trait', r'\b(?:virtues|sins)\s*=\s*\{([^}]*)\}'),
    ('government', r'\bgovernment\s*=\s*(\w+)'),
]
# Modifier icons are only checked where they name modifier icons.
MODIFIER_DIRS = ('modifiers',)
# Files whose `N = key` lines are terrain assignments.
TERRAIN_FILES = ('00_rasen_province_terrain.txt',)
# Where the game defines each kind of key.
DEFINITIONS = {
    'tradition': ['common/culture/traditions'],
    'ethos': ['common/culture/pillars'],
    'martial custom': ['common/culture/pillars'],
    'doctrine': ['common/religion/doctrine_types'],
    'tenet': ['common/religion/tenet_types'],
    'innovation': ['common/culture/innovations'],
    'culture era': ['common/culture/eras'],
    'graphics set': ['common/culture/cultures', 'gfx', 'common/coat_of_arms', 'common/culture'],
    'ethnicity': ['common/ethnicities'],
    'religion family': ['common/religion/religion_family_types'],
    'graphical faith': ['gfx', 'common/religion'],
    'piety icon group': ['gfx/interface', 'gui', 'common/religion'],
    'terrain': ['common/terrain_types'],
    'modifier icon': ['gfx/interface/icons/modifiers'],
    'event theme': ['common/event_themes'],
    'men-at-arms': ['common/men_at_arms_types'],
    'trait': ['common/traits'],
    'government': ['common/governments'],
}
SKIP_DIRS = {'map_data'}


def mod_files():
    for mod in MODS:
        for path in mod.rglob('*.txt'):
            if not SKIP_DIRS.intersection(path.relative_to(mod).parts):
                yield path


def references():
    found = {}
    for path in mod_files():
        text = path.read_text(encoding='utf-8-sig', errors='replace')
        text = re.sub(r'#[^\n]*', '', text)
        for label, pattern in REFERENCES:
            if label == 'terrain' and path.name not in TERRAIN_FILES:
                continue
            if label == 'modifier icon' and path.parent.name not in MODIFIER_DIRS:
                continue
            for match in re.finditer(pattern, text, re.M):
                for key in match.group(1).split():
                    key = key.strip('"')
                    if '=' in key or key.isdigit() or key.startswith('$') or not key:
                        continue
                    found.setdefault((label, key), set()).add(path.relative_to(ROOT).as_posix())
    return found


def defined(root: Path, label: str, key: str, cache: dict) -> bool:
    if label == 'modifier icon':
        return any((base / 'gfx/interface/icons/modifiers' / f'{key}.dds').exists() for base in (root, *MODS))
    pattern = re.compile(rf'(?m)^\s*{re.escape(key)}\s*=|["\s/]{re.escape(key)}["\s./]')
    for folder in DEFINITIONS[label]:
        for base in (root, *MODS):
            directory = base / folder
            if not directory.exists():
                continue
            ck = (str(directory),)
            if ck not in cache:
                cache[ck] = '\n'.join(p.read_text(encoding='utf-8-sig', errors='replace')
                                      for p in directory.rglob('*') if p.suffix in ('.txt', '.gui', '.gfx', '.asset', '.yml')
                                      and p.stat().st_size < 4_000_000)
                cache[ck] += '\n' + '\n'.join(p.as_posix() for p in directory.rglob('*'))
            if pattern.search(cache[ck]):
                return True
    return False


def check(root: Path):
    cache = {}
    return {ref: files for ref, files in sorted(references().items()) if not defined(root, *ref, cache)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game-root', type=Path, default=overrides.DEFAULT_GAME)
    args = parser.parse_args()
    if not (args.game_root / 'common').exists():
        raise SystemExit('CK3 game files not found; set CK3_GAME_ROOT or pass --game-root')
    missing = check(args.game_root)
    total = len(references())
    for (label, key), files in missing.items():
        print(f'undefined {label}: {key}  ({", ".join(sorted(files))})')
    print(f'{total - len(missing)} of {total} vanilla key references are defined.')
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()
