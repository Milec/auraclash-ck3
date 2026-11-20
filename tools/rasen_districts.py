"""Starting districts for Imperial Rasen's provinces (CK3 1.21, Silk and Silver).

CK3 1.21 builds each holding out of districts, and vanilla history gives a settled 1066 province
its holding district and three to five more (villages, manors, a resource district, walls).
Rasen's empire is thousands of years old, so its provinces start the same way, scaled by rank:

- every holding: its holding district (level 3 at a county seat, 2 elsewhere) and villages;
- county seats: a district for one of the county's trade goods (common/trade, build_rasen_trade.py),
  and for castles a military district;
- duchy seats (the trade markets) are larger, walled, and have a port on the coast;
- realm capitals and Azuma Honsha are the great cities: markets, urban housing, larger still;
- **entrepots**, Silk and Silver's great ports, sit at the busiest coastal markets: the ends of
  the sea roads (build_rasen_roads.py) and coastal realm capitals, at most ENTREPOTS of them.

build_rasen_world.py adds these lines to history/provinces/rasen_provinces.txt.
"""
from __future__ import annotations

from functools import lru_cache

import build_rasen_roads as roads
import build_rasen_trade as trade
import rasen_map_graph as graph

ENTREPOTS = 20
HOLDING_DISTRICT = {'castle_holding': 'castle_holding_district', 'city_holding': 'city_holding_district',
                    'church_holding': 'temple_holding_district', 'tribal_holding': 'tribal_holding_district'}
# The resource district each trade good allows (vanilla common/districts/resource_districts.txt).
# Rice is left out: its district also needs an East Asian culture.
RESOURCE_DISTRICT = {
    'wood': 'forestry_district', 'grain': 'grain_district', 'wool': 'wool_district', 'cattle': 'cattle_district',
    'cotton': 'cotton_district', 'stone': 'stone_district', 'fish': 'fish_district', 'wine': 'wine_district',
    'oil': 'oil_district', 'millet': 'millet_district', 'salt': 'salt_district', 'amber': 'amber_district',
    'silk': 'silk_district', 'furs': 'furs_district', 'spices': 'spices_district', 'tea': 'tea_district',
    'dyes': 'dyes_district', 'ivory': 'ivory_district', 'sugar': 'sugar_district', 'incense': 'incense_district',
    'medicaments': 'medicaments_district', 'ceramics': 'ceramics_district', 'hemp': 'hemp_district',
    'flax': 'flax_district', 'honey': 'honey_district', 'fruit': 'fruit_district', 'horses': 'horses_district',
    **{g: 'mine_district' for g in ('iron', 'copper', 'gold', 'silver', 'gems', 'alum', 'jade')},
}
# Province size (CK3 1.21 province_size, 1 when history omits it) by rank.
SIZE = {'hub': 8, 'realm': 6, 'duchy': 4, 'county': 2}


@lru_cache(maxsize=None)
def ranks() -> dict[int, str]:
    """Province -> 'hub' (Azuma Honsha), 'realm', 'duchy' or 'county' seat."""
    titles, counties = graph.titles(), graph.counties()
    seat = {key: info['provinces'][0] for key, info in counties.items()}
    rank = {p: 'county' for p in seat.values()}
    for key, info in titles.items():
        if info['capital'] in seat:
            if info['tier'] == 'd':
                rank[seat[info['capital']]] = 'duchy'
    for key, info in titles.items():
        if info['tier'] == 'k' and info['capital'] in seat:
            rank[seat[info['capital']]] = 'realm'
    rank[seat[titles[roads.CAPITAL]['capital']]] = 'hub'
    return rank


@lru_cache(maxsize=None)
def county_of() -> dict[int, str]:
    return {p: key for key, info in graph.counties().items() for p in info['provinces']}


@lru_cache(maxsize=None)
def goods() -> dict[str, set[str]]:
    return trade.assign(graph.counties(), graph.terrain(), graph.coastal_provinces())


@lru_cache(maxsize=None)
def entrepots() -> frozenset[int]:
    """The busiest coastal markets: sea-road ends and coastal realm capitals, by road count."""
    coastal, rank = graph.coastal_provinces(), ranks()
    built = roads.build()
    ends: dict[int, int] = {}
    sea_ends = set()
    for road in built:
        for p in (road['path'][0], road['path'][-1]):
            ends[p] = ends.get(p, 0) + 1
            if road['sea']:
                sea_ends.add(p)
    candidates = {p for p in sea_ends | {p for p, r in rank.items() if r in ('hub', 'realm')} if p in coastal}
    order = sorted(candidates, key=lambda p: (rank[p] not in ('hub', 'realm'), -ends.get(p, 0), p))
    return frozenset(order[:ENTREPOTS])


def resource(province: int) -> str | None:
    county = county_of()[province]
    for good in sorted(goods()[county], key=lambda g: trade.roll(county, 'district:' + g)):
        if good in RESOURCE_DISTRICT:
            return RESOURCE_DISTRICT[good]
    return None


