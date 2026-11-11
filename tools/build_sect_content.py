"""Generate repetitive sect identities, estate buildings, and mission contracts.

The lifecycle, activities, decisions, and diplomacy are hand-authored alongside
these files. Run with --check to detect stale generated content.
"""
from pathlib import Path
import argparse
import re

from build_event_overrides import masked

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'AuraClash'

# Canonical Aura Clash sects (Style/Elements from the IF where it states them; see docs/sects.md).
IDENTITIES = [
    ('thunderfall', 'Thunderfall', 'storm', 'earth', 'midorikatai', 'tiger'),
    ('sunbringer', 'Sunbringer', 'light', 'fire', 'kiihakai', 'dragon'),
    ('mountain_hazard', 'Mountain Hazard', 'ice', 'earth', 'midorikatai', 'wolf'),
    ('dreamriver', 'Dreamriver', 'fire', 'water', 'kiihakai', 'monkey'),
    ('waverunner', 'Waverunner', 'water', 'ice', 'akakiru', 'stallion'),
    ('lost_siren', 'Lost Siren', 'water', 'ice', 'aoyusumu', 'crane'),
    ('endless_beating', 'Endless Beating', 'water', 'earth', 'midorikatai', 'ox'),
    ('windrising', 'Windrising', 'wind', 'water', 'aoyusumu', 'ram'),
    ('hidden_coil', 'Hidden Coil', 'darkness', 'water', 'kurokonton', 'snake'),
    # Named in the IF with little detail: Elements, Style and Foundation are inferred.
    ('choral_line', 'Choral Line', 'wind', 'light', 'aoyusumu', 'crane'),
    ('thousand_lantern', 'Thousand Lantern', 'fire', 'light', 'kiihakai', 'rat'),
    ('shielded_hull', 'Shielded Hull', 'earth', 'water', 'midorikatai', 'boar'),
    ('scarlet_sun', 'Scarlet Sun', 'fire', 'earth', 'akakiru', 'rabbit'),
    ('forbidden_field', 'Forbidden Field', 'darkness', 'earth', 'kurokonton', 'rat'),
    ('auroran_lights', 'Auroran Lights', 'light', 'ice', 'kiihakai', 'rabbit'),
    ('wandering_tear', 'Wandering Tear', 'water', 'wind', 'aoyusumu', 'stallion'),
    ('alluvial_fan', 'Alluvial Fan', 'earth', 'water', 'midorikatai', 'ox'),
    # Generated for the Inner Lands and the capital, where the IF names no sect.
    ('ten_thousand_blades', 'Ten Thousand Blades', 'wind', 'storm', 'akakiru', 'dragon'),
    ('veiled_moon', 'Veiled Moon', 'darkness', 'wind', 'kurokonton', 'snake'),
    ('saints_vigil', "Saint's Vigil", 'light', 'water', 'aoyusumu', 'crane'),
    ('endless_daylight', 'Endless Daylight', 'light', 'storm', 'kiihakai', 'dragon'),
    ('great_arena', 'Great Arena', 'earth', 'fire', 'midorikatai', 'tiger'),
    ('heavenly_ascension', 'Heavenly Ascension', 'light', 'fire', 'akakiru', 'dragon'),
]
# Trade Sects earn more for their treasury; the IF calls them "Trade Sects" and Endless Beating a "School".
TRADE_SECTS = ('choral_line', 'thousand_lantern', 'shielded_hull', 'scarlet_sun', 'forbidden_field')
NAME_FORMS = {key: '{} Trade Sect' for key in TRADE_SECTS} | {'endless_beating': '{} School'}
# A sect's standing follows the natural aura where its headquarters sits (ac_sect_region_tier).
STANDINGS = {1: 'Frontier Sect', 2: 'Established Sect', 3: 'Great Sect', 4: 'Imperial Sect'}


def sect_name(key, name):
    return NAME_FORMS.get(key, '{} Sect').format(name)
