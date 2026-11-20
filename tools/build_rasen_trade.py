"""Give Imperial Rasen's counties potential trade goods (CK3 1.21 economy).

CK3 1.21 lists, for every trade good, the counties that may produce it
(common/trade/county_potential_trade_goods). The vanilla list names Earth's counties only
(about 14,000 load errors on this map) and leaves Rasen with no goods at all, so this
builder replaces that file with one drawn from Rasen's own map:

- a county's main terrain gives its staple goods (rice and grain on farmland, timber and
  honey in forest, stone and ore in the mountains, and so on);
- a county that is mostly coast fishes (other shores sometimes), and some also make salt;
- each land adds its own wares: silk and ceramics around Azuma Honsha, ink-and-paper
  crafts and medicine in the Mystic Lands, steel in the Bladed Lands, poisons, dyes and
  black iron in the Cursed Lands, incense in the Sacred Lands, beastbone (ivory) and furs
  in the Wild Lands, snowsteel (silver) and amber in the north;
- the IF's treasure materials are rare: Jade and Truegold (gold) in a few hill and
  mountain counties.

Choices are deterministic (hashed from the county key), so rebuilding gives the same file.

Usage: python tools/build_rasen_trade.py [--check]
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter

import rasen_map_graph as graph

MOD = graph.MOD
OUTPUT = 'common/trade/county_potential_trade_goods/county_potential_trade_goods.txt'

# Every raw good vanilla assigns to counties (CK3 1.21.0); crafted goods come from buildings.
GOODS = ('alum', 'medicaments', 'horses', 'amber', 'honey', 'cattle', 'copper', 'cotton', 'dyes',
         'fish', 'flax', 'fruit', 'furs', 'gems', 'gold', 'grain', 'hemp', 'incense', 'iron', 'ivory',
         'jade', 'millet', 'oil', 'rice', 'salt', 'silk', 'silver', 'spices', 'stone', 'sugar',
         'wine', 'wood', 'wool', 'tea', 'ceramics')

# Staples by the county's main terrain: the first two always, then one more chosen by hash.
TERRAIN_GOODS = {
    'farmlands': ('rice', 'grain', 'cattle', 'flax', 'silk'),
    'plains': ('grain', 'cattle', 'millet', 'horses', 'wool', 'hemp'),
    'drylands': ('millet', 'horses', 'wool', 'cotton'),
    'hills': ('stone', 'wool', 'tea', 'wine', 'oil'),
    'mountains': ('stone', 'iron', 'copper'),
    'forest': ('wood', 'honey', 'medicaments', 'furs'),
    'taiga': ('wood', 'furs', 'honey'),
    'jungle': ('wood', 'fruit', 'spices', 'sugar'),
    'wetlands': ('rice', 'fish', 'hemp', 'dyes'),
    'desert': ('salt', 'incense', 'dyes'),
}
# A second terrain present in the county adds its first staple.

# Each land's own wares: one of them in about two counties out of three.
REGION_GOODS = {
    'azuma': ('silk', 'ceramics', 'tea', 'dyes'),
    'mystic': ('ceramics', 'medicaments', 'silk', 'tea'),
    'bladed': ('iron', 'silk', 'tea', 'horses'),
    'cursed': ('iron', 'alum', 'dyes', 'medicaments', 'hemp'),
    'sacred': ('incense', 'salt', 'medicaments', 'wool'),
    'wild': ('furs', 'ivory', 'spices', 'fruit', 'honey'),
    'outer_north': ('furs', 'silver', 'amber', 'fish'),
    'outer_west': ('wine', 'honey', 'oil', 'flax'),
    'outer_east': ('horses', 'cotton', 'wool', 'salt'),
    'outer_south': ('sugar', 'cotton', 'spices', 'fruit', 'oil'),
}
# Rare goods for hill and mountain counties, by land: one in about half of them.
RARE_GOODS = {
    'azuma': ('jade', 'gold'),
    'mystic': ('jade', 'gems'),
    'bladed': ('gold', 'iron', 'gems'),
    'cursed': ('alum', 'silver'),
    'sacred': ('jade', 'silver', 'gems'),
    'wild': ('gems', 'gold', 'ivory'),
    'outer_north': ('silver', 'gems'),
    'outer_west': ('copper', 'gold'),
    'outer_east': ('copper', 'silver'),
    'outer_south': ('gems', 'gold'),
}
# Goods that must appear somewhere, and where to put them if the rules above miss them.
FALLBACK = {good: ('mountains', 'hills') for good in ('gold', 'jade', 'gems', 'silver', 'copper', 'alum')}
FALLBACK.update({'amber': ('taiga', 'forest'), 'ivory': ('jungle', 'forest'), 'incense': ('desert', 'hills'),
                 'salt': ('desert', 'drylands'), 'fish': ('wetlands',), 'oil': ('hills',), 'wine': ('hills',)})
MINIMUM = 3


def roll(key: str, salt: str) -> int:
    return int(hashlib.sha256(f'{key}:{salt}'.encode()).hexdigest()[:8], 16)


def parse_counties() -> dict[str, dict]:
    """County key -> {'region', 'duchy', 'provinces'} (see rasen_map_graph.counties)."""
    return graph.counties()


def assign(counties: dict[str, dict], terrain: dict, coastal: set[int]) -> dict[str, set[str]]:
    goods: dict[str, set[str]] = {}
    main_terrain: dict[str, str] = {}
    for key, info in sorted(counties.items()):
        kinds = Counter(terrain.get(p, terrain['default']) for p in info['provinces'])
        # Ties go to the first barony (the county seat).
        first = terrain.get(info['provinces'][0], terrain['default'])
        main = max(kinds, key=lambda t: (kinds[t], t == first))
        main_terrain[key] = main
        staples = TERRAIN_GOODS.get(main, TERRAIN_GOODS['plains'])
        chosen = set(staples[:2])
        if len(staples) > 2:
            chosen.add(staples[2 + roll(key, 'staple') % (len(staples) - 2)])
        for other in kinds:
            if other != main:
                chosen.add(TERRAIN_GOODS.get(other, TERRAIN_GOODS['plains'])[0])
        region = info['region']
        wares = REGION_GOODS.get(region, ())
        if wares and roll(key, 'region') % 3:
            chosen.add(wares[roll(key, 'ware') % len(wares)])
        rares = RARE_GOODS.get(region, ())
        if rares and main in ('hills', 'mountains') and roll(key, 'rare') % 2 == 0:
            chosen.add(rares[roll(key, 'which_rare') % len(rares)])
        # Rasen's spiral gives most counties a shore; fishing is a staple only where nearly
        # all of the county is coast, and an occasional extra elsewhere.
        shore = sum(p in coastal for p in info['provinces']) / len(info['provinces'])
        if shore >= 0.75 or (shore and roll(key, 'fish') % 4 == 0):
            chosen.add('fish')
            if roll(key, 'salt') % 5 == 0:
                chosen.add('salt')
        filler = list(TERRAIN_GOODS.get(main, TERRAIN_GOODS['plains']))
        while len(chosen) < MINIMUM and filler:
            chosen.add(filler.pop(0))
        goods[key] = chosen
    # Every good must be reachable somewhere: place missing ones on the best-suited counties.
    counts = Counter(g for chosen in goods.values() for g in chosen)
    for good in GOODS:
        if counts[good] >= 2:
            continue
        preferred = FALLBACK.get(good, ('plains',))
        candidates = sorted((roll(key, good), key) for key in goods if main_terrain[key] in preferred) or \
            sorted((roll(key, good), key) for key in goods)
        for _, key in candidates[:2 - counts[good]]:
            goods[key].add(good)
    return goods


def render() -> dict[str, bytes]:
    counties = parse_counties()
    goods = assign(counties, graph.terrain(), graph.coastal_provinces())
    lines = ['# Generated by tools/build_rasen_trade.py: the counties of Imperial Rasen that may produce each good.',
             '# Replaces the vanilla list, which names only Earth counties.', '']
    for good in GOODS:
        keys = sorted(key for key, chosen in goods.items() if good in chosen)
        lines.append(f'trade_good_{good} = {{')
        lines.append('\tcounties = {')
        lines += [f'\t\t{key}' for key in keys]
        lines += ['\t}', '}', '']
    return {OUTPUT: ('﻿' + '\n'.join(lines).rstrip('\n') + '\n').encode('utf-8')}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = [r for r, d in files.items() if not (MOD / r).exists() or (MOD / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale trade goods: ' + ', '.join(stale))
        print('Trade goods are current.')
        return
    for relative, data in files.items():
        path = MOD / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f'Trade goods: {len(GOODS)} goods over Rasen\'s counties.')


if __name__ == '__main__':
    main()
