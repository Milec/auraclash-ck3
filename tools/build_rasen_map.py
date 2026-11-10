"""Generate the Imperial Rasen map data from the painted Aura Clash world map.

The source painting (assets/map/imperial_rasen_source.jpg) is classified into
water and land, land is split into the five Inner Kingdoms, Azuma Honsha and
the four Outer provinces, and each region is divided into compact provinces.
The result is written to RasenMap/ (a separate overhaul mod) as:

  map_data/provinces.png, definition.csv, default.map, heightmap.png,
  adjacencies.csv, island_region.txt, geographical_region.txt
  common/landed_titles/00_rasen_titles.txt
  localization/english/rasen_titles_l_english.yml
  output/rasen-preview.png (not shipped)

Everything is deterministic: the same source and seed reproduce the same files.
Usage: python tools/build_rasen_map.py [--check]
"""
from __future__ import annotations

import argparse
import colorsys
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from scipy.cluster.vq import kmeans2
from scipy.spatial import cKDTree

from rasen_names import NameForge

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/map/imperial_rasen_source.jpg'
OUT = ROOT / 'RasenMap'
PREVIEW = ROOT / 'output/rasen-preview.png'
SPEC = json.loads((Path(__file__).with_name('rasen_regions.json')).read_text(encoding='utf-8'))

WIDTH, HEIGHT = 8192, 4096
SEED = 1066
SEA_LEVEL = 18          # heightmap value at the coast; CK3's water plane sits just above it
TARGET_PROVINCE_PX = SPEC['target_province_px']
SEA_ZONE_PX = SPEC['sea_zone_px']
MIN_FRAGMENT_PX = 400
COUNTY_SIZE = 4
DUCHY_SIZE = 5

REGIONS = SPEC['regions']                       # ordered list of region specs
REGION_INDEX = {r['key']: i + 1 for i, r in enumerate(REGIONS)}
WATER = 0


# ----------------------------------------------------------------------------
# Source classification
# ----------------------------------------------------------------------------
def load_source():
    image = Image.open(SOURCE).convert('RGB')
    rgb = np.asarray(image).astype(np.int16)
    hsv = np.asarray(image.convert('HSV')).astype(np.float32)
    hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
    return rgb, hue, sat, val


def polygon_mask(shape, points, scale):
    mask = Image.new('L', (shape[1], shape[0]), 0)
    ImageDraw.Draw(mask).polygon([(x * scale, y * scale) for x, y in points], fill=1)
    return np.asarray(mask).astype(bool)