BUILDINGS = [
    ('cultivation_hall', 'Cultivation Hall', 'Quiet chambers for meditation and core advancement.', 'Annual cultivation lifestyle experience: 20 per level.'),
    ('alchemy_pavilion', 'Alchemy Pavilion', 'Furnaces, laboratories, and apprentices prepare cultivation medicines.', 'Unlocks medicinal pills in the sect exchange.'),
    ('training_ground', 'Martial Training Ground', 'Disciples drill footwork, weapon forms, and unarmed techniques.', 'Annual Power Core experience: 1 per level; strengthens sect battle formations.'),
    ('scripture_library', 'Scripture Library', 'The sect preserves manuals, examination records, and its martial lineage.', 'Annual cultivation lifestyle experience: 20 per level; unlocks manual study.'),
    ('spirit_garden', 'Spirit Garden', 'Cultivated medicinal herbs sustain the alchemy pavilion.', 'Annual Fortitude Core experience: 1 per level.'),
    ('formation_hall', 'Formation Hall', 'Disciples study how to combine their elements in coordinated battle.', 'Annual Agility Core experience: 1 per level; strengthens sect battle formations.'),
]
MISSIONS = [
    ('patrol', 'Patrol the Sect Roads', 'Escort merchants and drive brigands away from the headquarters.', 'prowess', 50),
    ('herbs', 'Gather Spiritual Herbs', 'Locate medicinal herbs and deliver a usable harvest to the alchemy pavilion.', 'learning', 50),
    ('manual', 'Recover a Lost Manual', 'Investigate a missing scripture and bring its teachings home.', 'intrigue', 70),
    ('mediation', 'Settle a Local Dispute', 'Resolve a feud among the households supporting the sect.', 'diplomacy', 40),
    ('relief', 'Aid the Local Villages', 'Organize supplies and cultivation healing for vulnerable villagers.', 'stewardship', 50),
    ('escort', 'Guard a Sect Delegation', 'Protect a delegation carrying tribute and correspondence.', 'martial', 70),
]


def format_script(text):
    depth = 0
    lines = []
    for line, clean in zip(text.splitlines(), masked(text).splitlines()):
        stripped = line.strip()
        leading = len(re.match(r'^\s*(}*)', clean)[1])
        lines.append('\t' * max(0, depth - leading) + stripped if stripped else '')
        depth += clean.count('{') - clean.count('}')
    if depth:
        raise ValueError('Unbalanced generated sect script')
    return '\n'.join(lines)


