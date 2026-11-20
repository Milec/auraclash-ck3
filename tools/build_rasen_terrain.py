"""Paint Imperial Rasen's ground: terrain materials, colour tint and the zoomed-out paper map.

Without these the game draws Earth's ground textures and paper map over the new continent.
Everything is derived from files already generated for the map:

- gfx/map/terrain/detail_index.tga and detail_intensity.tga: for every map pixel, up to four
  terrain materials (indices into vanilla's materials.settings, which this mod does not replace)
  and their weights, which sum to 255. Each province takes its terrain type's ground in its
  region's colours; over that, the source painting's drawn trees, peaks and snow show through
  (build_rasen_map.biome_layers). Plains are broken up with a second grass, and materials blend
  softly. Water is vanilla's sea-floor sand.
- gfx/map/terrain/colormap.dds: a soft colour tint per terrain.
- gfx/map/terrain/flat_maps/flatmap.dds and flatmap_tgp.dds: a paper map drawn from the terrain
  (parchment, ground wash, relief shading, inked coast), without the painting's labels or icons.
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
    'beach_02': 6, 'desert_01': 11, 'drylands_01': 18, 'farmland_01': 22, 'floodplains_01': 23,
    'forest_jungle_01': 24, 'forest_leaf_01': 25, 'forest_pine_01': 26, 'hills_01': 28, 'hills_01_rocks': 29,
    'medi_farmlands': 34, 'northern_plains_01': 39, 'plains_01': 41, 'plains_01_dry': 42, 'plains_01_noisy': 44,
    'snow': 46, 'steppe_grass': 48, 'wetlands_02': 50, 'wetlands_02_mud': 51, 'central_mountain': 52,
}
TERRAIN_MATERIAL = {
    'plains': 'plains_01', 'farmlands': 'farmland_01', 'hills': 'hills_01', 'mountains': 'central_mountain',
    'drylands': 'drylands_01', 'forest': 'forest_leaf_01', 'jungle': 'forest_jungle_01', 'taiga': 'forest_pine_01',
    'wetlands': 'wetlands_02', 'floodplains': 'floodplains_01', 'desert': 'desert_01',
}
# Regional ground, as the painting colours it: the frozen north's pale grass, the Outer East's
# steppe, the Mystic Lands' golden fields, the Bladed Lands' dry plains, the Cursed Lands' mud.
REGION_MATERIAL = {
    ('outer_north', 'plains'): 'northern_plains_01', ('sacred', 'plains'): 'northern_plains_01',
    ('outer_east', 'plains'): 'steppe_grass', ('mystic', 'farmlands'): 'medi_farmlands',
    ('bladed', 'plains'): 'plains_01_dry', ('cursed', 'wetlands'): 'wetlands_02_mud',
}
WATER = 'beach_02'
TINT = {
    'beach_02': (58, 78, 88), 'plains_01': (104, 116, 62), 'plains_01_noisy': (96, 112, 60), 'farmland_01': (124, 124, 66),
    'hills_01': (110, 104, 70), 'hills_01_rocks': (112, 106, 92), 'central_mountain': (104, 98, 90), 'snow': (214, 218, 224),
    'drylands_01': (140, 124, 84), 'forest_leaf_01': (66, 92, 50), 'forest_jungle_01': (44, 92, 44),
    'forest_pine_01': (62, 82, 66), 'wetlands_02': (78, 96, 70), 'wetlands_02_mud': (82, 78, 62), 'floodplains_01': (110, 122, 64),
    'desert_01': (176, 152, 104), 'medi_farmlands': (150, 136, 72), 'northern_plains_01': (120, 128, 100),
    'plains_01_dry': (132, 124, 74), 'steppe_grass': (128, 128, 76),
}
BLEND_RADIUS = 5          # pixels: how softly materials meet
SNOW_SHARE = 0.25         # in the frozen lands, the highest quarter of mountain ground is snow-capped
COLORMAP_SCALE = 4        # colormap.dds is a quarter of the map's size
FLATMAP_SCALE = 2
STRIP = 256
# The paper map: parchment, ink at the coast, land washed with its ground's colour and shaded by relief.
PARCHMENT, SEA_PAPER, INK = (226, 210, 172), (196, 196, 172), (74, 56, 40)
PAPER_WASH, HILLSHADE = 0.5, 0.55
# Water textures (RGBA), from vanilla's open-ocean and shallow-sea values.
WATER_DEEP, WATER_SHALLOW, WATER_SHELF = (22, 56, 60, 90), (34, 72, 76, 70), 40
FOAM_WATER, FOAM_LAND = (18, 255, 140, 255), (71, 0, 140, 255)


def province_kinds():
    """Terrain type per province id (None for water, which has no entry in the terrain file)."""
    terrain = dict(re.findall(r'^(\d+)=(\w+)$', TERRAIN.read_text(encoding='utf-8-sig'), re.M))
    count = 0
    colours = {}
    for line in (MAP / 'definition.csv').read_text(encoding='utf-8-sig').splitlines():
        pid, r, g, b = line.split(';')[:4]
        colours[(int(r) << 16) | (int(g) << 8) | int(b)] = int(pid)
        count = max(count, int(pid))
    kinds = [None] * (count + 1)
    for pid, kind in terrain.items():
        kinds[int(pid)] = kind
    return colours, kinds


def material_map():
    """Per pixel: an index into the sorted list of materials used.

    Each province takes its terrain type's ground, in its region's colours. Over that, the painting's
    own drawing shows through: where it draws trees there is forest, where it draws peaks there is
    rock, and where it paints snow and ice in the frozen north there is snow.
    """
    colours, kinds = province_kinds()
    used = sorted(MATERIAL_INDEX)
    at = used.index
    regions, tree, rock, snow = rasen.biome_layers()
    region_key = {v: k for k, v in rasen.REGION_INDEX.items()}
    rgb = np.asarray(Image.open(MAP / 'provinces.png').convert('RGB'))
    packed = (rgb[..., 0].astype(np.uint32) << 16) | (rgb[..., 1].astype(np.uint32) << 8) | rgb[..., 2]
    del rgb
    keys, inverse = np.unique(packed, return_inverse=True)
    del packed
    kind_names = sorted(TERRAIN_MATERIAL)
    kind_table = np.array([kind_names.index(k) + 1 if (k := kinds[colours[int(c)]]) else 0 for c in keys], np.uint8)
    kind = kind_table[inverse].reshape(regions.shape)
    del inverse
    # Ground by (terrain type, region).
    material = np.full(regions.shape, at(WATER), np.uint8)
    for code in np.unique(kind[kind > 0]):
        name = kind_names[code - 1]
        here = kind == code
        for region in np.unique(regions[here]):
            ground = TERRAIN_MATERIAL[name]
            if region in region_key:
                ground = REGION_MATERIAL.get((region_key[region], name), ground)
            material[here & (regions == region)] = at(ground)
    land = kind > 0
    # The painting's trees: each region's own forest.
    for region, key in region_key.items():
        forest = TERRAIN_MATERIAL[rasen.BIOME_TERRAIN[key][1]]
        material[land & (regions == region) & (tree > rasen.FOREST_CUT)] = at(forest)
    # The painting's peaks: mountain rock in high country, a rocky rise elsewhere.
    high = np.isin(kind, [kind_names.index(k) + 1 for k in ('mountains', 'hills')])
    peaks = land & (rock > rasen.ROCK_CUT)
    material[peaks & high] = at('central_mountain')
    material[peaks & ~high] = at('hills_01_rocks')
    # Snow and ice where the painting has them, and on the frozen lands' highest mountains.
    frozen = land & np.isin(regions, [rasen.REGION_INDEX[k] for k in rasen.SNOWY])
    material[frozen & (snow > rasen.SNOW_CUT)] = at('snow')
    height = np.asarray(Image.open(MAP / 'heightmap.png').convert('L'))
    peak = frozen & (material == at('central_mountain'))
    if peak.any():
        material[peak & (height >= np.quantile(height[peak], 1 - SNOW_SHARE))] = at('snow')
    # Break up the plains with a second grass, in broad soft patches.
    rng = np.random.default_rng(rasen.SEED + 11)
    coarse = Image.fromarray(rng.integers(0, 256, (material.shape[0] // 64, material.shape[1] // 64), np.uint8), 'L')
    patches = np.asarray(coarse.resize(material.shape[::-1], Image.BICUBIC)) > 150
    material[(material == at('plains_01')) & patches] = at('plains_01_noisy')
    return material, used, height


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


def flatmap(material, used, height):
    """The zoomed-out paper map, drawn from the terrain itself: no painted labels or icons.

    Parchment, the land washed with its ground's colour and shaded by relief, an inked coast
    and a faint band of shallows; the realm map modes draw their own colours and names over it.
    """
    size = (rasen.MAP_WIDTH // FLATMAP_SCALE, rasen.MAP_HEIGHT // FLATMAP_SCALE)
    small = np.asarray(Image.fromarray(material, 'L').resize(size, Image.NEAREST))
    land = small != used.index(WATER)
    palette = np.array([TINT[name] for name in used], np.float32)
    wash = np.asarray(Image.fromarray(palette[small].astype(np.uint8), 'RGB').filter(ImageFilter.GaussianBlur(3)), np.float32)
    paper = np.array(PARCHMENT, np.float32)
    ground = paper * (1 - PAPER_WASH) + wash * PAPER_WASH
    # Relief, lit from the north-west.
    relief = nd.gaussian_filter(np.asarray(Image.fromarray(height).resize(size, Image.BILINEAR), np.float32), 2)
    gy, gx = np.gradient(relief)
    slope = -(gx + gy)
    slope /= np.percentile(np.abs(slope[land]), 99) + 1e-6
    shade = 1 + HILLSHADE * 0.3 * np.clip(slope, -1, 1)
    ground *= shade[..., None]
    # The sea: paler paper, darkening a little in the shallows; ink along the coast.
    offshore = nd.distance_transform_edt(~land)
    sea = np.array(SEA_PAPER, np.float32) * (1 - 0.08 * np.clip(1 - offshore / 24, 0, 1))[..., None]
    image = np.where(land[..., None], ground, sea)
    ink = np.clip(1 - np.abs(nd.distance_transform_edt(land) - offshore) / 1.5, 0, 1)
    image = image * (1 - 0.8 * ink[..., None]) + np.array(INK, np.float32) * 0.8 * ink[..., None]
    # Paper grain in broad soft blotches.
    rng = np.random.default_rng(rasen.SEED + 13)
    grain = np.asarray(Image.fromarray(rng.integers(0, 256, (size[1] // 32, size[0] // 32), np.uint8), 'L').resize(size, Image.BICUBIC), np.float32)
    image *= (0.97 + 0.06 * grain / 255)[..., None]
    return Image.fromarray(np.clip(image, 0, 255).astype(np.uint8), 'RGB')


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
    material, used, height = material_map()
    index, intensity = detail_maps(material, used)
    land = material != used.index(WATER)
    paper = encode(flatmap(material, used, height).convert('RGBA'), 'DDS', pixel_format='DXT1')
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