def classify(hue, sat, val):
    """Return a region label per source pixel (0 = water/outside)."""
    shape = hue.shape
    frame = SPEC['frame']
    yy, xx = np.mgrid[:shape[0], :shape[1]]
    inside = ((xx - frame['cx']) / frame['rx']) ** 2 + ((yy - frame['cy']) / frame['ry']) ** 2 < 1
    water = (hue > 185) & (hue < 225) & (sat > 0.45)
    land = ~water & inside
    land = nd.binary_opening(land, iterations=2)
    land = nd.binary_closing(land, iterations=3)          # painted rivers become land
    # Fill only small enclosed specks; the Inner Sea is an enclosed hole too.
    holes, n = nd.label(nd.binary_fill_holes(land) & ~land)
    if n:
        sizes = nd.sum(np.ones_like(holes), holes, range(1, n + 1))
        small = np.isin(holes, np.nonzero(sizes < SPEC['max_filled_hole_px'])[0] + 1)
        land |= small
    land &= inside & (yy > SPEC['frame']['top'])
    scale = SPEC['polygon_scale']
    inner = polygon_mask(shape, SPEC['inner_polygon'], scale)
    capital = polygon_mask(shape, SPEC['capital_polygon'], scale)

    labels = np.zeros(shape, np.uint8)
    # Outer provinces: angular sectors around the spiral's centre.
    rx, ry = (c * scale for c in SPEC['ring_centre'])
    ring_angle = np.degrees(np.arctan2(yy - ry, xx - rx))
    for sector in SPEC['outer_sectors']:
        lo, hi = sector['from'], sector['to']
        hit = (ring_angle >= lo) & (ring_angle < hi) if lo < hi else (ring_angle >= lo) | (ring_angle < hi)
        labels[land & ~inner & hit] = REGION_INDEX[sector['region']]
    # Inner Kingdoms: painted colours vote, geometry decides the rest.
    cx, cy = (c * scale for c in SPEC['spiral_centre'])
    angle = np.degrees(np.arctan2(yy - cy, xx - cx))
    radius = np.hypot(xx - cx, yy - cy)
    fallback = np.zeros(shape, np.uint8)
    for sector in SPEC['inner_sectors']:
        lo, hi = sector['from'], sector['to']
        hit = (angle >= lo) & (angle < hi) if lo < hi else (angle >= lo) | (angle < hi)
        if 'max_radius' in sector:
            hit &= radius < sector['max_radius'] * scale
        fallback[hit & (fallback == 0)] = REGION_INDEX[sector['region']]
    votes = np.zeros(shape, np.uint8)
    for rule in SPEC['hue_rules']:
        lo, hi = rule['hue']
        hit = (hue >= lo) & (hue <= hi) & (sat >= rule.get('min_sat', 0)) & (sat <= rule.get('max_sat', 1)) & (val >= rule.get('min_val', 0))
        votes[hit & (votes == 0)] = REGION_INDEX[rule['region']]
    # Azuma Honsha is only the landmass at the island's centre; the polygon is a bound.
    pieces, _ = nd.label(nd.binary_erosion(land & capital, iterations=3))
    ix, iy = (int(c * scale) for c in SPEC['capital_centre'])
    island = pieces == pieces[iy, ix] if pieces[iy, ix] else np.zeros(shape, bool)
    capital = nd.binary_dilation(island, iterations=3) & land & capital
    inner_land = land & inner & ~capital
    labels[inner_land] = np.where(votes[inner_land] > 0, votes[inner_land], fallback[inner_land])
    labels[land & capital] = REGION_INDEX['azuma']
    return labels, land


def smooth_regions(labels, land, iterations=3):
    """Majority filter so text, trees and outlines do not fragment regions."""
    result = labels.copy()
    keys = [REGION_INDEX[r['key']] for r in REGIONS]
    for _ in range(iterations):
        counts = np.stack([nd.uniform_filter((result == k).astype(np.float32), size=31) for k in keys])
        best = np.array(keys, np.uint8)[counts.argmax(0)]
        result = np.where(land, best, 0).astype(np.uint8)
    # Fragments of a region (shoreline glow, a stray islet) join the nearest larger body.
    stray = np.zeros(result.shape, bool)
    for k in keys:
        pieces, n = nd.label(result == k)
        if n > 1:
            sizes = nd.sum(np.ones_like(pieces), pieces, range(1, n + 1))
            stray |= np.isin(pieces, np.nonzero(sizes < SPEC['min_region_fragment_px'])[0] + 1)
    if stray.any():
        _, (iy, ix) = nd.distance_transform_edt(~land | stray, return_indices=True)
        result = np.where(stray, result[iy, ix], result).astype(np.uint8)
    return result


# ----------------------------------------------------------------------------
# Projection to the CK3 canvas
# ----------------------------------------------------------------------------
def project(labels, land, val, sat):
    box = SPEC['content_box']        # x0, y0, x1, y1 in source pixels
    sw, sh = box[2] - box[0], box[3] - box[1]
    scale = min((WIDTH - 2 * SPEC['margin']) / sw, (HEIGHT - 2 * SPEC['margin']) / sh)
    tw, th = int(sw * scale), int(sh * scale)
    ox, oy = (WIDTH - tw) // 2, (HEIGHT - th) // 2
    crop = (box[0], box[1], box[2], box[3])

    def resize(array, mode, resample):
        image = Image.fromarray(array, mode).crop(crop).resize((tw, th), resample)
        canvas = Image.new(mode, (WIDTH, HEIGHT), 0)
        canvas.paste(image, (ox, oy))
        return np.asarray(canvas)

    land_soft = resize((land * 255).astype(np.uint8), 'L', Image.BILINEAR)
    target_land = nd.gaussian_filter(land_soft.astype(np.float32), 2.0) > 127
    target_labels = resize(labels, 'L', Image.NEAREST)
    # Land created by smoothing takes the nearest painted region.
    missing = target_land & (target_labels == 0)
    if missing.any():
        _, (iy, ix) = nd.distance_transform_edt(target_labels == 0, return_indices=True)
        target_labels = np.where(missing, target_labels[iy, ix], target_labels)
    target_labels = np.where(target_land, target_labels, 0).astype(np.uint8)
    # Mountain glyphs: low-saturation grey/white strokes on land.
    rocky = ((sat < 0.22) & (val > 0.35)).astype(np.uint8) * 255
    target_rock = resize(rocky, 'L', Image.BILINEAR).astype(np.float32) / 255
    return target_labels, target_rock, (scale, ox, oy, box)