def render():
    files = {}
    # Story scope. A new sect takes a name no living sect uses; names repeat only once all are taken.
    effects = ['# Generated by tools/build_sect_content.py.\nac_sect_random_identity_effect = {\n\trandom_list = {']
    for key, *_ in IDENTITIES:
        effects.append(f'\t\t1 = {{ trigger = {{ NOT = {{ any_in_global_list = {{ variable = ac_sects var:ac_identity ?= flag:{key} }} }} }} '
                       f'set_variable = {{ name = ac_identity value = flag:{key} }} }}')
    effects += ['\t}', '\tif = {', '\t\tlimit = { NOT = { has_variable = ac_identity } }', '\t\trandom_list = {']
    for key, *_ in IDENTITIES:
        effects.append(f'\t\t\t1 = {{ set_variable = {{ name = ac_identity value = flag:{key} }} }}')
    effects += ['\t\t}', '\t}', '}', '',
                '# Story scope, once the name is known: Trade Sects are marked for their richer income.',
                'ac_sect_mark_kind_effect = {',
                '\tif = { limit = { OR = { ' + ' '.join(f'var:ac_identity = flag:{key}' for key in TRADE_SECTS)
                + ' } } set_variable = { name = ac_trade_sect value = 1 } }',
                '}', '', 'ac_sect_teach_identity_effect = {']
    for key, _, e1, e2, style, foundation in IDENTITIES:
        effects.append(f'''\tif = {{
        limit = {{ var:ac_sect.var:ac_identity = flag:{key} }}
        if = {{ limit = {{ ac_has_foundation_trigger = no }} add_trait = ac_foundation_{foundation} }}
        if = {{ limit = {{ ac_has_martial_style_trigger = no }} add_trait = ac_style_{style} }}
        if = {{ limit = {{ ac_has_element_trigger = no }} add_trait = ac_element_{e1} }}
    }}''')
    effects += ['}', '', 'ac_sect_teach_second_element_effect = {']
    for key, _, e1, e2, *_ in IDENTITIES:
        effects.append(f'''\tif = {{
        limit = {{ var:ac_sect.var:ac_identity = flag:{key} ac_element_count < 2 }}
        if = {{ limit = {{ NOT = {{ has_trait = ac_element_{e2} }} }} add_trait = ac_element_{e2} }}
        else = {{ add_trait = ac_element_{e1} }}
    }}''')
    effects += ['}', '', '''# A small opening remains in both ranks for players and subsequent recruitment.
ac_sect_seed_roster_effect = {
    var:ac_sect = { save_scope_as = ac_seeded_sect }
    while = {
        count = ac_sect_initial_upper
        ac_sect_seed_disciple_effect = { RANK = upper }
    }
    while = {
        count = ac_sect_initial_lower
        ac_sect_seed_disciple_effect = { RANK = lower }
    }
    var:ac_sect = { ac_sect_recount_effect = yes }
}
ac_sect_seed_disciple_effect = {
    create_character = {
        gender_female_chance = 50
        age = { 20 38 }
        culture = this.culture
        faith = this.faith
        location = scope:ac_seeded_sect.var:ac_headquarters
        random_traits = yes
        save_scope_as = ac_seeded_member
    }
    scope:ac_seeded_member = {
        set_variable = { name = ac_sect value = scope:ac_seeded_sect }
        set_variable = { name = ac_sect_contribution value = 0 }
        set_variable = { name = ac_sect_merit value = 0 }
        add_trait = ac_cultivator
        add_trait = ac_sect_$RANK$_disciple
        ac_sect_teach_identity_effect = yes
        if = {
            limit = { has_trait = ac_sect_upper_disciple }
            set_variable = { name = ac_sect_merit value = 150 }
            ac_sect_teach_second_element_effect = yes
            ac_sect_develop_rank_effect = yes
        }
    }
    scope:ac_seeded_sect = { add_to_variable_list = { name = ac_members target = scope:ac_seeded_member } }
}
''']
    files['common/scripted_effects/ac_sect_identity_effects.txt'] = '\n'.join(effects)
    loc = {'ac_sect_identity_unknown': 'Unrecorded lineage'}
    custom = ['AC_SectIdentity = { type = character']
    for key, name, e1, e2, style, foundation in IDENTITIES:
        loc[f'ac_sect_identity_{key}'] = f'{name}: {e1.title()} and {e2.title()}, $trait_ac_style_{style}$, {foundation.title()} Foundation'
        loc[f'ac_sect_name_{key}'] = sect_name(key, name)
        custom.append(f'text = {{ trigger = {{ var:ac_sect.var:ac_identity = flag:{key} }} localization_key = ac_sect_identity_{key} }}')
    custom += ['text = { localization_key = ac_sect_identity_unknown }', '}', 'AC_SectName = {', '\ttype = character']
    for key, *_ in IDENTITIES:
        custom.append(f'\ttext = {{ trigger = {{ var:ac_sect.var:ac_identity = flag:{key} }} localization_key = ac_sect_name_{key} }}')
    loc['ac_sect_name_unknown'] = 'Cultivation Sect'
    custom += ['\ttext = { localization_key = ac_sect_name_unknown }', '}', 'AC_SectStanding = {', '\ttype = character']
    for tier, name in STANDINGS.items():
        loc[f'ac_sect_standing_{tier}'] = name
        if tier != 2:
            custom.append(f'\ttext = {{ trigger = {{ var:ac_sect.var:ac_tier ?= {tier} }} localization_key = ac_sect_standing_{tier} }}')
    custom += ['\ttext = { localization_key = ac_sect_standing_2 }', '}', '''
AC_SectRank = {
    type = character
    text = { trigger = { has_trait = ac_sect_master } localization_key = trait_ac_sect_master }
    text = { trigger = { has_trait = ac_sect_upper_disciple } localization_key = trait_ac_sect_upper_disciple }
    text = { localization_key = trait_ac_sect_lower_disciple }
}
''']
    files['common/customizable_localization/ac_sect_custom_loc.txt'] = '\n'.join(custom)

    # Native domicile construction is the authority. Keep this timer handler
    # solely to finish projects already paid for in pre-domicile saves.
    estate = ['ac_sect_finish_construction_effect = { if = { limit = { has_variable = ac_building NOT = { has_variable = ac_building_timer } NOT = { has_variable = ac_native_construction } }']
    values = []
    for b, name, desc, benefit in BUILDINGS:
        values.append(f'ac_sect_{b}_cost = {{ value = var:ac_sect.var:ac_{b} add = 1 multiply = 100 }}')
        estate.append(f'if = {{ limit = {{ var:ac_building = flag:{b} }} change_variable = {{ name = ac_{b} add = 1 }} }}')
        loc[f'ac_sect_build_{b}'] = f'Improve the {name}'
        loc[f'ac_sect_build_{b}_tt'] = f'{desc} {benefit} Costs 100/200/300 sect gold. Base construction time: 180 days.'
    estate += ["""remove_variable = ac_building
        ac_sect_migrate_building_levels_effect = yes
        story_owner = { send_interface_toast = { type = event_toast_effect_good title = ac_sect_construction_complete left_icon = this } }
    } }
    ac_sect_training_effect = {
        ac_gain_cultivation_study_xp_effect = { XP = ac_sect_annual_study_xp }
        add_trait_xp = { trait = ac_cultivator track = ac_core_power value = var:ac_sect.var:ac_training_ground }
        add_trait_xp = { trait = ac_cultivator track = ac_core_fortitude value = var:ac_sect.var:ac_spirit_garden }
        add_trait_xp = { trait = ac_cultivator track = ac_core_agility value = var:ac_sect.var:ac_formation_hall }
    }
    """]
    values.append('ac_sect_annual_study_xp = { value = var:ac_sect.var:ac_cultivation_hall add = var:ac_sect.var:ac_scripture_library multiply = 20 }')
    files['common/scripted_effects/ac_sect_estate_effects.txt'] = '\n'.join(estate)
    files['common/script_values/ac_sect_estate_values.txt'] = '\n'.join(values)
    files['events/ac_sect_estate_events.txt'] = 'namespace = ac_sect_estate\nac_sect_estate.0001 = { type = character_event hidden = yes trigger = { ac_sect_member_trigger = yes } immediate = { ac_sect_open_estate_effect = yes } }\nac_sect_estate.0002 = { type = character_event hidden = yes trigger = { ac_sect_master_trigger = yes } immediate = { var:ac_sect = { ac_sect_ensure_domicile_effect = yes } } }\n'
    import build_sect_domiciles
    files.update(build_sect_domiciles.render(BUILDINGS))

    import build_sect_contracts
    files.update(build_sect_contracts.render(MISSIONS, loc))
    import build_cultivation_population
    files.update(build_cultivation_population.render(IDENTITIES))
    files['localization/english/ac_sect_generated_l_english.yml'] = 'l_english:\n' + '\n'.join(f' {key}:0 "{value}"' for key, value in loc.items()) + '\n'
    return {name: format_script(text) if name.endswith('.txt') else text for name, text in files.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for name, text in render().items():
        path = MOD / name
        data = ('\ufeff' + text.rstrip() + '\n').encode('utf-8')
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if stale:
        raise SystemExit('Stale sect content: ' + ', '.join(stale))
    print('Sect generated content is current.' if args.check else 'Generated sect identities, buildings, and contracts.')


if __name__ == '__main__':
    main()
