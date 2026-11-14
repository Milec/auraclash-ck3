"""Generate the Imperial Rasen map data from the painted Aura Clash world map.

The source painting (assets/map/imperial_rasen_source.jpg) is classified into
water and land, land is split into the five Inner Kingdoms, Azuma Honsha and
the four Outer provinces, and each region is divided into compact provinces.
The result is written to AuraClash/ (a separate overhaul mod) as:

  map_data/provinces.png, definition.csv, default.map, heightmap.png,
  adjacencies.csv, island_region.txt, seasons.txt, climate.txt,
  geographical_regions/rasen_geographical_regions.txt
  common/landed_titles/00_rasen_titles.txt
  localization/replace/english/rasen_titles_l_english.yml
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
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from scipy.cluster.vq import kmeans2
from scipy.spatial import cKDTree

from rasen_names import NameForge

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'assets/map/imperial_rasen_source.jpg'
OUT = ROOT / 'AuraClash'
PREVIEW = ROOT / 'output/rasen-preview.png'
SPEC = json.loads((Path(__file__).with_name('rasen_regions.json')).read_text(encoding='utf-8'))

WIDTH, HEIGHT = 8192, 4096            # the painted world
MAP_WIDTH, MAP_HEIGHT = 9216, 4608    # vanilla CK3 1.20 map size
PAD_X, PAD_Y = (MAP_WIDTH - WIDTH) // 2, (MAP_HEIGHT - HEIGHT) // 2
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
    # The painted region names are white lettering too: relief under them follows the ground around.
    rocky = (fill_labels(((sat < 0.22) & (val > 0.35)).astype(np.float32)) * 255).astype(np.uint8)
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


# Kingdoms no one may crown themselves king of: the Wild Lands and the Outer Provinces.
UNCROWNABLE = ('wild', 'outer_west', 'outer_north', 'outer_east', 'outer_south')
# The Celestial ministries, with vanilla's names (the hegemony keeps All Under Heaven's bureaucracy).
MINISTRIES = [('e_minister_chancellor', '228 237 113', 'Chancellery'), ('e_minister_censor', '185 192 35', 'Censorate'),
              ('e_minister_grand_marshal', '212 150 69', 'Commission'), ('e_minister_of_personnel', '228 237 59', 'Ministry of Personnel'),
              ('e_minister_of_revenue', '206 247 0', 'Ministry of Revenue'), ('e_minister_of_rites', '248 247 0', 'Ministry of Rites'),
              ('e_minister_of_war', '255 168 10', 'Ministry of War'), ('e_minister_of_justice', '255 237 13', 'Ministry of Justice'),
              ('e_minister_of_works', '239 255 13', 'Ministry of Works')]


def landed_titles(kingdoms, rng):
    region_spec = {r['key']: r for r in REGIONS}
    lines = ['# Generated by tools/build_rasen_map.py. Edit tools/rasen_regions.json or tools/rasen_names.py instead.',
             'e_rasen = {', '\tcolor = { 196 160 72 }', '\tcapital = %s' % kingdoms[[k['key'] for k in kingdoms].index('azuma')]['duchies'][0]['counties'][0]['key'], '']
    loc = ['l_english:', ' h_china:0 "Imperial Rasen"', ' h_china_adj:0 "Imperial"',
           # The dynastic cycle names its land after this key (vanilla: "China").
           ' dynastic_cycle_sub_region_core:0 "Imperial Rasen"',
           ' rasen_uncrownable_tt:0 "No one is crowned here: the Wild Lands answer to their Maos and the Outer Provinces to the Council"',
           ' e_rasen:0 "The Spiral Continent"', ' e_rasen_adj:0 "Rasenese"']
    for kingdom in kingdoms:
        spec = region_spec[kingdom['key']]
        k_key = 'k_' + kingdom['key']
        lines += [f'\t{k_key} = {{', '\t\tcolor = { %d %d %d }' % tuple(spec['colour']),
                  f"\t\tcapital = {kingdom['duchies'][0]['counties'][0]['key']}", '']
        if kingdom['key'] in UNCROWNABLE:
            # The Wild Lands stay thirteen Maos, and the Outer Provinces are the Council's territories.
            lines[-1:-1] = ['\t\tcan_create = { custom_tooltip = { text = rasen_uncrownable_tt always = no } }',
                            '\t\tcan_create_on_partition = { always = no }']
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
    # The whole continent is one hegemony, ruled by the Exalted Council from Azuma Honsha.
    capital = next(l for l in lines if l.startswith('\tcapital = '))
    # Its key is h_china so the game's own Celestial bureaucracy (ministries, laws, the dynastic cycle)
    # applies to it. The nine landless ministries sit inside it as they do in vanilla.
    ministers = []
    for key, colour, name in MINISTRIES:
        loc += [f' {key}:0 "{name}"', f' {key}_article:0 "the "']
        ministers += [f'\t{key} = {{', f'\t\tcolor = {{ {colour} }}', '\t\tlandless = yes', '\t\tallow_domicile = no',
                      '\t\tdestroy_if_invalid_heir = yes', '\t\tdlc_feature = all_under_heaven', '\t\tno_automatic_claims = yes',
                      '\t\tde_jure_drift_disabled = yes', '\t\tcan_use_nomadic_naming = no', '\t\tcan_be_named_after_dynasty = no',
                      '\t\tdefinite_form = yes', '\t\truler_uses_title_name = no', '\t' + capital, '\t}']
    lines = [lines[0], 'h_china = {', '\tcolor = { 214 176 76 }', capital, '\tdisable_regnal_numbers = always', '',
             *('\t' + l if l else l for l in lines[1:]), *ministers, '}']
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
             'topology = "heightmap.heightmap"', 'adjacencies = "adjacencies.csv"',
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
    h, w = labels.shape
    noise = nd.gaussian_filter(rng.standard_normal((h // 8, w // 8)).astype(np.float32), 3)
    noise = np.asarray(Image.fromarray(noise).resize((w, h), Image.BICUBIC))
    mountains = nd.gaussian_filter(rock, 10) * 2.2
    raised = np.zeros_like(coast)
    for region in REGIONS:
        raised[labels == REGION_INDEX[region['key']]] = region.get('elevation', 0)
    raised = nd.gaussian_filter(raised, 25)
    land_h = SEA_LEVEL + 3 + np.minimum(coast, 120) * 0.12 + raised + mountains * 90 + noise * 6
    # The water plane sits at about 15 (WATERLEVEL in the game's defines): drop the sea floor well
    # below it right at the coast, or a wide shelf of bare sand shows above the water.
    sea_h = SEA_LEVEL - 7 - np.minimum(depth, 45) * 0.2
    height = np.where(land, land_h, sea_h)
    height = nd.gaussian_filter(height, 1.2)
    return np.clip(height, 0, 255).astype(np.uint8)


# ----------------------------------------------------------------------------
# Biomes: what the painting draws, region by region
# ----------------------------------------------------------------------------
# The painting's region labels (source pixels, x0 y0 x1 y1): their lettering is not terrain.
LABEL_BOXES = [
    (950, 155, 1195, 205), (965, 480, 1225, 525), (1470, 585, 1695, 680), (1345, 780, 1500, 870),
    (1865, 785, 2085, 830), (435, 870, 655, 910), (950, 985, 1065, 1070), (1180, 975, 1355, 1055),
    (1415, 1080, 1685, 1130), (1415, 1330, 1670, 1375), (865, 1440, 1115, 1490),
]
# Per region, from the painting and the lore: (open ground, forest, high ground) as CK3 terrain types.
BIOME_TERRAIN = {
    'outer_north': ('plains', 'taiga', 'mountains'), 'sacred': ('plains', 'taiga', 'mountains'),
    'outer_west': ('plains', 'forest', 'mountains'), 'outer_east': ('plains', 'forest', 'hills'),
    'outer_south': ('plains', 'jungle', 'mountains'), 'mystic': ('farmlands', 'forest', 'hills'),
    'bladed': ('drylands', 'forest', 'hills'), 'cursed': ('wetlands', 'forest', 'hills'),
    'wild': ('plains', 'jungle', 'hills'), 'azuma': ('farmlands', 'forest', 'hills'),
}
SNOWY = ('outer_north', 'sacred')
# Outer South: "jungle inland, dunes on the coast" (rulebook). Coastal pixels within this reach are dunes.
DUNE_REACH = 70
FOREST_CUT, ROCK_CUT, SNOW_CUT = 0.22, 0.20, 0.30


def label_mask(shape):
    """True over the painting's region-name lettering (source pixels)."""
    text = np.zeros(shape, bool)
    for x0, y0, x1, y1 in LABEL_BOXES:
        text[y0:y1, x0:x1] = True
    return text