# ----------------------------------------------------------------------------
# Provinces
# ----------------------------------------------------------------------------
def seeds_for(mask, count, rng):
    ys, xs = np.nonzero(mask)
    take = min(len(xs), 60000)
    pick = rng.choice(len(xs), take, replace=False)
    points = np.column_stack([xs[pick], ys[pick]]).astype(np.float64)
    count = max(1, min(count, take))
    centroids, _ = kmeans2(points, count, iter=25, minit='++', seed=rng)
    return centroids


def assign(mask, centroids, first_id, out):
    ys, xs = np.nonzero(mask)
    _, nearest = cKDTree(centroids).query(np.column_stack([xs, ys]), workers=-1)
    out[ys, xs] = nearest + first_id


def split_fragments(provinces, region_of, next_id, land_mask):
    """Give every province a single contiguous body; merge slivers into a neighbour."""
    objects = nd.find_objects(provinces)
    for pid, sl in enumerate(objects, start=0):
        if sl is None or pid == 0:
            continue
        window = provinces[sl] == pid
        lab, n = nd.label(window)
        if n <= 1:
            continue
        sizes = nd.sum(window, lab, range(1, n + 1))
        keep = int(np.argmax(sizes)) + 1
        for part in range(1, n + 1):
            if part == keep:
                continue
            sub = lab == part
            if sizes[part - 1] >= MIN_FRAGMENT_PX * 4:
                provinces[sl][sub] = next_id
                region_of[next_id] = region_of[pid]
                next_id += 1
            else:
                provinces[sl][sub] = 0      # refilled below
    # Refill orphaned pixels from the nearest province of the same land/water kind.
    for kind in (True, False):
        mask = land_mask if kind else ~land_mask
        hole = mask & (provinces == 0)
        if hole.any():
            source = np.where(mask & (provinces > 0), 0, 1)
            _, (iy, ix) = nd.distance_transform_edt(source, return_indices=True)
            provinces[hole] = provinces[iy[hole], ix[hole]]
    return next_id


def merge_tiny(provinces, region_of, land_mask):
    sizes = np.bincount(provinces.ravel())
    tiny = [pid for pid in range(1, len(sizes)) if 0 < sizes[pid] < MIN_FRAGMENT_PX]
    for pid in tiny:
        body = provinces == pid
        ring = nd.binary_dilation(body, iterations=2) & ~body
        neighbours = provinces[ring]
        same_kind = land_mask[ring] == bool(land_mask[body].any())
        candidates = neighbours[same_kind & (neighbours != pid)]
        if candidates.size:
            provinces[body] = np.bincount(candidates).argmax()
            region_of.pop(pid, None)


def renumber(provinces, region_of, land_mask):
    """Land first (by region order, west to east), then sea zones, then impassable ocean."""
    ids = np.unique(provinces)
    ids = ids[ids > 0]
    flat = provinces.ravel()
    counts = np.bincount(flat)
    ys, xs = np.divmod(np.arange(flat.size), provinces.shape[1])
    sx = np.bincount(flat, weights=xs)
    sy = np.bincount(flat, weights=ys)
    centres = {int(pid): (sx[pid] / counts[pid], sy[pid] / counts[pid]) for pid in ids}
    def key(pid):
        region = region_of.get(pid, 'sea')
        order = {r['key']: i for i, r in enumerate(REGIONS)}
        group = order.get(region, 100 if region == 'sea' else 200)
        x, y = centres[pid]
        return (group, round(y / 256), x)
    ordered = sorted((int(p) for p in ids), key=key)
    lookup = np.zeros(int(provinces.max()) + 1, np.int32)
    for new, old in enumerate(ordered, start=1):
        lookup[old] = new
    remapped = lookup[provinces]
    new_region = {lookup[p]: region_of.get(p, 'sea') for p in ordered}
    new_centre = {lookup[p]: centres[p] for p in ordered}
    return remapped, new_region, new_centre


