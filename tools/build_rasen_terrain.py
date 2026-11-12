"""Paint Imperial Rasen's ground: terrain materials, colour tint and the zoomed-out paper map.

Without these the game draws Earth's ground textures and paper map over the new continent.
Everything is derived from files already generated for the map:

- gfx/map/terrain/detail_index.tga and detail_intensity.tga: for every map pixel, up to four
  terrain materials (indices into vanilla's materials.settings, which this mod does not replace)
  and their weights, which sum to 255. Each province takes the material of its terrain type;
  the highest mountain ground is snow-capped, plains are broken up with a second grass, and
  materials blend softly across province borders. Water is vanilla's sea-floor sand.
- gfx/map/terrain/colormap.dds: a soft colour tint per terrain.
- gfx/map/terrain/flat_maps/flatmap.dds and flatmap_tgp.dds: the source painting, placed where
  the map generator placed the continent; beyond the coastal waters it fades to open sea.
- gfx/map/water/watercolor_rgb_waterspec_a.dds, foam_map.dds and flowmap.dds: the sea's colour,
  foam mask and (still) currents for this coastline. Vanilla's carry Earth's continents.

Usage: python tools/build_rasen_terrain.py [--check]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

import numpy as np
import scipy.ndimage as nd
from PIL import Image, ImageFilter

import build_rasen_map as rasen

Image.MAX_IMAGE_PIXELS = None
OUT = rasen.OUT / 'gfx/map/terrain'
MAP = rasen.OUT / 'map_data'
TERRAIN = rasen.OUT / 'common/province_terrain/00_rasen_province_terrain.txt'

# Vanilla material names in the order of gfx/map/terrain/materials.settings (CK3 1.20.1); the
# index maps store positions in this list. test_rasen_terrain.py checks it against the game.
MATERIAL_INDEX = {
    'beach_02': 6, 'drylands_01': 18, 'farmland_01': 22, 'floodplains_01': 23, 'forest_jungle_01': 24,
    'forest_leaf_01': 25, 'forest_pine_01': 26, 'hills_01': 28, 'mountain_02': 38, 'mountain_02_snow': 46,
    'plains_01': 51, 'plains_01_noisy': 54, 'wetlands_02': 60,
}
TERRAIN_MATERIAL = {
    'plains': 'plains_01', 'farmlands': 'farmland_01', 'hills': 'hills_01', 'mountains': 'mountain_02',
    'drylands': 'drylands_01', 'forest': 'forest_leaf_01', 'jungle': 'forest_jungle_01', 'taiga': 'forest_pine_01',
    'wetlands': 'wetlands_02', 'floodplains': 'floodplains_01',
}
WATER = 'beach_02'
TINT = {
    'beach_02': (58, 78, 88), 'plains_01': (104, 116, 62), 'plains_01_noisy': (96, 112, 60), 'farmland_01': (124, 124, 66),
    'hills_01': (110, 104, 70), 'mountain_02': (104, 98, 90), 'mountain_02_snow': (200, 204, 208),
    'drylands_01': (140, 124, 84), 'forest_leaf_01': (66, 92, 50), 'forest_jungle_01': (52, 88, 46),
    'forest_pine_01': (70, 88, 66), 'wetlands_02': (78, 96, 70), 'floodplains_01': (110, 122, 64),
}
BLEND_RADIUS = 5          # pixels: how softly materials meet
SNOW_SHARE = 0.25         # the highest quarter of mountain ground is snow-capped
COLORMAP_SCALE = 4        # colormap.dds is a quarter of the map's size
FLATMAP_SCALE = 2
FLATMAP_SHORE, FLATMAP_FADE = 110, 60   # flatmap pixels of painted sea kept off the coast, then faded
STRIP = 256
# Water textures (RGBA), from vanilla's open-ocean and shallow-sea values.
WATER_DEEP, WATER_SHALLOW, WATER_SHELF = (22, 56, 60, 90), (34, 72, 76, 70), 40
FOAM_WATER, FOAM_LAND = (18, 255, 140, 255), (71, 0, 140, 255)


def province_materials():
    """Material name per province id (water where the terrain file has no entry)."""
    terrain = dict(re.findall(r'^(\d+)=(\w+)$', TERRAIN.read_text(encoding='utf-8-sig'), re.M))
    count = 0
    colours = {}
    for line in (MAP / 'definition.csv').read_text(encoding='utf-8-sig').splitlines():
        pid, r, g, b = line.split(';')[:4]
        colours[(int(r) << 16) | (int(g) << 8) | int(b)] = int(pid)
        count = max(count, int(pid))
    names = [WATER] * (count + 1)
    for pid, kind in terrain.items():
        names[int(pid)] = TERRAIN_MATERIAL[kind]
    return colours, names


def material_map():
    """Per pixel: an index into the sorted list of materials used."""
    colours, names = province_materials()
    used = sorted(MATERIAL_INDEX)
    rgb = np.asarray(Image.open(MAP / 'provinces.png').convert('RGB'))
    packed = (rgb[..., 0].astype(np.uint32) << 16) | (rgb[..., 1].astype(np.uint32) << 8) | rgb[..., 2]
    keys, inverse = np.unique(packed, return_inverse=True)
    table = np.array([used.index(names[colours[int(k)]]) for k in keys], np.uint8)
    material = table[inverse].reshape(packed.shape)
    height = np.asarray(Image.open(MAP / 'heightmap.png').convert('L'))
    mountain = material == used.index('mountain_02')
    if mountain.any():
        material[mountain & (height >= np.quantile(height[mountain], 1 - SNOW_SHARE))] = used.index('mountain_02_snow')
    # Break up the plains with a second grass, in broad soft patches.
    rng = np.random.default_rng(rasen.SEED + 11)
    coarse = Image.fromarray(rng.integers(0, 256, (material.shape[0] // 64, material.shape[1] // 64), np.uint8), 'L')
    patches = np.asarray(coarse.resize(material.shape[::-1], Image.BICUBIC)) > 150
    material[(material == used.index('plains_01')) & patches] = used.index('plains_01_noisy')
    return material, used


def detail_maps(material, used):
    """The index and intensity images (RGBA): the four heaviest materials per pixel, weights summing to 255."""
    blur = ImageFilter.GaussianBlur(BLEND_RADIUS)
    weights = [np.asarray(Image.fromarray((material == i).astype(np.uint8) * 255, 'L').filter(blur)) for i in range(len(used))]
    game_index = np.array([MATERIAL_INDEX[name] for name in used], np.uint8)
    index = np.empty(material.shape + (4,), np.uint8)
    intensity = np.empty(material.shape + (4,), np.uint8)
    for top in range(0, material.shape[0], STRIP):
        stack = np.stack([w[top:top + STRIP] for w in weights]).astype(np.int32)       # material, y, x
        # Ties go to the lower material position, so the result does not depend on sort internals.
        order = np.argsort(-(stack * 64) + np.arange(len(used))[:, None, None], axis=0, kind='stable')[:4]
        chosen = np.take_along_axis(stack, order, axis=0)
        chosen[0] = np.maximum(chosen[0], 1)
        scaled = chosen * 255 // chosen.sum(axis=0)
        scaled[0] += 255 - scaled.sum(axis=0)
        # A slot with no weight repeats the main material, so every index is a real material.
        slots = np.where(scaled > 0, order, order[0])
        index[top:top + STRIP] = np.moveaxis(game_index[slots], 0, -1)
        intensity[top:top + STRIP] = np.moveaxis(scaled.astype(np.uint8), 0, -1)
    return index, intensity


def colormap(material, used):
    small = Image.fromarray(material, 'L').resize((material.shape[1] // COLORMAP_SCALE, material.shape[0] // COLORMAP_SCALE), Image.NEAREST)
    palette = np.array([TINT[name] for name in used], np.uint8)
    tint = Image.fromarray(palette[np.asarray(small)], 'RGB').filter(ImageFilter.GaussianBlur(12))
    return tint.convert('RGBA')


def flatmap(land):
    """The source painting, placed exactly where build_rasen_map.project() put the continent."""
    spec = rasen.SPEC
    box = spec['content_box']
    sw, sh = box[2] - box[0], box[3] - box[1]
    scale = min((rasen.WIDTH - 2 * spec['margin']) / sw, (rasen.HEIGHT - 2 * spec['margin']) / sh)
    tw, th = int(sw * scale), int(sh * scale)
    ox, oy = (rasen.WIDTH - tw) // 2 + rasen.PAD_X, (rasen.HEIGHT - th) // 2 + rasen.PAD_Y
    painting = Image.open(rasen.SOURCE).convert('RGB').crop(tuple(box))
    # The painting's sea colour: the median of its clearly blue pixels.
    pixels = np.asarray(painting).reshape(-1, 3).astype(np.int16)
    sea = np.median(pixels[pixels[:, 2] > pixels[:, 0] + 40], axis=0)
    size = (rasen.MAP_WIDTH // FLATMAP_SCALE, rasen.MAP_HEIGHT // FLATMAP_SCALE)
    canvas = Image.new('RGB', size, tuple(int(v) for v in sea))
    canvas.paste(painting.resize((tw // FLATMAP_SCALE, th // FLATMAP_SCALE), Image.LANCZOS), (ox // FLATMAP_SCALE, oy // FLATMAP_SCALE))
    # Keep the painting near land and fade to open sea beyond it, which drops the painted frame.
    small = Image.fromarray((land * 255).astype(np.uint8), 'L').resize(size, Image.NEAREST)
    distance = nd.distance_transform_edt(np.asarray(small) == 0)
    keep = np.clip((FLATMAP_SHORE + FLATMAP_FADE - distance) / FLATMAP_FADE, 0, 1)
    painted = np.asarray(canvas).astype(np.int16)
    # Off the coast, anything that is not sea-blue is the frame.
    keep[(distance > 6) & (painted[..., 2] <= painted[..., 0] + 10)] = 0
    keep = keep[..., None]
    return Image.fromarray((painted * keep + sea * (1 - keep)).astype(np.uint8), 'RGB')


def water(land):
    """The sea's colour, foam and flow maps. Vanilla's have Earth's continents painted into them,
    so without these the sea is tinted like land wherever Earth has land."""
    size = (rasen.MAP_WIDTH // 2, rasen.MAP_HEIGHT // 2)
    small = np.asarray(Image.fromarray((land * 255).astype(np.uint8), 'L').resize(size, Image.BILINEAR)) > 127
    offshore = nd.distance_transform_edt(~small)
    # Colour (and specular in alpha): shallow teal at the coast, deepening over WATER_SHELF pixels.
    depth = np.clip(offshore / WATER_SHELF, 0, 1)[..., None]
    colour = (np.array(WATER_SHALLOW) * (1 - depth) + np.array(WATER_DEEP) * depth).astype(np.uint8)
    # Foam map: green marks water, as in vanilla's; the mask is softened at the shore.
    wet = np.asarray(Image.fromarray((~small).astype(np.uint8) * 255, 'L').filter(ImageFilter.GaussianBlur(2)))[..., None] / 255
    foam = (np.array(FOAM_WATER) * wet + np.array(FOAM_LAND) * (1 - wet)).astype(np.uint8)
    # Flow map: still water everywhere (neutral direction); alpha marks land.
    tiny = np.asarray(Image.fromarray(small.astype(np.uint8) * 255, 'L').resize((2048, 1024), Image.BILINEAR))
    flow = np.empty((1024, 2048, 4), np.uint8)
    flow[..., :3] = (127, 129, 255)
    flow[..., 3] = (tiny.astype(np.uint16) * 248 // 255).astype(np.uint8)
    return {
        '../water/watercolor_rgb_waterspec_a.dds': encode(Image.fromarray(colour, 'RGBA'), 'DDS', pixel_format='DXT5'),
        '../water/foam_map.dds': encode(Image.fromarray(foam, 'RGBA'), 'DDS', pixel_format='DXT5'),
        '../water/flowmap.dds': encode(Image.fromarray(flow, 'RGBA'), 'DDS', pixel_format='DXT5'),
    }


def encode(image, fmt, **options):
    buf = io.BytesIO()
    image.save(buf, format=fmt, **options)
    return buf.getvalue()


def render():
    material, used = material_map()
    index, intensity = detail_maps(material, used)
    land = material != used.index(WATER)
    paper = encode(flatmap(land).convert('RGBA'), 'DDS', pixel_format='DXT1')
    return water(land) | {
        # Run-length encoded, bottom-left origin like vanilla's: about 1% of the uncompressed size.
        'detail_index.tga': encode(Image.fromarray(index, 'RGBA'), 'TGA', compression='tga_rle', orientation=-1),
        'detail_intensity.tga': encode(Image.fromarray(intensity, 'RGBA'), 'TGA', compression='tga_rle', orientation=-1),
        'colormap.dds': encode(colormap(material, used), 'DDS', pixel_format='DXT5'),
        'flat_maps/flatmap.dds': paper,
        'flat_maps/flatmap_tgp.dds': paper,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if any image is missing or differs in pixels.')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = [name for name, data in files.items()
                 if not (OUT / name).exists()
                 or not np.array_equal(np.asarray(Image.open(OUT / name)), np.asarray(Image.open(io.BytesIO(data))))]
        if stale:
            raise SystemExit('Stale terrain images: ' + ', '.join(stale))
    else:
        for name, data in files.items():
            path = OUT / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print('Terrain: ' + ', '.join(f'{name} {len(data) // 1024} KB' for name, data in files.items()))


if __name__ == '__main__':
    main()
