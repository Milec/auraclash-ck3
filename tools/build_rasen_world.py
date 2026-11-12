"""Generate Imperial Rasen's peoples, faiths and starting history for AuraClash/.

Reads the landed titles produced by build_rasen_map.py and writes:
  common/culture/{pillars,cultures,name_lists}/   Zenshin, Cathayan, Oni, Yokai, Kitsune
  common/religion/{religions,holy_sites}/          Ancestral Rites, the Devanic Faith, the Wild Gods
  common/dynasties/, history/{characters,titles,provinces}/
  common/bookmarks/, common/defines/, localization/english/
Usage: python tools/build_rasen_world.py [--check]
"""
from __future__ import annotations

import argparse
import random
import re
from pathlib import Path

from rasen_world_data import (BOOKMARK, CANON_CAST, CULTURE_RACE, DIVINE_GENERAL, YOKAI_KINDS, INNOVATIONS, MORTAL_LIMIT_BONUS, SECT_SEATS, SECT_STANDING, CANON_HOLDERS, CULTURES, EXALTS, FAITHS, HOLY_SITES,
                              NAME_LISTS, RELIGIONS, REGION_PEOPLES, RELIGION_LOC_KEYS, START, TRAIT_GROUPS)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
TITLES = OUT / 'common/landed_titles/00_rasen_titles.txt'
BOM = '﻿'
SEED = 3000


def parse_titles():
    """Return {kingdom: [duchy: {key, counties: [{key, baronies: [(key, province)]}]}]}."""
    kingdoms, k, d, c = {}, None, None, None
    pending = None
    for line in TITLES.read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'^(\t*)([ekdcb])_(\w+) = \{', line)
        if m:
            tier, key = m.group(2), f'{m.group(2)}_{m.group(3)}'
            if tier == 'k':
                k = key; kingdoms[k] = []
            elif tier == 'd':
                d = {'key': key, 'counties': []}; kingdoms[k].append(d)
            elif tier == 'c':
                c = {'key': key, 'baronies': []}; d['counties'].append(c)
            elif tier == 'b':
                pending = key
            continue
        m = re.match(r'^\t*province = (\d+)', line)
        if m and pending:
            c['baronies'].append((pending, int(m.group(1))))
            pending = None
    return kingdoms


def block(name, body, depth=0):
    pad = '\t' * depth
    return f'{pad}{name} = {{\n' + ''.join(f'{pad}\t{line}\n' if not line.endswith('\n') else line for line in body) + f'{pad}}}\n'


# ----------------------------------------------------------------------------
# Peoples
# ----------------------------------------------------------------------------
def culture_files():
    pillars, cultures, loc = [], [], ['l_english:']
    for heritage in sorted({c['heritage'] for c in CULTURES.values()}):
        pillars.append(f'{heritage} = {{\n\ttype = heritage\n\taudio_parameter = sea\n}}\n')
    languages = {}
    for c in CULTURES.values():
        languages.setdefault(c['language'], c['colour'])
    for language, colour in languages.items():
        pillars.append(f'{language} = {{\n\ttype = language\n\tcolor = {{ {colour[0]} {colour[1]} {colour[2]} }}\n}}\n')
    for key, c in CULTURES.items():
        body = [f"color = {{ {c['colour'][0]} {c['colour'][1]} {c['colour'][2]} }}",
                f"ethos = {c['ethos']}", f"heritage = {c['heritage']}", f"language = {c['language']}",
                f"martial_custom = {c['martial_custom']}", 'head_determination = head_determination_domain',
                'traditions = { ' + ' '.join(c['traditions']) + ' }',
                f"name_list = {c['name_list']}",
                'coa_gfx = { ' + ' '.join(c['coa_gfx']) + ' }',
                'building_gfx = { ' + ' '.join(c['building_gfx']) + ' }',
                'clothing_gfx = { ' + ' '.join(c['clothing_gfx']) + ' }',
                'unit_gfx = { ' + ' '.join(c['unit_gfx']) + ' }',
                'ethnicities = { 10 = ' + c['ethnicity'] + ' }']
        cultures.append(block(key, body))
        loc += [f' {key}:0 "{c["name"]}"', f' {key}_prefix:0 "{c["prefix"]}"',
                f' {key}_collective_noun:0 "{c["plural"]}"', f' {key}_desc:0 "{c["desc"]}"']
    for heritage, name in {c['heritage']: c['heritage_name'] for c in CULTURES.values()}.items():
        loc += [f' {heritage}_name:0 "{name}"', f' {heritage}_collective_noun:0 "{name}"']
    for language, name in {c['language']: c['language_name'] for c in CULTURES.values()}.items():
        loc += [f' {language}_name:0 "{name}"']
    names = []
    for key, n in NAME_LISTS.items():
        body = ['cadet_dynasty_names = { ' + ' '.join(f'"{x}"' for x in n['dynasties'][:12]) + ' }',
                'dynasty_names = { ' + ' '.join(f'"{x}"' for x in n['dynasties']) + ' }',
                'male_names = { ' + ' '.join(n['male']) + ' }',
                'female_names = { ' + ' '.join(n['female']) + ' }']
        names.append(block(key, body))
        loc.append(f' {key}:0 "{n["label"]}"')
    histories = {}
    for key in CULTURES:
        histories[f'history/cultures/{key}.txt'] = (f'{START[0] - 100}.1.1 = {{\n\tjoin_era = culture_era_early_medieval\n'
                                                   + ''.join(f'\tdiscover_innovation = {i}\n' for i in INNOVATIONS) + '}\n')
    return {
        **histories,
        'common/culture/pillars/rasen_pillars.txt': '\n'.join(pillars),
        'common/culture/cultures/rasen_cultures.txt': '\n'.join(cultures),
        'common/culture/name_lists/rasen_name_lists.txt': '\n'.join(names),
    }, loc