def build_provinces(labels, rng):
    land_mask = labels > 0
    provinces = np.zeros(labels.shape, np.int32)
    region_of = {}
    next_id = 1
    for region in REGIONS:
        mask = labels == REGION_INDEX[region['key']]
        area = int(mask.sum())
        if not area:
            continue
        count = max(3, round(area * region['density'] / TARGET_PROVINCE_PX))
        centroids = seeds_for(mask, count, rng)
        assign(mask, centroids, next_id, provinces)
        for i in range(len(centroids)):
            region_of[next_id + i] = region['key']
        next_id += len(centroids)
    # Sea: near-shore zones and a ring of impassable open ocean.
    water = ~land_mask
    distance = nd.distance_transform_edt(water)
    near = water & (distance < SPEC['sea_reach_px'])
    far = water & ~near
    sea_count = max(8, round(int(near.sum()) / SEA_ZONE_PX))
    centroids = seeds_for(near, sea_count, rng)
    assign(near, centroids, next_id, provinces)
    for i in range(len(centroids)):
        region_of[next_id + i] = 'sea'
    next_id += len(centroids)
    centroids = seeds_for(far, SPEC['ocean_zones'], rng)
    assign(far, centroids, next_id, provinces)
    for i in range(len(centroids)):
        region_of[next_id + i] = 'ocean'
    next_id += len(centroids)
    next_id = split_fragments(provinces, region_of, next_id, land_mask)
    merge_tiny(provinces, region_of, land_mask)
    return renumber(provinces, region_of, land_mask)


# ----------------------------------------------------------------------------
# Title hierarchy
# ----------------------------------------------------------------------------
def adjacency(provinces):
    pairs = set()
    for a, b in ((provinces[:, :-1], provinces[:, 1:]), (provinces[:-1, :], provinces[1:, :])):
        diff = a != b
        for x, y in zip(a[diff].ravel(), b[diff].ravel()):
            pairs.add((min(int(x), int(y)), max(int(x), int(y))))
    graph = {}
    for x, y in pairs:
        graph.setdefault(x, set()).add(y)
        graph.setdefault(y, set()).add(x)
    return graph


