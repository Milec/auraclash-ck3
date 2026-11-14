"""Pack AuraClash/map_data/heightmap.png into the files CK3 actually reads.

CK3 never reads heightmap.png directly. `topology = "heightmap.heightmap"` in default.map
points at a descriptor plus two images. This format was worked out from the CK3 1.20.1
vanilla files and verified by rebuilding vanilla tiles from them:

- **Tiles:** the heightmap is cut into 64 px tiles sampled as 65 x 65 (one pixel of
  overlap). A tile stored at compression level L is subsampled every 2^L pixels,
  giving (64 >> L) + 1 px.
- **indirection_heightmap.png:** RGBA, one pixel per tile, (R, G, 2^L, L). R and G
  are the tile's column and row inside level L's section of the packed image.
- **packed_heightmap.png:** 16-bit greyscale, stored bottom-up. Level L's section
  starts `level_offsets[L].y` rows from the bottom, so a tile's top row is
  `H - (offset_L + G * ts) - ts` and its left column is `R * ts`.

Each tile gets the coarsest level whose reconstruction stays within MAX_ERROR of the
source (16-bit units). Flat sea and plains compress well.

Usage: python tools/pack_heightmap.py [--check]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / 'AuraClash/map_data'
TILE = 64
LEVELS = 5            # 65, 33, 17, 9, 5 px
MAX_ERROR = 192       # 16-bit units (about 0.75 of an 8-bit step)
PACKED_TILES_WIDE = 64


def load_heightmap():
    img = Image.open(MAP / 'heightmap.png')
    a = np.asarray(img)
    if a.dtype == np.uint8:
        a = a.astype(np.uint16) * 257
    return a.astype(np.uint16)


def tile_samples(hm, ty, tx, level):
    step = 1 << level
    h, w = hm.shape
    ys = np.minimum(np.arange(ty * TILE, ty * TILE + TILE + 1, step), h - 1)
    xs = np.minimum(np.arange(tx * TILE, tx * TILE + TILE + 1, step), w - 1)
    return hm[np.ix_(ys, xs)]


def reconstruct_error(full, level):
    """Max error of bilinear reconstruction from a level-L subsample."""
    if level == 0:
        return 0
    step = 1 << level
    sub = full[::step, ::step].astype(np.float64)
    n = sub.shape[0]
    coords = np.arange(TILE + 1) / step
    i0 = np.minimum(np.floor(coords).astype(int), n - 2)
    f = coords - i0
    rows = sub[i0] * (1 - f)[:, None] + sub[i0 + 1] * f[:, None]
    up = rows[:, i0] * (1 - f)[None, :] + rows[:, i0 + 1] * f[None, :]
    return float(np.abs(up - full).max())


def render():
    hm = load_heightmap()
    h, w = hm.shape
    if h % TILE or w % TILE:
        raise SystemExit(f'heightmap {w}x{h} must be a multiple of {TILE}')
    tiles_y, tiles_x = h // TILE, w // TILE
    level_of = np.zeros((tiles_y, tiles_x), dtype=int)
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            full = tile_samples(hm, ty, tx, 0).astype(np.float64)
            level = 0
            for candidate in range(LEVELS - 1, 0, -1):
                if reconstruct_error(full, candidate) <= MAX_ERROR:
                    level = candidate
                    break
            level_of[ty, tx] = level
    width = PACKED_TILES_WIDE * (TILE + 1)
    per_row = [min(255, width // ((TILE >> lv) + 1)) for lv in range(LEVELS)]
    counts = [int((level_of == lv).sum()) for lv in range(LEVELS)]
    rows = [-(-c // per_row[lv]) if c else 0 for lv, c in enumerate(counts)]
    offsets, y = [], 0
    for lv in range(LEVELS):
        offsets.append(y)
        y += rows[lv] * ((TILE >> lv) + 1)
    height = max(y, 1)
    packed = np.zeros((height, width), dtype=np.uint16)
    indirection = np.zeros((tiles_y, tiles_x, 4), dtype=np.uint8)
    slot = [0] * LEVELS
    empty = None
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            lv = level_of[ty, tx]
            ts = (TILE >> lv) + 1
            r, g = slot[lv] % per_row[lv], slot[lv] // per_row[lv]
            slot[lv] += 1
            top = height - (offsets[lv] + g * ts) - ts
            data = tile_samples(hm, ty, tx, lv)
            packed[top:top + ts, r * ts:r * ts + ts] = data
            indirection[ty, tx] = (r, g, 1 << lv, lv)
            # The descriptor's empty tile: the first flat tile at the coarsest level.
            if empty is None and lv == LEVELS - 1 and data.max() == data.min():
                empty = (r, g)
    empty = empty or (0, 0)

    def png(array, mode):
        buf = io.BytesIO()
        # Pillow infers I;16 for uint16 and RGBA for four uint8 channels.
        Image.fromarray(array).save(buf, format='PNG', optimize=False, compress_level=9)
        return buf.getvalue()

    descriptor = '\n'.join([
        '﻿heightmap_file="map_data/packed_heightmap.png"',
        'indirection_file="map_data/indirection_heightmap.png"',
        f'original_heightmap_size={{ {w} {h} }}',
        f'tile_size={TILE + 1}',
        'should_wrap_x=no',
        'level_offsets={ ' + ' '.join(f'{{ 0 {o} }}' for o in offsets) + ' }',
        f'max_compress_level={LEVELS - 1}',
        f'empty_tile_offset={{ {empty[0]} {empty[1]} }}',
        '',
    ])
    summary = dict(tiles=int(tiles_x * tiles_y), per_level=counts, packed=(width, height))
    return {
        'heightmap.heightmap': descriptor.encode('utf-8'),
        'packed_heightmap.png': (packed, 'I;16'),
        'indirection_heightmap.png': (indirection, 'RGBA'),
    }, summary, png


def unpack(descriptor_offsets, packed, indirection):
    """Rebuild the full heightmap from packed files (used by the test)."""
    tiles_y, tiles_x = indirection.shape[:2]
    out = np.zeros((tiles_y * TILE, tiles_x * TILE), dtype=np.float64)
    H = packed.shape[0]
    for ty in range(tiles_y):
        for tx in range(tiles_x):
            r, g, _, lv = (int(v) for v in indirection[ty, tx])
            ts = (TILE >> lv) + 1
            top = H - (descriptor_offsets[lv] + g * ts) - ts
            sub = packed[top:top + ts, r * ts:r * ts + ts].astype(np.float64)
            step = 1 << lv
            coords = np.arange(TILE) / step
            i0 = np.minimum(np.floor(coords).astype(int), ts - 2) if ts > 1 else np.zeros(TILE, int)
            f = coords - i0
            rows = sub[i0] * (1 - f)[:, None] + sub[i0 + 1] * f[:, None]
            out[ty * TILE:(ty + 1) * TILE, tx * TILE:(tx + 1) * TILE] = rows[:, i0] * (1 - f)[None, :] + rows[:, i0 + 1] * f[None, :]
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if the packed files are missing or differ in content.')
    args = parser.parse_args()
    files, summary, png = render()
    if args.check:
        stale = []
        if (MAP / 'heightmap.heightmap').read_bytes() != files['heightmap.heightmap'] if (MAP / 'heightmap.heightmap').exists() else True:
            stale.append('heightmap.heightmap')
        for name in ('packed_heightmap.png', 'indirection_heightmap.png'):
            path = MAP / name
            array, _ = files[name]
            if not path.exists() or not np.array_equal(np.asarray(Image.open(path)), array):
                stale.append(name)
        if stale:
            raise SystemExit('Stale packed heightmap files: ' + ', '.join(stale))
    else:
        (MAP / 'heightmap.heightmap').write_bytes(files['heightmap.heightmap'])
        for name in ('packed_heightmap.png', 'indirection_heightmap.png'):
            array, mode = files[name]
            (MAP / name).write_bytes(png(array, mode))
    print(summary)


if __name__ == '__main__':
    main()