# ----------------------------------------------------------------------------
# Faiths
# ----------------------------------------------------------------------------
def religion_files(kingdoms):
    county_of = {b: c['key'] for ds in kingdoms.values() for d in ds for c in d['counties'] for b, _ in c['baronies']}
    sites, loc = [], ['l_english:']
    for key, site in HOLY_SITES.items():
        barony = site['barony'] if site['barony'] in county_of else resolve_site(kingdoms, site)
        # CK3 1.20: holy_site_types. Every Rasen site is eminent, so faith_character_modifier applies.
        sites.append(block(key, [f'county = {county_of[barony]}', f'barony = {barony}', 'faith_character_modifier = {',
                                 *[f'\t{k} = {v}' for k, v in site['modifier'].items()], '}']))
        loc += [f' holy_site_{key}_name:0 "{site["name"]}"']
    religions, faiths, rites = [], [], []
    for rkey, r in RELIGIONS.items():
        body = ['religion_details = {', f"\tfamily = {r['family']}", f"\tgraphical_faith = {r['graphical_faith']}",
                f"\tpiety_icon_group = {r['piety_icon_group']}", '}', 'pagan_roots = yes' if r.get('pagan_roots') else '',
                *[f'doctrine = {x}' for x in r['doctrines']],
                'traits = {', '\tvirtues = { ' + ' '.join(r['virtues']) + ' }',
                '\tsins = { ' + ' '.join(r['sins']) + ' }', '}',
                'custom_faith_icons = { ' + ' '.join(f'custom_faith_{i}' for i in range(1, 11)) + ' }',
                'holy_order_names = { { name = "' + r['holy_order'] + '" } }',
                'holy_order_maa = { light_horsemen }', 'localization = {']
        for loc_key in RELIGION_LOC_KEYS:
            loc_id = f'{rkey}_{loc_key}'.lower()
            body.append(f'\t{loc_key} = {loc_id}')
            loc.append(f' {loc_id}:0 "{religion_text(r, loc_key)}"')
        body += ['\tGoodGodNames = { ' + ' '.join(f'{rkey}_good_god_{i}'.lower() for i in range(len(r['good_gods']))) + ' }',
                 '\tEvilGodNames = { ' + ' '.join(f'{rkey}_evil_god_{i}'.lower() for i in range(len(r['evil_gods']))) + ' }', '}']
        loc += [f' {rkey}_good_god_{i}:0 "{g}"' for i, g in enumerate(r['good_gods'])]
        loc += [f' {rkey}_evil_god_{i}:0 "{g}"' for i, g in enumerate(r['evil_gods'])]
        # CK3 1.20: faiths are faith_types that name their religion. Each has a scripted main Rite
        # with the faith's own key (as vanilla does), which history assigns with `rite =`.
        # The Rite owns the core tenets.
        for fkey, f in FAITHS.items():
            if f['religion'] != rkey:
                continue
            rbody = [f'faith = {fkey}', f"color = {{ {f['colour'][0]} {f['colour'][1]} {f['colour'][2]} }}",
                     'tenets = {', *[f'\t{t}' for t in f['tenets']], '}']
            if f.get('doctrines'):
                rbody += ['doctrines = {', *[f'\t{d}' for d in f['doctrines']], '}']
            rites.append(block(fkey, rbody))
            fbody = [f'main_rite = {fkey}', 'faith_details = {', f'\treligion = {rkey}',
                     f"\tcolor = {{ {f['colour'][0]} {f['colour'][1]} {f['colour'][2]} }}", f"\ticon = {f['icon']}",
                     f"\treformed_icon = {f['icon']}", '}',
                     'eminent_holy_sites = {', *[f'\t{s}' for s in f['holy_sites']], '}']
            faiths.append(block(fkey, fbody))
            loc += [f' {fkey}:0 "{f["name"]}"', f' {fkey}_adj:0 "{f["adjective"]}"',
                    f' {fkey}_adherent:0 "{f["adherent"]}"', f' {fkey}_adherent_plural:0 "{f["adherents"]}"',
                    f' {fkey}_desc:0 "{f["desc"]}"']
        religions.append(block(rkey, [x for x in body if x]))
        loc += [f' {rkey}:0 "{r["name"]}"', f' {rkey}_adj:0 "{r["adjective"]}"',
                f' {rkey}_adherent:0 "{r["adherent"]}"', f' {rkey}_adherent_plural:0 "{r["adherents"]}"',
                f' {rkey}_desc:0 "{r["desc"]}"', f' {r["holy_order"]}:0 "{r["holy_order_name"]}"']
    return {
        'common/religion/religion_types/rasen_religions.txt': '\n'.join(religions),
        'common/religion/faith_types/rasen_faiths.txt': '\n'.join(faiths),
        'common/religion/rite_types/rasen_rites.txt': '\n'.join(rites),
        'common/religion/holy_site_types/rasen_holy_sites.txt': '\n'.join(sites),
    }, loc