def grow_groups(members, graph, centre, size, rng):
    """Partition members into contiguous groups of roughly `size`."""
    remaining = set(members)
    groups = []
    while remaining:
        start = min(remaining, key=lambda p: (centre[p][0] + centre[p][1] * 0.25))
        group = [start]
        remaining.discard(start)
        frontier = set(graph.get(start, ())) & remaining
        while frontier and len(group) < size:
            gx = sum(centre[p][0] for p in group) / len(group)
            gy = sum(centre[p][1] for p in group) / len(group)
            nxt = min(frontier, key=lambda p: (centre[p][0] - gx) ** 2 + (centre[p][1] - gy) ** 2)
            group.append(nxt)
            remaining.discard(nxt)
            frontier |= set(graph.get(nxt, ()))
            frontier &= remaining
        groups.append(group)
    # Fold undersized groups into a touching neighbour group.
    owner = {p: i for i, g in enumerate(groups) for p in g}
    for i, group in enumerate(groups):
        if 0 < len(group) < max(2, size // 2):
            touching = [owner[n] for p in group for n in graph.get(p, ()) if n in owner and owner[n] != i and groups[owner[n]]]
            if touching:
                target = max(set(touching), key=touching.count)
                for p in group:
                    owner[p] = target
                groups[target].extend(group)
                groups[i] = []
    return [g for g in groups if g]


def build_titles(region_of, centre, graph, rng):
    forge = NameForge(SPEC, seed=SEED)
    kingdoms = []
    for region in REGIONS:
        baronies = sorted((p for p, r in region_of.items() if r == region['key']), key=lambda p: (centre[p][1], centre[p][0]))
        if not baronies:
            continue
        counties = grow_groups(baronies, graph, centre, COUNTY_SIZE, rng)
        county_graph = {}
        county_of = {p: i for i, c in enumerate(counties) for p in c}
        for i, county in enumerate(counties):
            county_graph[i] = {county_of[n] for p in county for n in graph.get(p, ()) if n in county_of and county_of[n] != i}
        county_centre = {i: (sum(centre[p][0] for p in c) / len(c), sum(centre[p][1] for p in c) / len(c)) for i, c in enumerate(counties)}
        duchies = grow_groups(list(range(len(counties))), county_graph, county_centre, DUCHY_SIZE, rng)
        kingdom = {'key': region['key'], 'duchies': []}
        for duchy in duchies:
            d = {'name': forge.duchy(region['key']), 'counties': []}
            for ci in duchy:
                county = sorted(counties[ci], key=lambda p: (centre[p][1], centre[p][0]))
                c = {'name': forge.county(region['key']), 'baronies': []}
                for p in county:
                    c['baronies'].append({'name': forge.barony(region['key']), 'province': p})
                d['counties'].append(c)
            kingdom['duchies'].append(d)
        forge.apply_canon(kingdom)
        kingdoms.append(kingdom)
    return kingdoms


# ----------------------------------------------------------------------------
# Writers
# ----------------------------------------------------------------------------
def province_colours(count):
    colours = {}
    used = {(0, 0, 0)}
    for pid in range(1, count + 1):
        digest = hashlib.sha256(f'rasen-{pid}'.encode()).digest()
        i = 0
        while True:
            colour = (digest[i % 32], digest[(i + 1) % 32], digest[(i + 2) % 32])
            if colour not in used:
                break
            i += 3
            if i > 90:
                digest = hashlib.sha256(digest).digest()
                i = 0
        used.add(colour)
        colours[pid] = colour
    return colours


def title_colour(region, jitter, rng):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in region['colour']))
    h = (h + rng.uniform(-jitter, jitter) / 360) % 1
    s = min(1, max(0.2, s + rng.uniform(-0.15, 0.15)))
    v = min(1, max(0.25, v + rng.uniform(-0.15, 0.15)))
    return tuple(int(c * 255) for c in colorsys.hsv_to_rgb(h, s, v))


def landed_titles(kingdoms, rng):
    region_spec = {r['key']: r for r in REGIONS}
    lines = ['# Generated by tools/build_rasen_map.py. Edit tools/rasen_regions.json or tools/rasen_names.py instead.',
             'e_rasen = {', '\tcolor = { 196 160 72 }', '\tcapital = %s' % kingdoms[[k['key'] for k in kingdoms].index('azuma')]['duchies'][0]['counties'][0]['key'], '']
    loc = ['l_english:', ' e_rasen:0 "Imperial Rasen"', ' e_rasen_adj:0 "Rasenese"']
    for kingdom in kingdoms:
        spec = region_spec[kingdom['key']]
        k_key = 'k_' + kingdom['key']
        lines += [f'\t{k_key} = {{', '\t\tcolor = { %d %d %d }' % tuple(spec['colour']),
                  f"\t\tcapital = {kingdom['duchies'][0]['counties'][0]['key']}", '']
        loc += [f' {k_key}:0 "{spec["name"]}"', f' {k_key}_adj:0 "{spec["adjective"]}"']
        for duchy in kingdom['duchies']:
            lines += [f"\t\t{duchy['key']} = {{", '\t\t\tcolor = { %d %d %d }' % title_colour(spec, 12, rng),
                      f"\t\t\tcapital = {duchy['counties'][0]['key']}", '']
            loc += [f" {duchy['key']}:0 \"{duchy['name']}\"", f" {duchy['key']}_adj:0 \"{duchy['name']}\""]
            for county in duchy['counties']:
                lines += [f"\t\t\t{county['key']} = {{", '\t\t\t\tcolor = { %d %d %d }' % title_colour(spec, 20, rng), '']
                loc += [f" {county['key']}:0 \"{county['name']}\"", f" {county['key']}_adj:0 \"{county['name']}\""]
                for barony in county['baronies']:
                    lines += [f"\t\t\t\t{barony['key']} = {{", f"\t\t\t\t\tprovince = {barony['province']}",
                              '\t\t\t\t\tcolor = { %d %d %d }' % title_colour(spec, 20, rng), '\t\t\t\t}']
                    loc.append(f" {barony['key']}:0 \"{barony['name']}\"")
                lines.append('\t\t\t}')
            lines.append('\t\t}')
        lines.append('\t}')
    lines.append('}')
    return '\n'.join(lines) + '\n', '\n'.join(loc) + '\n'