def fill_labels(layer, sigma=20):
    """A 0-1 layer with the lettering replaced by the surrounding ground's average (normalized blur)."""
    text = label_mask(layer.shape)
    keep = (~text).astype(np.float32)
    around = nd.gaussian_filter(layer * keep, sigma) / np.maximum(nd.gaussian_filter(keep, sigma), 1e-3)
    return np.where(text, around, layer).astype(np.float32)


def feature_layers(hue, sat, val, labels, land):
    """Densities (0-1, source pixels) of the painting's drawn trees, peaks and snow."""
    ground = land & ~label_mask(land.shape)
    # Tree clusters: darker than the ground around them and not grey (the regions are tinted, so not only green).
    tree = ground & (val < nd.uniform_filter(val, 31) - 0.10) & (sat > 0.25)
    # Peaks: low-saturation grey or white strokes.
    rock = ground & (sat < 0.22) & (val > 0.30) & (val <= 0.80)
    # Snow and ice: white, or pale blue, and only where the painting is a frozen land.
    frozen = np.isin(labels, [REGION_INDEX[k] for k in SNOWY])
    snow = ground & frozen & (((val > 0.80) & (sat < 0.20)) | ((hue >= 185) & (hue <= 230) & (sat < 0.40) & (val > 0.72)))
    return [fill_labels(nd.gaussian_filter(a.astype(np.float32), 4)) * land for a in (tree, rock, snow)]