def religion_text(r, key):
    """Fill the long tail of religion localization keys from a few core terms."""
    core = r['loc']
    if key in core:
        return core[key]
    pronoun = {'SheHe': core['god_pronoun'][0], 'HerHis': core['god_pronoun'][1], 'HerHim': core['god_pronoun'][2],
               'HerselfHimself': core['god_pronoun'][3]}
    for god in ('HighGod', 'Creator', 'HealthGod', 'FertilityGod', 'WealthGod', 'HouseholdGod', 'FateGod',
                'KnowledgeGod', 'WarGod', 'TricksterGod', 'NightGod', 'WaterGod', 'DeathDeity', 'WitchGod', 'Devil'):
        if key.startswith(god):
            base = core.get(god + 'Name', core['HighGodName'])
            rest = key[len(god):]
            if rest in ('Name', 'NameAlternate'):
                return base
            if rest in ('NamePossessive', 'NameAlternatePossessive'):
                return base + "'s"
            for suffix, value in pronoun.items():
                if rest.endswith(suffix):
                    return value
            if rest == 'MistressMaster':
                return 'master'
            if rest == 'MotherFather':
                return 'father'
            return base
    plural = key.endswith('Plural')
    stem = key[:-6] if plural else key
    for prefix, term in (('Devotee', 'devotee'), ('Priest', 'priest'), ('Bishop', 'bishop'), ('AltPriestTerm', 'priest')):
        if stem.startswith(prefix):
            word = core.get(term, term)
            return word + ('s' if plural or prefix == 'AltPriestTerm' else '')
    if key.startswith('PositiveAfterLife'):
        return core['paradise']
    if key.startswith('NegativeAfterLife'):
        return core['hell']
    if key.startswith('DivineRealm'):
        return core['realm']
    if key.startswith('GHWName'):
        return core['holy_war'] + ('s' if plural else '')
    if key.startswith('HouseOfWorship'):
        return core['temple'] + ('s' if plural else '')
    if key == 'PantheonTermHasHave':
        return 'has'
    # Numbered and gendered variants (ReligiousText2, ReligiousHeadNameFemale) reuse the base term.
    base_key = re.sub(r'(\d|Female)$', '', key)
    if base_key in core:
        return core[base_key]
    return core.get('fallback', r['name'])


def resolve_site(kingdoms, site):
    """Fallback: a barony in the named kingdom's n-th county."""
    duchies = kingdoms[site['kingdom']]
    counties = [c for d in duchies for c in d['counties']]
    return counties[site.get('county_index', 0) % len(counties)]['baronies'][0][0]


