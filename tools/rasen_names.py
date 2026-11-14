"""Deterministic place names for Imperial Rasen, in a distinct style per region."""
from __future__ import annotations

import random
import re

ZEN = ['ka', 'ki', 'ku', 'ko', 'sa', 'shi', 'su', 'se', 'so', 'ta', 'chi', 'tsu', 'to', 'na', 'ni', 'no', 'ha', 'hi',
       'fu', 'ho', 'ma', 'mi', 'mo', 'ya', 'yu', 'yo', 'ra', 'ri', 'ro', 'wa', 'ga', 'go', 'ji', 'da', 'ba', 'be', 'ze']
CATHAY = ['Lan', 'Shu', 'Qing', 'Mei', 'Yun', 'Hua', 'Jin', 'Ling', 'Xuan', 'Zhao', 'Feng', 'Bai', 'Tian', 'Luo',
          'Wen', 'Yao', 'Kun', 'Su', 'Ming', 'Hou', 'Nan', 'Long', 'Xi', 'Rui', 'Guang', 'He', 'Jing', 'Zhen']
WORDS = {
    'outer_west': (['Thunder', 'Rolling', 'Stone', 'Copper', 'Mist', 'Wind', 'Iron', 'Cedar', 'Rain', 'Red', 'Long', 'Bright', 'High', 'Ember', 'Pine'],
                   ['fall', 'ford', 'reach', 'hollow', 'crest', 'field', 'watch', 'brook', 'stead', 'vale', 'gate', 'rise']),
    'outer_north': (['Frost', 'White', 'Snow', 'Ice', 'Brass', 'Winter', 'Pale', 'Hail', 'Grey', 'Glacier', 'Rime', 'Storm'],
                    ['fang', 'peak', 'hold', 'wall', 'march', 'watch', 'spire', 'drift', 'bastion', 'pass', 'reach', 'fort']),
    'outer_south': (['Sun', 'Salt', 'Reed', 'Coral', 'Amber', 'Wave', 'Jade', 'Lotus', 'Tide', 'Silk', 'Gold', 'Moss'],
                    ['harbour', 'shore', 'bay', 'field', 'haven', 'marsh', 'point', 'grove', 'cove', 'terrace', 'dale', 'well']),
    'wild': (['Iron', 'Great', 'Blood', 'Beast', 'Root', 'Fang', 'Thorn', 'Bone', 'Elder', 'Howl', 'Tusk', 'Wild', 'Green'],
             ['claw', 'root', 'den', 'maw', 'grove', 'arena', 'pit', 'hide', 'thicket', 'roar', 'run', 'tangle']),
}
ZEN_SUFFIX = {
    'outer_east': ['hama', 'mura', 'saki', 'ichi', 'gura', 'zawa', 'no', 'oka'],
    'bladed': ['jo', 'zaki', 'yama', 'mori', 'hara', 'gawa', 'dake', 'kawa'],
    'cursed': ['kage', 'yami', 'numa', 'kubo', 'tani', 'mura', 'zaka', 'mori'],
    'sacred': ['ji', 'san', 'dera', 'miya', 'yama', 'take', 'sawa', 'mine'],
    'azuma': ['kyo', 'machi', 'za', 'cho', 'bashi', 'mon', 'den', 'ura'],
    'outer_west': ['mura', 'hara', 'yama', 'saka'],
    'outer_north': ['yuki', 'mine', 'dake', 'sawa'],
    'outer_south': ['hama', 'shima', 'ura', 'ta'],
    'wild': ['mori', 'no', 'kiba', 'gari'],
}
CATHAY_SUFFIX = {'mystic': ['zhou', 'ling', 'shan', 'tai', 'yuan', 'cheng', 'lou', 'he']}


def slug(name):
    return re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')


class NameForge:
    def __init__(self, spec, seed=0):
        self.rng = random.Random(seed)
        self.used = set()
        self.keys = set()
        self.canon = spec.get('canon', {})
        self.style = {r['key']: r['style'] for r in spec['regions']}

    def _zen(self, region):
        stem = ''.join(self.rng.choice(ZEN) for _ in range(self.rng.choice((1, 2, 2))))
        return (stem + self.rng.choice(ZEN_SUFFIX[region])).capitalize()

    def _cathay(self, region):
        first = self.rng.choice(CATHAY)
        return first + self.rng.choice(CATHAY_SUFFIX[region])

    def _compound(self, style):
        head, tail = WORDS[style]
        return self.rng.choice(head) + self.rng.choice(tail)

    def raw(self, region):
        style = self.style[region]
        if style in WORDS:
            if style == 'outer_west' and self.rng.random() < 0.3:
                return self.rng.choice(CATHAY) + self.rng.choice(['hou', 'an', 'zhou', 'ling'])
            if self.rng.random() < 0.55:
                return self._compound(style)
            return self._zen(style)
        if style in CATHAY_SUFFIX:
            return self._cathay(style)
        return self._zen(style)

    def unique(self, region):
        for _ in range(500):
            name = self.raw(region)
            if name not in self.used:
                self.used.add(name)
                return name
        raise RuntimeError(f'Name space exhausted for {region}')

    def key(self, prefix, name):
        base = f'{prefix}_{slug(name)}'
        key, n = base, 2
        while key in self.keys:
            key, n = f'{base}_{n}', n + 1
        self.keys.add(key)
        return key

    def duchy(self, region):
        return self.unique(region)

    def county(self, region):
        return self.unique(region)

    def barony(self, region):
        return self.unique(region)

    def apply_canon(self, kingdom):
        """Rename the first counties/baronies with canonical names, then assign keys."""
        canon = self.canon.get(kingdom['key'], {})
        counties = [c for d in kingdom['duchies'] for c in d['counties']]
        baronies = [b for c in counties for b in c['baronies'][1:]] or [b for c in counties for b in c['baronies']]
        for county, name in zip(counties, canon.get('counties', [])):
            county['name'] = name
            county['baronies'][0]['name'] = name
        for barony, name in zip(baronies[::7], canon.get('baronies', [])):
            barony['name'] = name
        for duchy in kingdom['duchies']:
            duchy['key'] = self.key('d', duchy['name'])
            for county in duchy['counties']:
                county['key'] = self.key('c', county['name'])
                for barony in county['baronies']:
                    barony['key'] = self.key('b', barony['name'])