def project_layer(layer, transform):
    """A float source layer on the padded CK3 canvas, where project() put the continent."""
    scale, ox, oy, box = transform
    tw, th = int((box[2] - box[0]) * scale), int((box[3] - box[1]) * scale)
    image = Image.fromarray(layer.astype(np.float32), 'F').crop(tuple(box)).resize((tw, th), Image.BILINEAR)
    canvas = np.zeros((HEIGHT, WIDTH), np.float32)
    canvas[oy:oy + th, ox:ox + tw] = np.asarray(image)
    return np.pad(canvas, ((PAD_Y, MAP_HEIGHT - HEIGHT - PAD_Y), (PAD_X, MAP_WIDTH - WIDTH - PAD_X)))


def biome_layers():
    """Region labels and the drawn tree, peak and snow densities, all on the padded CK3 canvas."""
    rgb, hue, sat, val = load_source()
    labels, land = classify(hue, sat, val)
    labels = smooth_regions(labels, land)
    target, _rock, transform = project(labels, land, val, sat)
    target = np.pad(target, ((PAD_Y, MAP_HEIGHT - HEIGHT - PAD_Y), (PAD_X, MAP_WIDTH - WIDTH - PAD_X)))
    tree, rock, snow = (project_layer(a, transform) for a in feature_layers(hue, sat, val, labels, land))
    return target, tree, rock, snow