def districts(province: int, holding: str) -> list[tuple[str, int]]:
    """(district, level) pairs for one province, holding district first."""
    if holding not in HOLDING_DISTRICT:
        return []
    rank = ranks().get(province)
    tribal = holding == 'tribal_holding'
    out = [(HOLDING_DISTRICT[holding], 2 if tribal or not rank else 3)]
    if tribal:
        if rank and resource(province):
            out.append((resource(province), 1))
        if province in entrepots():
            out.append(('entrepot_location_district', 1))
        return out
    out.append(('villages_district', 2))
    if rank:
        if resource(province):
            out.append((resource(province), 2))
        if holding == 'castle_holding':
            out.append(('military_district', 1))
        elif holding == 'church_holding':
            out.append(('religious_community_district', 1))
        else:
            out.append(('manor_houses_district', 1))
    if rank in ('duchy', 'realm', 'hub'):
        out.append(('walls_district', 2 if rank == 'duchy' else 3))
        if province in graph.coastal_provinces():
            out.append(('port_district', 1 if rank == 'duchy' else 2))
    if rank in ('realm', 'hub'):
        out += [('market_district', 2 if rank == 'realm' else 3), ('urban_housing_district', 2)]
    if province in entrepots():
        out.append(('entrepot_location_district', 1 if rank == 'duchy' else 2))
    return out


def history_lines(province: int, holding: str, year: int) -> list[str]:
    """A dated history entry for build_rasen_world.py, or nothing for an empty barony."""
    found = districts(province, holding)
    if not found:
        return []
    rank = ranks().get(province)
    lines = [f'{year}.1.1 = {{']
    if rank in SIZE:
        lines.append(f'\tprovince_size = {SIZE[rank]}')
    lines.append('\tdistricts = {')
    for kind, level in found:
        lines.append(f'\t\tdistrict = {{ type = {kind} level = {level} }}')
    lines += ['\t}', '}']
    return lines


LOCATORS = 'gfx/map/map_object_data/entrepot_locators.txt'


def entrepot_positions() -> dict[int, tuple[float, float]]:
    """Where CK3 draws each coastal province's entrepot: just offshore from the stretch of coast
    nearest the province's centre (map x, CK3 z, which runs bottom-up). Every coastal province has
    one, so entrepots that script adds later can be drawn too; inland provinces sit at their centre."""
    import numpy as np
    grid = graph._grid()
    height = grid.shape[0]
    water = np.isin(grid, sorted(graph.water_ids() - graph.impassable_seas()))
    shore = np.zeros(grid.shape, bool)
    pull_x = np.zeros(grid.shape)
    pull_y = np.zeros(grid.shape)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        neighbour = np.roll(water, (-dy, -dx), axis=(0, 1))
        touch = neighbour & ~water & (grid > 0)
        shore |= touch
        pull_x += touch * dx
        pull_y += touch * dy
    centres = graph.centres()
    out = {}
    ys, xs = np.nonzero(shore)
    ids = grid[ys, xs]
    for province in sorted(graph.coastal_provinces()):
        pick = np.nonzero(ids == province)[0]
        if not len(pick):
            continue
        cx, cy = centres[province]
        best = pick[np.argmin((xs[pick] - cx) ** 2 + (ys[pick] - cy) ** 2)]
        y, x = ys[best], xs[best]
        x_off, y_off = pull_x[y, x], pull_y[y, x]
        norm = max(1.0, (x_off ** 2 + y_off ** 2) ** 0.5)
        out[province] = (x + 0.5 + 2.5 * x_off / norm, (height - 1 - y) + 0.5 - 2.5 * y_off / norm)
    # CK3 wants a locator for every land province ("incomplete" otherwise); inland ones never hold an entrepot.
    for province, (cx, cy) in centres.items():
        if province not in out and province not in graph.water_ids():
            out[province] = (cx + 0.5, (height - 1 - cy) + 0.5)
    return out


def render() -> dict[str, bytes]:
    lines = ['game_object_locator={', '\tname="entrepot"', '\trender_pass=Map', '\tclamp_to_water_level=yes',
             '\tgenerated_content=no', '\tlayer="building_layer"', '\tinstances={']
    for province, (x, z) in sorted(entrepot_positions().items()):
        lines += ['\t\t{', f'\t\t\tid={province}', f'\t\t\tposition={{ {x:.6f} 0.000000 {z:.6f} }}',
                  '\t\t\trotation={ -0.000000 0.000000 -0.000000 1.000000 }',
                  '\t\t\tscale={ 1.000000 1.000000 1.000000 }', '\t\t}']
    lines += ['\t}', '}']
    return {LOCATORS: ('﻿' + '\n'.join(lines) + '\n').encode('utf-8')}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description='Write the entrepot locators (the districts go into '
                                                 'the province history through build_rasen_world.py).')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = [r for r, d in files.items() if not (graph.MOD / r).exists() or (graph.MOD / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale: ' + ', '.join(stale))
        return
    for relative, data in files.items():
        (graph.MOD / relative).write_bytes(data)
    print(f'Entrepot locators: {len(entrepot_positions())} provinces; {len(entrepots())} entrepots at the start.')


if __name__ == '__main__':
    main()