def default_map(region_of):
    land = sorted(p for p, r in region_of.items() if r not in ('sea', 'ocean'))
    sea = sorted(p for p, r in region_of.items() if r == 'sea')
    ocean = sorted(p for p, r in region_of.items() if r == 'ocean')
    def ranges(ids):
        out, start, prev = [], None, None
        for i in ids:
            if start is None:
                start = prev = i
            elif i == prev + 1:
                prev = i
            else:
                out.append((start, prev)); start = prev = i
        if start is not None:
            out.append((start, prev))
        return out
    lines = ['# Generated by tools/build_rasen_map.py',
             'definitions = "definition.csv"', 'provinces = "provinces.png"', 'rivers = "rivers.png"',
             'topology = "heightmap.heightmap"', 'continent = "continent.txt"', 'adjacencies = "adjacencies.csv"',
             'island_region = "island_region.txt"', 'seasons = "seasons.txt"', '']
    for a, b in ranges(sea):
        lines.append(f'sea_zones = RANGE {{ {a} {b} }}')
    for a, b in ranges(ocean):
        lines.append(f'impassable_seas = RANGE {{ {a} {b} }}')
    return '\n'.join(lines) + '\n', land, sea, ocean


def definition_csv(colours, names, count):
    rows = ['0;0;0;0;x;x;']
    for pid in range(1, count + 1):
        r, g, b = colours[pid]
        rows.append(f'{pid};{r};{g};{b};{names.get(pid, f"sea_{pid}")};x;')
    return '\n'.join(rows) + '\n'