def province_terrain(provinces, region_of, height, layers):
    """Terrain per land province, from what the painting draws there: peaks, forest or the region's open ground."""
    tree, rock, snow = layers
    count = int(provinces.max())
    flat = provinces.ravel()
    sizes = np.bincount(flat, minlength=count + 1).astype(np.float64)
    sizes[sizes == 0] = 1
    share = lambda mask: np.bincount(flat, weights=mask.ravel().astype(np.float64), minlength=count + 1) / sizes
    mean_h = np.bincount(flat, weights=height.ravel().astype(np.float64), minlength=count + 1) / sizes
    rocky, wooded = share(rock > ROCK_CUT), share(tree > FOREST_CUT)
    land_px = provinces > 0
    land_px &= np.isin(provinces, [p for p, r in region_of.items() if r not in ('sea', 'ocean')])
    coastal = share(nd.distance_transform_edt(land_px) < DUNE_REACH)
    land = [p for p, r in region_of.items() if r not in ('sea', 'ocean')]
    heights = np.array([mean_h[p] for p in land])
    mountain_cut = np.percentile(heights, 90)
    lines = ['# Generated by tools/build_rasen_map.py.', 'default_land=plains', 'default_sea=sea', 'default_coastal_sea=coastal_sea']
    props = ['# Generated by tools/build_rasen_map.py. Winter severity follows the frozen north.']
    spec = {r['key']: r for r in REGIONS}
    for p in sorted(land):
        key = region_of[p]
        region = spec[key]
        open_kind, forest_kind, high_kind = BIOME_TERRAIN[key]
        if rocky[p] >= 0.40 or (mean_h[p] >= mountain_cut and rocky[p] >= 0.15):
            kind = high_kind
        elif rocky[p] >= 0.20:
            kind = 'hills'
        elif wooded[p] >= 0.40:
            kind = forest_kind
        elif key == 'outer_south' and coastal[p] >= 0.6:
            kind = 'desert'
        else:
            kind = open_kind
        lines.append(f'{p}={kind}')
        if region.get('winter'):
            props.append(f'{p}={{ winter_severity_bias = {region["winter"]} }}')
    return '\n'.join(lines) + '\n', '\n'.join(props) + '\n'


# Same calendar as vanilla: the seasons drive winter and the tree colours.
SEASONS = """# Generated by tools/build_rasen_map.py
winter = { start_date=00.12.01 end_date=00.02.31 }
spring = { start_date=00.04.01 end_date=00.05.1 }
summer = { start_date=00.06.01 end_date=00.09.10 }
autumn = { start_date=00.10.10 end_date=00.10.31 }
tree_winter = { start_date=00.11.15 end_date=00.12.01 }
tree_winter2 = { start_date=00.12.20 end_date=00.01.20 }
tree_spring = { start_date=00.02.20 end_date=00.03.01 }
tree_spring2 = { start_date=00.03.20 end_date=00.04.20 }
tree_summer = { start_date=00.05.20 end_date=00.06.01 }
tree_summer2 = { start_date=00.06.20 end_date=00.09.10 }
tree_autumn = { start_date=00.10.01 end_date=00.10.10 }
tree_autumn2 = { start_date=00.10.25 end_date=00.11.01 }
"""


def climate(region_of):
    """Winter classes by region: severe where the region's winter bias is 0.6+, normal from 0.3, else mild."""
    spec = {r['key']: r for r in REGIONS}
    groups = {'mild_winter': [], 'normal_winter': [], 'severe_winter': []}
    for p in sorted(p for p, r in region_of.items() if r not in ('sea', 'ocean')):
        bias = spec[region_of[p]].get('winter', 0)
        groups['severe_winter' if bias >= 0.6 else 'normal_winter' if bias >= 0.3 else 'mild_winter'].append(p)
    lines = ['# Generated by tools/build_rasen_map.py']
    for key, ids in groups.items():
        lines += [f'{key} = {{'] + ['\t' + ' '.join(map(str, ids[i:i + 20])) for i in range(0, len(ids), 20)] + ['}']
    return '\n'.join(lines) + '\n'


