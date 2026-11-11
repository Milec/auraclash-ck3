"""Bookmark art for Imperial Rasen, cut from the painted world map.

CK3 shows a 1920x1080 background for each bookmark and a 1920x1080 "location" image for
each featured character. This writes, from assets/map/imperial_rasen_source.jpg:
  RasenMap/gfx/interface/bookmarks/bm_rasen_trials.dds              (the whole world)
  RasenMap/gfx/interface/bookmarks/bm_rasen_trials_bm_rasen_<land>.dds  (each Exalt's land)
Each land image is centred on that kingdom, found from the generated provinces and titles
and mapped back onto the painting through the map builder's projection.

Usage: python tools/build_rasen_bookmark_art.py [--check]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance

import build_rasen_map as rasen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'RasenMap/gfx/interface/bookmarks'
SIZE = (1920, 1080)
LANDS = ['bladed', 'sacred', 'mystic', 'cursed', 'wild', 'azuma']
ZOOM = 0.42  # fraction of the painting's content width shown in a land image


def kingdom_centres():
    """Centre of each kingdom in map pixels, from provinces.png and the barony provinces."""
    titles = (rasen.OUT / 'common/landed_titles/00_rasen_titles.txt').read_text(encoding='utf-8-sig')
    colour = {}
    for line in (rasen.OUT / 'map_data/definition.csv').read_text(encoding='utf-8-sig').splitlines():
        parts = line.split(';')
        if len(parts) > 3 and parts[0].isdigit():
            colour[int(parts[0])] = (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])
    a = np.asarray(Image.open(rasen.OUT / 'map_data/provinces.png')).astype(np.uint32)
    key = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    centres = {}
    for land in LANDS:
        start = titles.index(f'k_{land} = {{')
        nxt = re.search(r'(?m)^\tk_\w+ = \{', titles[start + 5:])
        block = titles[start:start + 5 + nxt.start()] if nxt else titles[start:]
        wanted = np.array([colour[int(p)] for p in re.findall(r'province = (\d+)', block)], dtype=np.uint32)
        ys, xs = np.nonzero(np.isin(key, wanted))
        centres[land] = (float(xs.mean()), float(ys.mean()))
    return centres


def to_source(x, y):
    """Map pixel -> painting pixel (inverse of build_rasen_map.project plus the ocean padding)."""
    box = rasen.SPEC['content_box']
    sw, sh = box[2] - box[0], box[3] - box[1]
    scale = min((rasen.WIDTH - 2 * rasen.SPEC['margin']) / sw, (rasen.HEIGHT - 2 * rasen.SPEC['margin']) / sh)
    ox, oy = (rasen.WIDTH - int(sw * scale)) // 2, (rasen.HEIGHT - int(sh * scale)) // 2
    return (x - rasen.PAD_X - ox) / scale + box[0], (y - rasen.PAD_Y - oy) / scale + box[1]


def crop(image, cx, cy, width):
    """A 16:9 window of the given width centred on (cx, cy), kept inside the image."""
    height = width * SIZE[1] / SIZE[0]
    left = min(max(cx - width / 2, 0), image.width - width)
    top = min(max(cy - height / 2, 0), image.height - height)
    return image.crop((round(left), round(top), round(left + width), round(top + height))).resize(SIZE, Image.LANCZOS)


def dds(image):
    buf = io.BytesIO()
    image.convert('RGBA').save(buf, format='DDS', pixel_format='DXT5')
    return buf.getvalue()


def render():
    painting = Image.open(rasen.SOURCE).convert('RGB')
    box = rasen.SPEC['content_box']
    files = {}
    # Background: the whole spiral continent, slightly darkened so the UI stays readable.
    width = min(painting.width, (box[3] - box[1]) * SIZE[0] / SIZE[1])
    world = crop(painting, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, width)
    files['bm_rasen_trials.dds'] = dds(ImageEnhance.Brightness(world).enhance(0.8))
    for land, (x, y) in kingdom_centres().items():
        sx, sy = to_source(x, y)
        files[f'bm_rasen_trials_bm_rasen_{land}.dds'] = dds(crop(painting, sx, sy, (box[2] - box[0]) * ZOOM))
    return files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if any image is missing or differs in pixels.')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = []
        for name, data in files.items():
            path = OUT / name
            if not path.exists() or not np.array_equal(np.asarray(Image.open(path)), np.asarray(Image.open(io.BytesIO(data)))):
                stale.append(name)
        if stale:
            raise SystemExit('Stale bookmark art: ' + ', '.join(stale))
    else:
        OUT.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (OUT / name).write_bytes(data)
    print(f'Bookmark art: {len(files)} images.')


if __name__ == '__main__':
    main()
