"""Read Imperial Rasen's built map back as data: titles, terrain, sea zones and the province graph.

Shared by the builders that place things on the finished map (tools/build_rasen_trade.py,
tools/build_rasen_roads.py). Reads only the generated files under AuraClash/, never the
source painting, so it stays fast and agrees with what the game loads.
"""
from __future__ import annotations

import csv
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'AuraClash'
TITLES = MOD / 'common/landed_titles/00_rasen_titles.txt'
TERRAIN = MOD / 'common/province_terrain/00_rasen_province_terrain.txt'
DEFAULT_MAP = MOD / 'map_data/default.map'
DEFINITION = MOD / 'map_data/definition.csv'
PROVINCES = MOD / 'map_data/provinces.png'
ADJACENCIES = MOD / 'map_data/adjacencies.csv'


@lru_cache(maxsize=None)
def titles() -> dict[str, dict]:
    """Every landed title below the hegemony: key -> {'tier', 'parent', 'kingdom', 'capital', 'provinces'}.

    'provinces' lists a county's barony provinces in file order (the first is its seat);
    'capital' is the county key a duchy or kingdom names as capital.
    """
    text = re.sub(r'#.*', '', TITLES.read_text(encoding='utf-8-sig'))
    found: dict[str, dict] = {}
    stack: list[str] = []
    for token in re.finditer(r'(\w+)\s*=\s*\{|\}|\b(province|capital)\s*=\s*(\w+)', text):
        if token.group(0) == '}':
            if stack:
                stack.pop()
            continue
        if token.group(2):
            owner = next((t for t in reversed(stack) if t in found), None)
            if owner is None:
                continue
            if token.group(2) == 'province':
                county = next((t for t in reversed(stack) if t.startswith('c_')), None)
                if county:
                    found[county]['provinces'].append(int(token.group(3)))
            elif owner == stack[-1]:
                found[owner]['capital'] = token.group(3)
            continue
        name = token.group(1)
        if re.match(r'^[ekdcb]_', name):
            parent = next((t for t in reversed(stack) if t in found), None)
            kingdom = name if name.startswith('k_') else (found[parent]['kingdom'] if parent else None)
            found[name] = {'tier': name[0], 'parent': parent, 'kingdom': kingdom, 'capital': None, 'provinces': []}
        stack.append(name)
    return found


def counties() -> dict[str, dict]:
    """County key -> {'region': kingdom suffix, 'duchy', 'provinces'} for every county with land."""
    out = {}
    for key, info in titles().items():
        if info['tier'] == 'c' and info['provinces'] and info['kingdom']:
            out[key] = {'region': info['kingdom'][2:], 'duchy': info['parent'], 'provinces': info['provinces']}
    return out


@lru_cache(maxsize=None)
def terrain() -> dict:
    text = TERRAIN.read_text(encoding='utf-8-sig')
    out: dict = {int(a): b for a, b in re.findall(r'^\s*(\d+)\s*=\s*(\w+)', text, re.M)}
    out['default'] = re.search(r'default_land\s*=\s*(\w+)', text).group(1)
    return out


def terrain_of(province: int) -> str:
    table = terrain()
    return table.get(province, table['default'])


@lru_cache(maxsize=None)
def water_ids() -> frozenset[int]:
    """Sea zones, impassable seas and lakes."""
    text = DEFAULT_MAP.read_text(encoding='utf-8-sig')
    ids: set[int] = set()
    for kind, body in re.findall(r'^(?:sea_zones|impassable_seas|lakes)\s*=\s*(RANGE|LIST)\s*\{([^}]*)\}', text, re.M):
        numbers = [int(n) for n in body.split()]
        ids.update(range(numbers[0], numbers[1] + 1) if kind == 'RANGE' else numbers)
    return frozenset(ids)


@lru_cache(maxsize=None)
def impassable_seas() -> frozenset[int]:
    text = DEFAULT_MAP.read_text(encoding='utf-8-sig')
    ids: set[int] = set()
    for kind, body in re.findall(r'^impassable_seas\s*=\s*(RANGE|LIST)\s*\{([^}]*)\}', text, re.M):
        numbers = [int(n) for n in body.split()]
        ids.update(range(numbers[0], numbers[1] + 1) if kind == 'RANGE' else numbers)
    return frozenset(ids)


@lru_cache(maxsize=None)
def _grid():
    import numpy as np
    from PIL import Image
    colours = {}
    for line in DEFINITION.read_text(encoding='utf-8-sig').splitlines()[1:]:
        parts = line.split(';')
        if len(parts) >= 4 and parts[0].isdigit():
            colours[(int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])] = int(parts[0])
    pixels = np.asarray(Image.open(PROVINCES).convert('RGB'), dtype=np.uint32)
    packed = (pixels[..., 0] << 16) | (pixels[..., 1] << 8) | pixels[..., 2]
    keys = np.array(sorted(colours), dtype=np.uint32)
    ids = np.array([colours[k] for k in keys.tolist()], dtype=np.int32)
    index = np.searchsorted(keys, packed)
    index[index >= len(keys)] = 0
    return np.where(keys[index] == packed, ids[index], 0)


@lru_cache(maxsize=None)
def neighbours() -> dict[int, frozenset[int]]:
    """Province adjacency from the province map, plus the crossings in adjacencies.csv."""
    import numpy as np
    grid = _grid()
    pairs = set()
    for a, b in ((grid[:, 1:], grid[:, :-1]), (grid[1:, :], grid[:-1, :])):
        mask = (a != b) & (a > 0) & (b > 0)
        stacked = np.unique(np.stack([a[mask], b[mask]], axis=1), axis=0)
        pairs.update(map(tuple, stacked.tolist()))
    graph: dict[int, set[int]] = {}
    for a, b in pairs:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    if ADJACENCIES.exists():
        for row in csv.reader(ADJACENCIES.read_text(encoding='utf-8-sig').splitlines(), delimiter=';'):
            if len(row) > 2 and row[0].lstrip('-').isdigit() and int(row[0]) > 0 and row[1].isdigit():
                a, b = int(row[0]), int(row[1])
                graph.setdefault(a, set()).add(b)
                graph.setdefault(b, set()).add(a)
    return {k: frozenset(v) for k, v in graph.items()}


@lru_cache(maxsize=None)
def centres() -> dict[int, tuple[float, float]]:
    """Province centroid in map pixels (x, y)."""
    import numpy as np
    grid = _grid()
    flat = grid.ravel()
    count = np.bincount(flat)
    ys, xs = np.indices(grid.shape)
    sx = np.bincount(flat, weights=xs.ravel())
    sy = np.bincount(flat, weights=ys.ravel())
    return {int(i): (float(sx[i] / count[i]), float(sy[i] / count[i])) for i in np.nonzero(count)[0] if i > 0}


def coastal_provinces() -> set[int]:
    water = water_ids()
    return {p for p, around in neighbours().items() if p not in water and any(n in water for n in around)}