# ----------------------------------------------------------------------------
# History
# ----------------------------------------------------------------------------
class People:
    def __init__(self, rng):
        self.rng = rng
        self.characters = []
        self.dynasties = {}
        self.next_id = 1
        self.info = {}

    def dynasty(self, name, culture):
        key = 'dynasty_rasen_' + re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
        if key not in self.dynasties:
            self.dynasties[key] = (name, culture)
        return key

    def person(self, culture, faith, name=None, dynasty=None, female=None, age=None, cultivator=0, traits=(), effects=()):
        n = NAME_LISTS[CULTURES[culture]['name_list']]
        female = self.rng.random() < 0.35 if female is None else female
        name = name or self.rng.choice(n['female' if female else 'male'])
        dynasty = dynasty or self.dynasty(self.rng.choice(n['dynasties']), culture)
        age = age or self.rng.randint(24, 58)
        cid = f'rasen_{self.next_id}'
        self.next_id += 1
        personality = []
        free = [g for g in TRAIT_GROUPS if not set(g) & set(traits)]
        fixed = [t for t in traits if any(t in g for g in TRAIT_GROUPS)]
        for group in self.rng.sample(free, max(0, 3 - len(fixed))):
            personality.append(self.rng.choice(group))
        edu = self.rng.choice(['martial', 'stewardship', 'diplomacy', 'intrigue', 'learning'])
        # Names are localization keys; one with a space (Black Flower) uses underscores.
        lines = [f'name = "{re.sub(r"[^A-Za-z0-9_]", "_", name)}"', f'dynasty = {dynasty}', f'rite = {faith}', f'culture = {culture}']
        race = CULTURE_RACE[culture]
        lines.append(f'trait = ac_race_{self.rng.choice(YOKAI_KINDS) if race == "yokai" else race}')
        if female:
            lines.append('female = yes')
        lines += [f'trait = {t}' for t in personality + [f'education_{edu}_{self.rng.randint(2, 4)}'] + list(traits)]
        if cultivator:
            lines.append('trait = ac_cultivator')
        year, month, day = START
        birth = f'{year - age}.{self.rng.randint(1, 12)}.{self.rng.randint(1, 28)}'
        lines.append(f'{birth} = {{ birth = yes }}')
        develop = {1: 'ac_develop_upper_effect', 2: 'ac_develop_master_effect', 3: 'ac_develop_grandmaster_effect'}.get(cultivator)
        effect_lines = ([f'{develop} = yes'] if develop else []) + list(effects)
        if effect_lines:
            lines.append(f'{year}.{month}.{day} = {{ effect = {{ ' + ' '.join(effect_lines) + ' } }')
        self.characters.append((cid, lines))
        self.info[cid] = dict(culture=culture, faith=faith, dynasty=dynasty, female=female, age=age, lines=lines)
        return cid

    def family(self, cid, rng):
        """A spouse and one to three children, so the house survives its founder."""
        ruler = self.info[cid]
        if ruler['age'] < 22:
            return
        year = START[0]
        n = NAME_LISTS[CULTURES[ruler['culture']]['name_list']]
        spouse_age = max(18, ruler['age'] + rng.randint(-6, 4))
        spouse_dynasty = self.dynasty(rng.choice([d for d in n['dynasties']]), ruler['culture'])
        spouse = self.person(ruler['culture'], ruler['faith'], female=not ruler['female'], age=spouse_age, dynasty=spouse_dynasty)
        married = year - min(ruler['age'], spouse_age) + 18
        verb = 'add_matrilineal_spouse' if ruler['female'] else 'add_spouse'
        ruler['lines'].append(f'{married}.1.1 = {{ {verb} = {spouse} }}')
        mother, father = (cid, spouse) if ruler['female'] else (spouse, cid)
        youngest = max(0, min(ruler['age'], spouse_age) - 40)
        oldest = min(ruler['age'], spouse_age) - 19
        if oldest < youngest:
            return
        for _ in range(rng.randint(1, 3)):
            child_age = rng.randint(youngest, oldest)
            child = self.person(ruler['culture'], ruler['faith'], age=max(child_age, 1), dynasty=ruler['dynasty'])
            self.info[child]['lines'][1:1] = [f'father = {father}', f'mother = {mother}']


# The Council's bureaucracy: All Under Heaven's merit government for realms outside China's dynastic
# cycle (appointed governors, merit ranks, a treasury). The Exalts keep their own kingdoms as kings.
OUTER_GOVERNMENT = 'meritocratic_government'
STEWARD_REGION = 'azuma'
# The Wild Lands are not unified: about thirteen Maos each run a faction and threaten the others.
# The strongest holds the Wild seat on the Council; the rest answer only to the hegemony.
UNRULY_REGION, RIVAL_MAOS = 'wild', 3
MAO_TITLES = {'duchy': [], 'county': []}