def heightmap(labels, rock, rng):
    land = labels > 0
    coast = nd.distance_transform_edt(land).astype(np.float32)
    depth = nd.distance_transform_edt(~land).astype(np.float32)
    noise = nd.gaussian_filter(rng.standard_normal((HEIGHT // 8, WIDTH // 8)).astype(np.float32), 3)
    noise = np.asarray(Image.fromarray(noise).resize((WIDTH, HEIGHT), Image.BICUBIC))
    mountains = nd.gaussian_filter(rock, 10) * 2.2
    raised = np.zeros_like(coast)
    for region in REGIONS:
        raised[labels == REGION_INDEX[region['key']]] = region.get('elevation', 0)
    raised = nd.gaussian_filter(raised, 25)
    land_h = SEA_LEVEL + 3 + np.minimum(coast, 120) * 0.12 + raised + mountains * 90 + noise * 6
    sea_h = SEA_LEVEL - 2 - np.minimum(depth, 300) * 0.05
    height = np.where(land, land_h, sea_h)
    height = nd.gaussian_filter(height, 1.2)
    return np.clip(height, 0, 255).astype(np.uint8)


def render(write=True):
    rng = np.random.default_rng(SEED)
    rgb, hue, sat, val = load_source()
    labels, land = classify(hue, sat, val)
    labels = smooth_regions(labels, land)
    target, rock, transform = project(labels, land, val, sat)
    provinces, region_of, centre = build_provinces(target, rng)
    count = int(provinces.max())
    graph = adjacency(provinces)
    kingdoms = build_titles(region_of, centre, graph, rng)
    names = {b['province']: b['key'] for k in kingdoms for d in k['duchies'] for c in d['counties'] for b in c['baronies']}
    colours = province_colours(count)
    palette = np.zeros((count + 1, 3), np.uint8)
    for pid, colour in colours.items():
        palette[pid] = colour
    files = {}
    def png(array, mode):
        buf = io.BytesIO()
        Image.fromarray(array, mode).save(buf, 'PNG', optimize=False, compress_level=6)
        return buf.getvalue()
    files['map_data/provinces.png'] = png(palette[provinces], 'RGB')
    files['map_data/heightmap.png'] = png(heightmap(target, rock, rng), 'L')
    default, land_ids, sea_ids, ocean_ids = default_map(region_of)
    files['map_data/default.map'] = default.encode('utf-8')
    files['map_data/definition.csv'] = definition_csv(colours, names, count).encode('utf-8')
    files['map_data/adjacencies.csv'] = b'From;To;Type;Through;start_x;start_y;stop_x;stop_y;Comment\n'
    files['map_data/island_region.txt'] = b'# No island regions yet.\n'
    titles, loc = landed_titles(kingdoms, rng)
    files['common/landed_titles/00_rasen_titles.txt'] = ('﻿' + titles).encode('utf-8')
    files['localization/english/rasen_titles_l_english.yml'] = ('﻿' + loc).encode('utf-8')
    regions = ['# Generated by tools/build_rasen_map.py']
    for region in REGIONS:
        keys = [d['key'] for k in kingdoms if k['key'] == region['key'] for d in k['duchies']]
        regions += [f"world_rasen_{region['key']} = {{", '\tduchies = { ' + ' '.join(keys) + ' }', '}']
    regions += ['world_rasen_inner = { regions = { ' + ' '.join(f"world_rasen_{r['key']}" for r in REGIONS if r['ring'] == 'inner') + ' } }',
                'world_rasen_outer = { regions = { ' + ' '.join(f"world_rasen_{r['key']}" for r in REGIONS if r['ring'] == 'outer') + ' } }']
    files['map_data/geographical_region.txt'] = ('\n'.join(regions) + '\n').encode('utf-8')
    summary = {
        'land_provinces': len(land_ids), 'sea_zones': len(sea_ids), 'impassable_seas': len(ocean_ids),
        'kingdoms': {k['key']: {'duchies': len(k['duchies']),
                                'counties': sum(len(d['counties']) for d in k['duchies']),
                                'baronies': sum(len(c['baronies']) for d in k['duchies'] for c in d['counties'])} for k in kingdoms},
    }
    files['map_data/rasen_summary.json'] = (json.dumps(summary, indent=1) + '\n').encode('utf-8')
    if write:
        for relative, data in files.items():
            path = OUT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        preview(provinces, region_of, target, kingdoms, centre)
    return files, summary


def preview(provinces, region_of, labels, kingdoms, centre):
    region_spec = {r['key']: r for r in REGIONS}
    shade = np.zeros((int(provinces.max()) + 1, 3), np.uint8)
    rng = np.random.default_rng(3)
    for pid, region in region_of.items():
        if region in region_spec:
            base = np.array(region_spec[region]['colour'], np.float32)
            shade[pid] = np.clip(base * rng.uniform(0.75, 1.15), 0, 255)
        else:
            shade[pid] = (30, 60, 120) if region == 'sea' else (15, 30, 70)
    image = shade[provinces]
    edges = (provinces[:, 1:] != provinces[:, :-1])
    image[:, 1:][edges] = image[:, 1:][edges] // 2
    edges = (provinces[1:, :] != provinces[:-1, :])
    image[1:, :][edges] = image[1:, :][edges] // 2
    small = Image.fromarray(image).resize((WIDTH // 2, HEIGHT // 2), Image.NEAREST)
    draw = ImageDraw.Draw(small)
    for kingdom in kingdoms:
        for duchy in kingdom['duchies']:
            ps = [b['province'] for c in duchy['counties'] for b in c['baronies']]
            x = sum(centre[p][0] for p in ps) / len(ps) / 2
            y = sum(centre[p][1] for p in ps) / len(ps) / 2
            draw.text((x - 20, y - 5), duchy['name'], fill=(255, 255, 255))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    small.save(PREVIEW)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if the generated files differ from RasenMap/.')
    args = parser.parse_args()
    files, summary = render(write=not args.check)
    if args.check:
        stale = [r for r, d in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale generated files: ' + ', '.join(stale))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