def rivers_png(labels):
    """CK3 rivers.png: 8-bit indexed, 255 = land (white), 254 = water (pink); no rivers drawn yet."""
    index = np.where(labels > 0, 255, 254).astype(np.uint8)
    image = Image.fromarray(index, 'P')
    palette = [0] * 768
    palette[0:3] = (0, 255, 0)        # river source
    palette[3:6] = (255, 0, 0)        # river merge
    palette[6:9] = (255, 252, 0)      # river split
    for i, blue in enumerate(range(255, 30, -25), start=3):
        palette[i * 3:i * 3 + 3] = (0, max(0, blue - 100), blue)
    palette[254 * 3:254 * 3 + 3] = (255, 0, 128)
    palette[255 * 3:255 * 3 + 3] = (255, 255, 255)
    image.putpalette(palette)
    buf = io.BytesIO()
    image.save(buf, 'PNG')
    return buf.getvalue()


# Map object locators: where CK3 draws holdings, armies, sieges and activities for each province.
# Vanilla's files place Earth's province ids, many outside this smaller map, which crashes the load.
# name, clamp_to_water_level, layer, land only?, (dx, dz) offset from the province's interior point
LOCATORS = {
    'building_locators': ('buildings', 'yes', 'building_layer', True, (0, 0)),
    'special_building_locators': ('special_building', 'yes', 'building_layer', True, (0, 0)),
    'siege_locators': ('siege', 'no', 'unit_layer', True, (6, -4)),
    'activities': ('activities', 'no', 'activities_layer', True, (-6, 4)),
    'combat_locators': ('combat', 'yes', 'unit_layer', False, (0, 6)),
    'stack_locators': ('unit_stack', 'yes', 'unit_layer', False, (-5, -5)),
    'player_stack_locators': ('unit_stack_player_owned', 'yes', 'unit_layer', False, (-5, -5)),
    'other_stack_locators': ('unit_stack_other_owner', 'yes', 'unit_layer', False, (5, -5)),
}


def interior_points(provinces, ids):
    """For each province, the pixel farthest from its border (so objects sit well inside it)."""
    edge = np.zeros(provinces.shape, bool)
    edge[:, :-1] |= provinces[:, :-1] != provinces[:, 1:]
    edge[:-1, :] |= provinces[:-1, :] != provinces[1:, :]
    edge[:, 1:] |= provinces[:, :-1] != provinces[:, 1:]
    edge[1:, :] |= provinces[:-1, :] != provinces[1:, :]
    depth = nd.distance_transform_edt(~edge)
    positions = nd.maximum_position(depth, labels=provinces, index=ids)
    return {pid: (int(row), int(col), float(depth[row, col])) for pid, (row, col) in zip(ids, positions)}


def map_object_locators(provinces, land_ids, water_ids):
    h, w = provinces.shape
    points = interior_points(provinces, sorted(land_ids) + sorted(water_ids))
    files = {}
    for filename, (name, clamp, layer, land_only, (dx, dz)) in LOCATORS.items():
        ids = sorted(land_ids) if land_only else sorted(points)
        lines = ['game_object_locator={', f'\tname="{name}"', '\trender_pass=Map', f'\tclamp_to_water_level={clamp}',
                 '\tgenerated_content=no', f'\tlayer="{layer}"', '\tinstances={']
        if not land_only:
            # Vanilla's army and combat locators also carry id 0 (no province); CK3 asks for it.
            lines += ['		{', '			id=0', '			position={ 0.000000 0.000000 0.000000 }',
                      '			rotation={ -0.000000 0.000000 -0.000000 1.000000 }',
                      '			scale={ 1.000000 1.000000 1.000000 }', '		}']
        for pid in ids:
            row, col, depth = points[pid]
            reach = min(1.0, depth / 8)  # keep offsets inside small provinces
            x = min(max(col + 0.5 + dx * reach, 0.0), w - 1.0)
            z = min(max((h - 1 - row) + 0.5 + dz * reach, 0.0), h - 1.0)  # CK3's z runs bottom-up
            lines += ['\t\t{', f'\t\t\tid={pid}', f'\t\t\tposition={{ {x:.6f} 0.000000 {z:.6f} }}',
                      '\t\t\trotation={ -0.000000 0.000000 -0.000000 1.000000 }',
                      '\t\t\tscale={ 1.000000 1.000000 1.000000 }', '\t\t}']
        lines += ['\t}', '}']
        files[f'gfx/map/map_object_data/{filename}.txt'] = ('﻿' + '\n'.join(lines) + '\n').encode('utf-8')
    return files