def history_files(kingdoms):
    rng = random.Random(SEED)
    people = People(rng)
    date = '{}.{}.{}'.format(*START)
    early = f'{START[0] - 10}.1.1'
    titles, provinces, loc = [], [], ['l_english:']
    bookmark_ids = {}
    rivals = {}
    MAO_TITLES['duchy'].clear()
    MAO_TITLES['county'].clear()
    for kingdom, duchies in kingdoms.items():
        region = kingdom[2:]
        peoples = REGION_PEOPLES[region]
        exalt = EXALTS.get(region)
        king = None
        if exalt:
            culture, faith = exalt['culture'], exalt['faith']
            king = people.person(culture, faith, name=exalt['name'], dynasty=people.dynasty(exalt['house'], culture),
                                 female=exalt.get('female', False), age=exalt['age'], cultivator=3,
                                 traits=exalt.get('traits', ()),
                                 effects=('add_trait = ac_immortal_core', 'ac_aura_floor_effect = { AP = 15000 }'))
            bookmark_ids[region] = king
            if region == STEWARD_REGION:
                # No Emperor has sat at Azuma Honsha for centuries: the High Steward holds the realm for the Council.
                # First in the file and earlier in time, so every 'liege = h_rasen' finds a holder.
                titles.insert(0, block('h_rasen', [f'{START[0] - 20}.1.1 = {{ holder = {king} government = {OUTER_GOVERNMENT} }}']))
                titles.append(block(kingdom, [f'{early} = {{ holder = {king} }}']))
            else:
                titles.append(block(kingdom, [f'{early} = {{ holder = {king} government = feudal_government liege = h_rasen }}']))
        for di, duchy in enumerate(duchies):
            counties = duchy['counties']
            culture = weighted(rng, peoples['cultures'])
            faith = weighted(rng, peoples['faiths'])
            canon = next((CANON_HOLDERS[c['key']] for c in counties if c['key'] in CANON_HOLDERS), None)
            if king and di == 0:
                duke = king
                culture, faith = EXALTS[region]['culture'], EXALTS[region]['faith']
            elif region == 'outer_north' and di == 0:
                g = DIVINE_GENERAL
                culture, faith = g['culture'], g['faith']
                duke = people.person(culture, faith, name=g['name'], dynasty=people.dynasty(g['house'], culture), age=g['age'],
                                     cultivator=3, traits=g['traits'] + ('rasen_divine_general',),
                                     effects=('add_trait = ac_immortal_core', 'ac_aura_floor_effect = { AP = 13000 }'))
            elif canon:
                duke = people.person(canon.get('culture', culture), canon.get('faith', faith), name=canon['name'],
                                     dynasty=people.dynasty(canon['house'], canon.get('culture', culture)),
                                     female=canon.get('female', False), age=canon['age'], cultivator=canon.get('cultivator', 2),
                                     traits=canon.get('traits', ()))
            else:
                rank = 2 if (king and rng.random() < 0.5) else (1 if rng.random() < 0.6 else 0)
                duke = people.person(culture, faith, cultivator=rank)
            general = region == 'outer_north' and di == 0
            # The Outer Lands have no kings: the Council appoints a Magistrate to each duchy and county.
            # (The Divine General answers to no one.)
            appointed = not king and not general
            mao = region == UNRULY_REGION and duke != king
            if appointed:
                liege = f' government = {OUTER_GOVERNMENT} liege = h_rasen'
            elif mao:
                liege = ' liege = h_rasen'
                MAO_TITLES['duchy'].append(duchy['key'])
            else:
                liege = f' liege = {kingdom}' if king and duke != king else ''
            titles.append(block(duchy['key'], [f'{early} = {{ holder = {duke}{liege} }}']))
            canon_county = next((c['key'] for c in counties if c['key'] in CANON_HOLDERS), counties[0]['key'])
            for county in counties:
                holder, county_liege = duke, ''
                if appointed and county['key'] != canon_county and county is not counties[0]:
                    holder = people.person(culture, faith, cultivator=1 if rng.random() < 0.4 else 0)
                    county_liege = f" government = {OUTER_GOVERNMENT} liege = {duchy['key']}"
                # In the largest Wild duchies a rival Mao has carved out the far counties.
                if mao and len(counties) >= 5 and county in counties[3:] and (
                        duchy['key'] in rivals or len(rivals) < RIVAL_MAOS):
                    if duchy['key'] not in rivals:
                        rivals[duchy['key']] = people.person(culture, faith, cultivator=2)
                    holder, county_liege = rivals[duchy['key']], ' liege = h_rasen'
                    MAO_TITLES['county'].append(county['key'])
                titles.append(block(county['key'], [f'{early} = {{ holder = {holder}{county_liege} }}']))
                for bi, (barony, province) in enumerate(county['baronies']):
                    holding = ['castle_holding', 'city_holding', 'church_holding'][bi] if bi < 3 else 'none'
                    # As in vanilla, only the county's capital province carries culture and rite.
                    people_lines = [f'culture = {culture}', f'rite = {faith}'] if bi == 0 else []
                    provinces.append(block(str(province), [*people_lines, f'holding = {holding}']))
    family_rng = random.Random(SEED + 1)
    for cid in sorted({h for h in re.findall(r'holder = (rasen_\d+)', '\n'.join(titles))}, key=lambda c: int(c.split('_')[1])):
        people.family(cid, family_rng)
    # Unlanded canon from the IF's chapter 9. Added last so the generated cast keeps its ids.
    for canon in CANON_CAST:
        effects = ['rasen_join_akuma_effect = yes'] if canon.get('akuma') else []
        dynasty = people.info[bookmark_ids[canon['child_of']]]['dynasty'] if canon.get('child_of') else \
            people.dynasty(canon['house'], canon['culture'])
        cid = people.person(canon['culture'], canon['faith'], name=canon['name'], dynasty=dynasty, female=canon['female'],
                            age=canon['age'], cultivator=canon.get('cultivator', 0), traits=canon.get('traits', ()), effects=effects)
        lines = people.info[cid]['lines']
        if canon.get('child_of'):
            parent = bookmark_ids[canon['child_of']]
            spouse = next((l.split(' = ')[-1].rstrip(' }') for l in people.info[parent]['lines'] if 'spouse = ' in l), None)
            father, mother = (spouse, parent) if people.info[parent]['female'] else (parent, spouse)
            lines[1:1] = [f'father = {father}'] + ([f'mother = {mother}'] if mother else [])
        if canon.get('court'):
            lines.append(f'{START[0] - 1}.1.1 = {{ employer = {bookmark_ids[canon["court"]]} }}')

    def ordered(lines):
        dated = sorted((l for l in lines if re.match(r'\d+\.\d+\.\d+ =', l)),
                       key=lambda l: tuple(int(x) for x in l.split(' ')[0].split('.')))
        return [l for l in lines if not re.match(r'\d+\.\d+\.\d+ =', l)] + dated
    chars = [block(cid, ordered(lines)) for cid, lines in people.characters]
    dynasties = []
    for key, (name, culture) in people.dynasties.items():
        dynasties.append(block(key, [f'name = "{key}"', f'culture = {culture}']))
        loc.append(f' {key}:0 "{name}"')
    return {
        'history/characters/rasen_characters.txt': '\n'.join(chars),
        'history/titles/rasen_titles.txt': '\n'.join(titles),
        'history/provinces/rasen_provinces.txt': '\n'.join(provinces),
        'common/dynasties/rasen_dynasties.txt': '\n'.join(dynasties),
    }, loc, bookmark_ids, people


