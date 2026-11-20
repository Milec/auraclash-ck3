"""Draw Imperial Rasen's rivers into CK3's rivers.png (called by build_rasen_map.py).

CK3's river map is 8-bit indexed: 255 land, 254 water, and rivers as 1-pixel lines joined
edge to edge (4-connected). Each river starts with a source pixel (0) and ends either touching
water or, for a tributary, with a merge pixel (1) beside the river it joins. Indices 3 and up
are widths, 3 the thinnest (vanilla's rivers are mostly 3 to 6, widening downstream).

The rivers follow Rasen's heightmap down to the sea:
- the land is drained on a coarse grid (STEP pixels a cell) by a priority flood from the coast,
  which gives every cell a downhill path to the sea even across flat ground; smooth noise added
  to the height makes the rivers meander;
- sources are high, inland cells, spaced by region: Outer West, "thousands of rivers" between
  its karst mountains (Aura Clash Core Rulebook), has the most; the Outer South dunes the fewest;
- each source flows down until it reaches the sea or a river already drawn, which it joins;
- a river widens with the number of sources upstream.
Cells are STEP pixels apart and stay COAST pixels from water, so two rivers never run side by side
and none brushes the shore except at its mouth.
"""
from __future__ import annotations

import heapq

import numpy as np
from scipy import ndimage as nd

STEP = 4
COAST = 7
# Minimum distance between river sources, in cells, by region (the default for others).
SPACING = {'outer_west': 12, 'outer_south': 40, 'azuma': 30, 'wild': 16, 'cursed': 16}
DEFAULT_SPACING = 22
MIN_LENGTH = 14          # cells; shorter streams are left out
MEANDER = ((2.5, 6.0), (8.0, 10.0))  # (cells, height units) of noise added to the drained height
SEED = 3000
WIDTHS = (3, 4, 5, 6, 9)  # by sources upstream: 1, 2-3, 4-7, 8-15, 16+
SOURCE, MERGE, WATER, LAND = 0, 1, 254, 255
NEIGHBOURS = ((0, 1), (1, 0), (0, -1), (-1, 0))


def drain(height: np.ndarray, inland: np.ndarray, sea: np.ndarray):
    """Priority flood from the coastal cells: each inland cell's next cell towards the sea."""
    rows, cols = inland.shape
    parent = np.full(inland.shape + (2,), -1, np.int32)
    done = ~inland
    queue = []
    for y, x in zip(*np.nonzero(inland & nd.binary_dilation(sea))):
        for dy, dx in NEIGHBOURS:
            ny, nx = y + dy, x + dx
            if 0 <= ny < rows and 0 <= nx < cols and sea[ny, nx]:
                parent[y, x] = (ny, nx)
                break
        done[y, x] = True
        heapq.heappush(queue, (float(height[y, x]), int(y), int(x)))
    while queue:
        level, y, x = heapq.heappop(queue)
        for dy, dx in NEIGHBOURS:
            ny, nx = y + dy, x + dx
            if 0 <= ny < rows and 0 <= nx < cols and not done[ny, nx]:
                done[ny, nx] = True
                parent[ny, nx] = (y, x)
                heapq.heappush(queue, (max(level, float(height[ny, nx])), ny, nx))
    return parent


def draw(index: np.ndarray, height: np.ndarray, provinces: np.ndarray, region_of: dict) -> np.ndarray:
    """Return a copy of the land/water index map with rivers drawn on it."""
    out = index.copy()
    water = index == WATER
    from_water = nd.distance_transform_edt(~water)
    centre = (slice(STEP // 2, None, STEP), slice(STEP // 2, None, STEP))
    cell_far = from_water[centre]
    rows, cols = cell_far.shape
    inland = cell_far >= COAST
    sea = ~inland
    smooth = nd.gaussian_filter(height.astype(np.float32), 6)[centre]
    # Smooth noise makes the rivers meander instead of running straight across flat ground.
    rng = np.random.default_rng(SEED)
    for sigma, amount in MEANDER:
        field = nd.gaussian_filter(rng.standard_normal(smooth.shape).astype(np.float32), sigma)
        smooth = smooth + field / (field.std() or 1) * amount
    parent = drain(smooth, inland, sea)
    cell_province = provinces[centre]
    region = np.vectorize(lambda p: region_of.get(int(p), ''), otypes=[object])(cell_province)

    # Sources: the highest inland cells first, each far enough from those already chosen.
    order = np.argsort(-smooth, axis=None)
    taken = np.zeros(inland.shape, bool)
    sources = []
    for flat in order:
        y, x = divmod(int(flat), cols)
        if not inland[y, x] or cell_far[y, x] < COAST * 3 or taken[y, x]:
            continue
        spacing = SPACING.get(region[y, x], DEFAULT_SPACING)
        sources.append((y, x))
        taken[max(0, y - spacing):y + spacing + 1, max(0, x - spacing):x + spacing + 1] = True

    def fine(cell):
        return cell[0] * STEP + STEP // 2, cell[1] * STEP + STEP // 2

    def mouth(cell):
        """From a last inland cell's centre down the distance to the sea, until it touches water."""
        y, x = fine(cell)
        walk = []
        for _ in range(COAST * 4):
            walk.append((y, x))
            if any(water[y + dy, x + dx] for dy, dx in NEIGHBOURS):
                return walk
            y, x = min(((y + dy, x + dx) for dy, dx in NEIGHBOURS), key=lambda q: from_water[q])
            if (y, x) in walk:
                return None
        return None

    river = np.zeros(inland.shape, np.int32)   # cell -> river number + 1
    flow = np.zeros(inland.shape, np.int32)
    head = set()
    near_mouths = set()
    paths = []
    for y, x in sources:
        path, cell = [], (y, x)
        while inland[cell] and not river[cell]:
            path.append(cell)
            cell = tuple(parent[cell])
        joins = bool(inland[cell] and river[cell])
        if len(path) < MIN_LENGTH or (joins and cell in head):
            continue
        end = None
        if not joins:
            end = mouth(path[-1])
            if end is None or any(q in near_mouths for q in end):
                continue
            for qy, qx in end:
                near_mouths.update((qy + dy, qx + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        number = len(paths) + 1
        for c in path:
            river[c] = number
            flow[c] += 1
        head.add(path[0])
        paths.append((path, cell if joins else None, end))
        # Everything downstream carries this source's water too.
        while joins:
            flow[cell] += 1
            cell = tuple(parent[cell])
            joins = bool(inland[cell])

    def width(cell):
        return WIDTHS[min(len(WIDTHS) - 1, int(np.log2(max(int(flow[cell]), 1))))]

    for path, joined, end in paths:
        pixels = []
        for a, b in zip(path, path[1:] + ([joined] if joined else [])):
            (ay, ax), (by, bx) = fine(a), fine(b)
            dy, dx = np.sign(by - ay), np.sign(bx - ax)
            pixels += [((ay + dy * i, ax + dx * i), width(a)) for i in range(STEP)]
        if end:
            pixels += [(q, width(path[-1])) for q in end]
        for q, w in pixels:
            out[q] = w
        out[pixels[0][0]] = SOURCE
        if joined is not None:
            out[pixels[-1][0]] = MERGE
    return out