def render(write=True):
    rng = np.random.default_rng(SEED)
    rgb, hue, sat, val = load_source()
    labels, land = classify(hue, sat, val)
    labels = smooth_regions(labels, land)
    target, rock, transform = project(labels, land, val, sat)
    # CK3's terrain textures, masks and colormap are all vanilla-sized: centre the painted world
    # in open ocean at 9216 x 4608 (a smaller map crashes the load as soon as holdings exist).
    pad = ((PAD_Y, MAP_HEIGHT - HEIGHT - PAD_Y), (PAD_X, MAP_WIDTH - WIDTH - PAD_X))
    target, rock = np.pad(target, pad), np.pad(rock, pad)
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
    height = heightmap(target, rock, rng)
    files['map_data/heightmap.png'] = png(height, 'L')
    tree, rock_drawn, snow = (project_layer(a, transform) for a in feature_layers(hue, sat, val, labels, land))
    terrain, properties = province_terrain(provinces, region_of, height, (tree, rock_drawn, snow))
    files['common/province_terrain/00_rasen_province_terrain.txt'] = ('\ufeff' + terrain).encode('utf-8')
    files['common/province_terrain/01_rasen_province_properties.txt'] = ('\ufeff' + properties).encode('utf-8')
    files['map_data/rivers.png'] = rivers_png(target)
    default, land_ids, sea_ids, ocean_ids = default_map(region_of)
    files['map_data/default.map'] = default.encode('utf-8')
    files['map_data/definition.csv'] = definition_csv(colours, names, count).encode('utf-8')
    # The -1 line ends the table. Without it CK3 1.20.1 spins forever reading past the end of the file.
    files['map_data/adjacencies.csv'] = (b'From;To;Type;Through;start_x;start_y;stop_x;stop_y;Comment\n'
                                         b'-1;-1;;-1;-1;-1;-1;-1;\n')
    files['map_data/island_region.txt'] = b'# No island regions yet.\n'
    titles, loc = landed_titles(kingdoms, rng)
    files['common/landed_titles/00_rasen_titles.txt'] = ('﻿' + titles).encode('utf-8')
    # Vanilla scripts name Earth's realms (title:e_byzantium, h_china ...). As the Atlantis
    # total-conversion template does, keep each vanilla hegemony, empire, kingdom and duchy
    # defined as a landless title, so those scripts find a title instead of crashing.
    ours = set(re.findall(r'\b([hekd]_\w+) = \{', titles))
    vanilla = json.loads(Path(__file__).with_name('vanilla_landed_titles.json').read_text(encoding='utf-8'))
    stubs = ['# Generated by tools/build_rasen_map.py from tools/vanilla_landed_titles.json']
    stubs += [f'{key} = {{\n\tcapital = c_azuma\n\tlandless = yes\n}}' for key in vanilla if key not in ours]
    files['common/landed_titles/zz_rasen_vanilla_title_stubs.txt'] = ('﻿' + '\n'.join(stubs) + '\n').encode('utf-8')
    files['localization/replace/english/rasen_titles_l_english.yml'] = ('﻿' + loc).encode('utf-8')
    regions = ['# Generated by tools/build_rasen_map.py']
    for region in REGIONS:
        keys = [d['key'] for k in kingdoms if k['key'] == region['key'] for d in k['duchies']]
        regions += [f"world_rasen_{region['key']} = {{", '\tduchies = { ' + ' '.join(keys) + ' }', '}']
    regions += ['world_rasen_inner = { regions = { ' + ' '.join(f"world_rasen_{r['key']}" for r in REGIONS if r['ring'] == 'inner') + ' } }',
                'world_rasen_outer = { regions = { ' + ' '.join(f"world_rasen_{r['key']}" for r in REGIONS if r['ring'] == 'outer') + ' } }']
    # Buildings and units take their look from graphical regions, which must cover the map.
    # Vanilla keys building models and illustrations to its seven graphical regions; reuse East Asia's.
    regions += ['graphical_east_asia = {', '	graphical = yes', '	color = { 200 60 50 }',
                '	regions = { world_rasen_inner world_rasen_outer world_rasen_azuma }', '}']
    files['map_data/geographical_regions/rasen_geographical_regions.txt'] = ('\ufeff' + '\n'.join(regions) + '\n').encode('utf-8')
    # Vanilla scripts name Earth's regions (building rules, decisions, achievements). Keep every
    # vanilla key defined, holding only one impassable ocean zone, so those triggers fail cleanly.
    ours = {line.split(' = ')[0] for line in regions if ' = {' in line}
    vanilla = json.loads(Path(__file__).with_name('vanilla_geographical_regions.json').read_text(encoding='utf-8'))
    stubs = ['# Generated by tools/build_rasen_map.py from tools/vanilla_geographical_regions.json']
    # The few that generate development modifiers keep doing so: buildings and traits name those modifiers.
    generated = set(json.loads(Path(__file__).with_name('vanilla_generated_modifier_regions.json').read_text(encoding='utf-8')))
    stubs += [f'{key} = {{ provinces = {{ {max(ocean_ids)} }}' + (' generate_modifiers = yes' if key in generated else '') + ' }'
              for key in vanilla if key not in ours]
    files['map_data/geographical_regions/00_rasen_vanilla_region_stubs.txt'] = ('﻿' + '\n'.join(stubs) + '\n').encode('utf-8')
    files['map_data/seasons.txt'] = SEASONS.encode('utf-8')
    files['map_data/climate.txt'] = climate(region_of).encode('utf-8')
    files.update(map_object_locators(provinces, land_ids, sea_ids + ocean_ids))
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
    small = Image.fromarray(image).resize((image.shape[1] // 2, image.shape[0] // 2), Image.NEAREST)
    draw = ImageDraw.Draw(small)
    for kingdom in kingdoms:
        for duchy in kingdom['duchies']:
            ps = [b['province'] for c in duchy['counties'] for b in c['baronies']]
            x = sum(centre[p][0] for p in ps) / len(ps) / 2
            y = sum(centre[p][1] for p in ps) / len(ps) / 2
            draw.text((x - 20, y - 5), duchy['name'], fill=(255, 255, 255))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    small.save(PREVIEW)


def _same(path, data):
    """True when path holds data. PNGs compare decoded pixels, since Pillow
    versions compress identical images to different bytes."""
    if not path.exists():
        return False
    current = path.read_bytes()
    if current == data or path.suffix != '.png':
        return current == data
    a, b = Image.open(path), Image.open(io.BytesIO(data))
    with a, b:
        return (a.mode == b.mode and a.size == b.size and a.getpalette() == b.getpalette()
                and np.array_equal(np.asarray(a), np.asarray(b)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Fail if the generated files differ from AuraClash/.')
    args = parser.parse_args()
    files, summary = render(write=not args.check)
    if args.check:
        stale = [r for r, d in files.items() if not _same(OUT / r, d)]
        if stale:
            raise SystemExit('Stale generated files: ' + ', '.join(stale))
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