def weighted(rng, table):
    total = sum(table.values())
    pick = rng.uniform(0, total)
    for key, weight in table.items():
        pick -= weight
        if pick <= 0:
            return key
    return key


def bookmark_files(bookmark_ids, people):
    date = '{}.{}.{}'.format(*START)
    characters = dict(people.characters)
    entries = []
    loc = ['l_english:', f' bm_group_rasen:0 "{BOOKMARK["group_name"]}"',
           f' bm_rasen_trials:0 "{BOOKMARK["name"]}"', f' bm_rasen_trials_desc:0 "{BOOKMARK["desc"]}"']
    for region, cid in bookmark_ids.items():
        lines = characters[cid]
        value = lambda k: next(l.split(' = ', 1)[1] for l in lines if l.startswith(k + ' = '))
        birth = next(l.split(' = ')[0] for l in lines if 'birth = yes' in l)
        female = any(l == 'female = yes' for l in lines)
        entries += ['character = {', f'\tname = "bm_rasen_{region}"', f'\tdynasty = {value("dynasty")}',
                    '\tdynasty_splendor_level = 1', f'\ttype = {"female" if female else "male"}', f'\tbirth = {birth}',
                    f'\ttitle = {"h_rasen" if region == STEWARD_REGION else "k_" + region}',
                    f'\tgovernment = {OUTER_GOVERNMENT if region == STEWARD_REGION else "feudal_government"}',
                    f'\tculture = {value("culture")}',
                    f'\treligion = {value("rite")}', '\tdifficulty = "BOOKMARK_CHARACTER_DIFFICULTY_EASY"',
                    f'\thistory_id = {cid}', '\tposition = { 900 500 }', '\tanimation = personality_bold', '}']
        loc += [f' bm_rasen_{region}:0 "{value("name").strip(chr(34))}"',
                f' bm_rasen_{region}_desc:0 "{EXALTS[region]["desc"]}"']
    bookmark = block('bm_rasen_trials', [f'start_date = {date}', 'is_playable = yes', 'group = bm_group_rasen',
                                         'weight = { value = 100 }', *entries])
    group = block('bm_group_rasen', [f'default_start_date = {date}'])
    defines = ('# Imperial Rasen begins three millennia after its founding.\n'
               f'NGame = {{\n\tSTART_DATE = "{date}"\n\tEND_DATE = "{START[0] + 300}.1.1"\n}}\n')
    limit = ['# Generated by tools/build_rasen_world.py. Natural aura by region.',
             'ac_mortal_limit_region_bonus = {', '\tvalue = 0']
    for i, (region, bonus) in enumerate(MORTAL_LIMIT_BONUS.items()):
        limit.append(f'\t{"if" if i == 0 else "else_if"} = {{ limit = {{ location ?= {{ geographical_region = {region} }} }} value = {bonus} }}')
    limit.append('}')
    race = ['# Generated by tools/build_rasen_world.py. Characters the game creates take their race from their culture.',
            'on_character_created = { on_actions = { rasen_assign_race } }',
            'on_game_start_after_lobby = { on_actions = { rasen_assign_races_at_start } }',
            'rasen_assign_race = { trigger = { NOT = { ac_has_race_trigger = yes } } effect = { rasen_assign_race_effect = yes } }',
            'rasen_assign_races_at_start = { effect = { every_living_character = { limit = { NOT = { ac_has_race_trigger = yes } } rasen_assign_race_effect = yes } } }']
    effect = ['# Generated by tools/build_rasen_world.py.', 'rasen_assign_race_effect = {']
    for i, (culture, kind) in enumerate(CULTURE_RACE.items()):
        if kind == 'yokai':
            body = 'random_list = { ' + ' '.join(f'1 = {{ add_trait = ac_race_{k} }}' for k in YOKAI_KINDS) + ' }'
        else:
            body = f'add_trait = ac_race_{kind}'
        effect.append(f'\t{"if" if i == 0 else "else_if"} = {{ limit = {{ culture = culture:{culture} }} {body} }}')
    effect += ['\telse = { add_trait = ac_race_human }', '}']
    return {
        'common/on_action/rasen_race_on_actions.txt': '\n'.join(race) + '\n',
        'common/scripted_effects/rasen_race_effects.txt': '\n'.join(effect) + '\n',
        'common/script_values/ac_mortal_limit_region_values.txt': '\n'.join(limit) + '\n',
        'common/bookmarks/bookmarks/rasen_bookmarks.txt': bookmark,
        'common/bookmarks/groups/rasen_bookmark_groups.txt': group,
        'common/defines/rasen_defines.txt': defines,
    }, loc


def sect_seats(kingdoms):
    """Resolve SECT_SEATS to {identity: (county, home title)}; the home is the county's duchy where free."""
    county_duchy = {c['key']: d['key'] for duchies in kingdoms.values() for d in duchies for c in d['counties']}
    seats, taken = {}, set()
    for identity, seat in SECT_SEATS.items():
        if seat.startswith('c_'):
            # Two story sects in one duchy (Thunderfall and Sunbringer): the second registers under its county.
            seats[identity] = (seat, seat if county_duchy[seat] in taken else county_duchy[seat])
            taken.add(county_duchy[seat])
    for kingdom, duchies in kingdoms.items():
        wanted = [i for i, seat in SECT_SEATS.items() if seat == kingdom]
        free = [d for d in duchies if d['key'] not in taken and d['counties']]
        # Spread the kingdom's sects evenly across its free duchies, in title order.
        for n, identity in enumerate(wanted):
            duchy = free[n * len(free) // len(wanted)]
            seats[identity] = (duchy['counties'][0]['key'], duchy['key'])
    if len({d for _, d in seats.values()}) != len(SECT_SEATS):
        raise SystemExit('Two sects share a home title')
    return {i: seats[i] for i in SECT_SEATS}


def sect_files(kingdoms):
    tier = ['# Generated by tools/build_rasen_world.py.',
            '# Province scope: a sect\'s standing follows the natural aura of its region.',
            'ac_sect_region_tier = {', '\tvalue = 1']
    for i, (region, value) in enumerate(SECT_STANDING.items()):
        tier.append(f'\t{"if" if i == 0 else "else_if"} = {{ limit = {{ geographical_region = {region} }} value = {value} }}')
    tier.append('}')
    world = ['# Generated by tools/build_rasen_world.py. The sects of Imperial Rasen keep their halls where the',
             '# story places them (ac_sect_seed_county_effect is in ac_sect_seeding_effects.txt).',
             'ac_sect_seed_world_effect = {']
    for identity, (county, home) in sect_seats(kingdoms).items():
        world.append(f'\ttitle:{home} = {{ set_variable = {{ name = ac_seed_identity value = flag:{identity} }} }}')
        world.append(f'\ttitle:{county} = {{ ac_sect_seed_county_effect = {{ HOME = title:{home} }} }}')
    world.append('}')
    return {'common/script_values/ac_sect_region_values.txt': '\n'.join(tier) + '\n',
            'common/scripted_effects/ac_sect_world_effects.txt': '\n'.join(world) + '\n'}


def rank_files():
    """What Imperial Rasen calls its rulers: Exalts, the High Steward and the Council's Magistrates."""
    exalted = ' '.join(f'k_{region}' for region in EXALTS if region != STEWARD_REGION)
    ranks = [('rasen_exalt', 'kingdom', f'titles = {{ {exalted} }}', 'Exalt'),
             ('rasen_high_steward', 'hegemony', 'titles = { h_rasen }', 'High Steward'),
             ('rasen_magistrate_duchy', 'duchy', f'governments = {{ {OUTER_GOVERNMENT} }}', 'Magistrate'),
             ('rasen_magistrate_county', 'county', f'governments = {{ {OUTER_GOVERNMENT} }}', 'Magistrate'),
             ('rasen_mao_duchy', 'duchy', 'titles = { ' + ' '.join(MAO_TITLES['duchy']) + ' }', 'Mao'),
             ('rasen_mao_county', 'county', 'titles = { ' + ' '.join(MAO_TITLES['county']) + ' }', 'Mao')]
    script, loc = ['# Generated by tools/build_rasen_world.py.'], ['l_english:']
    for key, tier, where, name in ranks:
        for gender in ('male', 'female'):
            script.append(f'{key}_{gender} = {{\n\ttype = character\n\tgender = {gender}\n\tspecial = holder\n\ttier = {tier}\n'
                          f'\tpriority = 600\n\t{where}\n\tflavourization_rules = {{ top_liege = no }}\n}}')
            loc.append(f' {key}_{gender}:0 "{name}"')
    return {'common/flavorization/rasen_title_holders.txt': '\n'.join(script) + '\n',
            'localization/english/rasen_ranks_l_english.yml': '\n'.join(loc) + '\n'}


def render():
    kingdoms = parse_titles()
    files = {}
    files.update({k: BOM + v for k, v in sect_files(kingdoms).items()})
    culture, culture_loc = culture_files()
    religion, religion_loc = religion_files(kingdoms)
    history, history_loc, bookmark_ids, people = history_files(kingdoms)
    files.update({k: BOM + v for k, v in rank_files().items()})
    bookmark, bookmark_loc = bookmark_files(bookmark_ids, people)
    for part in (culture, religion, history, bookmark):
        files.update({k: BOM + v for k, v in part.items()})
    files['localization/english/rasen_culture_l_english.yml'] = BOM + '\n'.join(culture_loc) + '\n'
    # Character names need a localization key each. Some also exist in vanilla, so these go in
    # replace/, which wins without duplicate-key errors.
    names = sorted({n for nl in NAME_LISTS.values() for n in nl['male'] + nl['female']} | {c['name'] for c in CANON_CAST} | {h['name'] for h in CANON_HOLDERS.values()})
    files['localization/replace/english/rasen_names_l_english.yml'] = BOM + 'l_english:\n' + ''.join(
        f' {re.sub(r"[^A-Za-z0-9_]", "_", n)}:0 "{n}"\n' for n in names)
    files['localization/english/rasen_religion_l_english.yml'] = BOM + '\n'.join(religion_loc) + '\n'
    files['localization/english/rasen_history_l_english.yml'] = BOM + '\n'.join(history_loc) + '\n'
    files['localization/english/rasen_bookmark_l_english.yml'] = BOM + '\n'.join(bookmark_loc) + '\n'
    return {k: v.encode('utf-8') for k, v in files.items()}, people


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files, people = render()
    if args.check:
        stale = [r for r, d in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale generated files: ' + ', '.join(stale))
    else:
        for relative, data in files.items():
            path = OUT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'{len(files)} files, {len(people.characters)} characters, {len(people.dynasties)} dynasties')


if __name__ == '__main__':
    main()
