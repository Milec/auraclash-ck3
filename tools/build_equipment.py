"""Generate Aura Clash equipment: forged weapons and armour as CK3 artifacts, made in the Soul Forge.

Follows the IF's forge (ch6 "Craft a ... weapon"), its weapon list and the Core Rulebook:
- Weapons are the IF's own: Katana, Jian, Tanto, Kunai, Qiang, Greataxe, Kusarigama,
  Bo Staff, Meteor Hammer, Claws and Yumi, plus armour. Each is a real CK3 artifact in the
  weapon or armour inventory slot, drawn with vanilla's East Asian weapon models.
- Materials, as the forgemaster lists them: plain steel, Jade (100 Shards, Craft 2),
  Beastbone (80, Craft 3), Snowsteel (120, Craft 2) or Truegold (140, Craft 3). The author's
  lore says which Cores each material fuels: Jade Soul and Power, Beastbone Fortitude and
  Agility, Snowsteel Fortitude and Soul, Truegold Power and Agility. A fuelled Core fights
  at +1 rating in the Clash of Auras.
- Quality follows the IF's grades: plain, Improved, Superior and Mastercrafted.
- A Soul Treasure forged into the piece grants +1d6 to a skill (rulebook), here a CK3 skill;
  a superior-grade treasure (1,800 AP or more) also fuels the material's first Core again.
  Only one Soul Treasure goes into a piece.
- Armed (rulebook): a wielded weapon adds +1 to Clash rolls, unless the foe is Armored.
  A critical blow (a margin of 5 or more) breaks plain steel armour (durability -50).

The Soul Forge is a crafting board modelled on Princes of Darkness's workshop minigame:
the commissioner picks the piece, and the smith's Craft lays out a board of linked steps.
The forging starts on a "Shape" step and moves along the links, one step per move:
tempering, honing and folding the steel, a material, a Soul Treasure, and special steps
from the smith's perks and Elements. The smith's Stewardship (Craft) sets the board's size
and the moves; Learning gives rerolls of the board. The piece takes form as it is worked,
so its effects show before it is finished. Craft is Stewardship (Craft 2 = 10, Craft 3 = 15);
Shards are gold.

Usage: python tools/build_equipment.py [--check]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
BOM = '﻿'
CORES = ('power', 'fortitude', 'agility', 'soul')

# key: (IF name, CK3 visuals, bladed?) - "bladed" is the IF's Reaper list.
WEAPONS = {
    'katana': ('Katana', 'sword', True),
    'jian': ('Jian', 'sword', True),
    'tanto': ('Tanto', 'dagger', True),
    'kunai': ('Kunai', 'dagger', True),
    'qiang': ('Qiang', 'spear', True),
    'greataxe': ('Greataxe', 'axe', True),
    'kusarigama': ('Kusarigama', 'dagger', True),
    'bo_staff': ('Bo Staff', 'spear', False),
    'meteor_hammer': ('Meteor Hammer', 'hammer', False),
    'claws': ('Claws', 'dagger', False),
    'yumi': ('Yumi', 'bow', False),
}
ARMOR = {'armor': ('Armour', 'armor')}
KINDS = {**{k: v[0] for k, v in WEAPONS.items()}, **{k: v[0] for k, v in ARMOR.items()}}
VISUAL = {**{k: v[1] for k, v in WEAPONS.items()}, **{k: v[1] for k, v in ARMOR.items()}}
# key: (name, Shards, Craft rank, Cores fuelled)
MATERIALS = {
    'steel': ('Steel', 0, 0, ()),
    'jade': ('Jade', 100, 2, ('soul', 'power')),
    'beastbone': ('Beastbone', 80, 3, ('fortitude', 'agility')),
    'snowsteel': ('Snowsteel', 120, 2, ('fortitude', 'soul')),
    'truegold': ('Truegold', 140, 3, ('power', 'agility')),
}
CRAFT_STEWARDSHIP = {0: 0, 2: 10, 3: 15}
# tier: (prefix, minimum quality points, prowess, rarity)
TIERS = {'plain': ('', 0, 2, 'common'), 'improved': ('Improved ', 1, 3, 'masterwork'),
         'superior': ('Superior ', 3, 4, 'famed'), 'mastercrafted': ('Mastercrafted ', 5, 6, 'illustrious')}
# Soul Treasure skills: key -> (IF skill, CK3 modifier, amount)
SKILLS = {
    'athletics': ('Athletics', 'prowess', 4), 'insight': ('Insight', 'learning', 2),
    'persuasion': ('Persuasion', 'diplomacy', 2), 'deception': ('Deception', 'intrigue', 2),
    'craft': ('Craft', 'stewardship', 2), 'handseals': ('Handseals', 'monthly_lifestyle_xp_gain_mult', 0.06),
}
ELEMENTS = ('darkness', 'earth', 'fire', 'ice', 'light', 'storm', 'water', 'wind')
SUPERIOR_TREASURE_AP = 1800
STYLE_WEAPON = {'akakiru': 'katana', 'aoyusumu': 'bo_staff', 'kiihakai': 'jian', 'kurokonton': 'kunai',
                'midorikatai': 'claws'}

# The board (Princes of Darkness's workshop): width, height, node chance, link reach (squared).
BOARD_WIDTH, BOARD_HEIGHT, BOARD_PADDING, NODE_CHANCE, LINK_REACH = 700, 440, 30, 75, 52000
START_NODES = 3
FORGE_COOLDOWN_YEARS = 1

# Board steps. key: (label, description, gold, weight, kind filter (weapon/armor/None), extra requirement)
NODES = {
    'start': ('Shape', 'Shape the {kind}: the work begins here.', 0, 0, None, None),
    'temper': ('Temper', 'Temper the piece: +15 durability.', 5, 4, None, None),
    'hone': ('Hone', 'Hone the edge: +1 grade point.', 10, 4, 'weapon', None),
    'plates': ('Lace Plates', 'Lace the plates tighter: +1 grade point.', 10, 4, 'armor', None),
    'fold': ('Fold the Steel', 'Fold the steel again: +1 grade point, but -10 durability.', 5, 3, None, None),
    'balance': ('Balance', 'Balance the weapon in the hand: +1 prowess.', 5, 2, 'weapon', None),
    'decorate': ('Decorate', 'Inlay and engrave: a little prestige each month.', 15, 2, None, None),
    'reinforcement': ('Reinforcement Seal', 'The Reinforcement Seal hardens the piece: +40 durability.', 0, 3, None,
                      'scope:ac_forge_smith = { has_perk = ac_2_handseals_b_perk }'),
    'armory': ('Bladed Armory', 'The Bladed Lands\' armouries: +3% knight effectiveness.', 10, 3, 'weapon',
               'scope:ac_forge_smith = { has_perk = ac_3_style_akakiru_f_perk }'),
    'runes': ('Runic Inscription', 'Kiihakai runes: +1 Learning.', 10, 3, None,
              'scope:ac_forge_smith = { has_perk = ac_3_style_kiihakai_g_perk }'),
    'refine': ('Treasure Refining', 'An alchemist\'s refining: +1 grade point and +20 durability.', 10, 3, None,
               'scope:ac_forge_smith = { has_perk = ac_1_alchemy_f_perk }'),
}
for mat, (name, shards, craft, cores) in MATERIALS.items():
    if cores:
        req = f'scope:ac_forge_smith.stewardship >= {CRAFT_STEWARDSHIP[craft]}' if craft else None
        NODES[f'mat_{mat}'] = (name, f'Forge it of {name} ({shards} Shards): fuels the {cores[0].title()} and {cores[1].title()} Cores.',
                               shards, 2, None, req)
for skill, (name, _, _) in SKILLS.items():
    NODES[f'treasure_{skill}'] = (f'Soul Treasure: {name}', f'Forge in my strongest Soul Treasure: +1d6 {name}.', 0, 1, None,
                                  'scope:ac_forge_owner = { ac_holds_soul_treasure_trigger = yes }')
for element in ELEMENTS:
    NODES[f'infuse_{element}'] = (f'{element.title()} Infusion', f'Infuse the piece with {element.title()} chi: +2 prowess.', 10, 2, None,
                                  f'scope:ac_forge_smith = {{ has_trait = ac_element_{element} }}')


def name_key(kind, material, tier):
    return f'ac_eq_{kind}_{material}_{tier}'


def values():
    out = ['# Generated by tools/build_equipment.py. Character scope unless noted.']
    for core in CORES:
        out += ['# Cores fuelled by equipped materials and Soul Treasures (+1 rating each in the Clash of Auras).',
                f'ac_equipment_{core}_bonus = {{', '\tvalue = 0',
                f'\tevery_equipped_character_artifact = {{ limit = {{ has_variable = ac_core_{core} }} add = var:ac_core_{core} }}',
                '\tmax = 4', '}']
    for key, (_, shards, craft, _) in MATERIALS.items():
        out.append(f'ac_eq_{key}_shards = {shards}')
    out += ['# Smith-quality for the AI\'s direct forging (the player\'s pieces are graded on the board).',
            'ac_eq_quality_value = {', '\tvalue = scope:ac_smith.stewardship', '\tmultiply = 3', '\tadd = 10',
            '\tif = { limit = { scope:ac_smith = { has_trait = ac_cultivator } } add = 10 }',
            '\tmin = 5', '\tmax = 95', '}',
            'ac_eq_wealth_value = { value = ac_eq_quality_value add = 10 max = 100 }',
            f'ac_eq_superior_treasure_ap = {SUPERIOR_TREASURE_AP}',
            '# The Soul Forge board, from the smith (player scope, var:ac_forge_smith).',
            'ac_forge_board_size = { value = var:ac_forge_smith.stewardship divide = 8 floor = yes add = 3 max = 5 }',
            'ac_forge_moves_max = { value = var:ac_forge_smith.stewardship divide = 5 floor = yes add = 3 max = 8 }',
            'ac_forge_moves_left = { value = ac_forge_moves_max if = { limit = { has_variable = ac_forge_moves } subtract = var:ac_forge_moves } min = 0 }',
            'ac_forge_rerolls_max = { value = var:ac_forge_smith.learning divide = 10 floor = yes add = 1 max = 3 }',
            'ac_forge_rerolls_left = { value = ac_forge_rerolls_max if = { limit = { has_variable = ac_forge_rerolls } subtract = var:ac_forge_rerolls } min = 0 }',
            'ac_forge_base_durability = { value = var:ac_forge_smith.stewardship multiply = 2 add = 60 max = 120 }',
            '# Grade points on the piece being forged (artifact scope).',
            'ac_forge_quality_points = { value = 0 if = { limit = { has_variable = ac_forge_quality } value = var:ac_forge_quality } }',
            f'ac_forge_width = {BOARD_WIDTH}', f'ac_forge_height = {BOARD_HEIGHT}']
    return '\n'.join(out)


def triggers():
    out = ['# Generated by tools/build_equipment.py. Character scope.',
           '# Armed (rulebook): wielding a weapon.',
           'ac_is_armed_trigger = { any_equipped_character_artifact = { artifact_slot_type = primary_armament } }',
           '# Armored: wearing armour.',
           'ac_is_armored_trigger = { any_equipped_character_artifact = { artifact_slot_type = armor } }',
           '# A forged bladed weapon (the IF\'s Reaper list).',
           'ac_wields_blade_trigger = { any_equipped_character_artifact = { artifact_slot_type = primary_armament has_variable = ac_bladed } }',
           'ac_holds_soul_treasure_trigger = { OR = { has_variable = ac_soul_treasure_1 has_variable = ac_soul_treasure_2 has_variable = ac_soul_treasure_3 } }',
           'ac_can_be_smith_trigger = { is_adult = yes is_imprisoned = no NOT = { has_trait = incapable } }',
           '# Story scope (a board step), with scope:ac_forge_owner/smith/item saved: is the step allowed?',
           'ac_forge_node_requirement_trigger = {']
    for key, (_, _, gold, _, kind, req) in NODES.items():
        conds = []
        if gold:
            conds.append(f'custom_tooltip = {{ text = ac_forge_needs_gold_tt scope:ac_forge_owner.short_term_gold >= {gold} }}')
        if kind == 'weapon':
            conds.append('custom_tooltip = { text = ac_forge_weapon_only_tt NOT = { scope:ac_forge_owner.var:ac_forge_template = flag:armor } }')
        if kind == 'armor':
            conds.append('custom_tooltip = { text = ac_forge_armor_only_tt scope:ac_forge_owner.var:ac_forge_template = flag:armor }')
        if key.startswith('mat_'):
            conds.append('custom_tooltip = { text = ac_forge_one_material_tt scope:ac_forge_item = { NOT = { has_variable = ac_forged_material } } }')
        if key.startswith('treasure_'):
            conds.append('custom_tooltip = { text = ac_forge_one_treasure_tt scope:ac_forge_item = { NOT = { has_variable = ac_soul_treasure_ap } } }')
            conds.append('custom_tooltip = { text = ac_forge_needs_treasure_tt scope:ac_forge_owner = { ac_holds_soul_treasure_trigger = yes } }')
        if key.startswith('infuse_'):
            conds.append('custom_tooltip = { text = ac_forge_one_infusion_tt scope:ac_forge_item = { NOT = { has_variable = ac_infused } } }')
        if key in ('balance', 'decorate', 'armory', 'runes'):
            conds.append(f'custom_tooltip = {{ text = ac_forge_once_tt scope:ac_forge_item = {{ NOT = {{ has_variable = ac_forge_did_{key} }} }} }}')
        out.append(f'\ttrigger_if = {{ limit = {{ var:ac_forge_node = flag:{key} }} {" ".join(conds) if conds else "always = yes"} }}')
    out.append('}')
    return '\n'.join(out)


def modifiers():
    out = ['# Generated by tools/build_equipment.py.']
    for tier, (_, _, prowess, _) in TIERS.items():
        out.append(f'ac_eq_{tier}_modifier = {{ icon = prowess_positive prowess = {prowess} }}')
    for key, (_, stat, amount) in SKILLS.items():
        out.append(f'ac_eq_treasure_{key}_modifier = {{ icon = learning_positive {stat} = {amount} }}')
    out += ['ac_eq_armor_modifier = { icon = health_positive health = 0.25 }',
            'ac_forge_balance_modifier = { icon = prowess_positive prowess = 1 }',
            'ac_forge_runes_modifier = { icon = learning_positive learning = 1 }',
            'ac_forge_infused_modifier = { icon = prowess_positive prowess = 2 }']
    return '\n'.join(out)


def artifact_types():
    out = ['# Generated by tools/build_equipment.py. No required features: the forge sets the look.']
    for kind in WEAPONS:
        out.append(f'ac_{kind} = {{ slot = primary_armament }}')
    out.append('ac_armor = { slot = armor }')
    return '\n'.join(out)


def story_cycles():
    return '\n'.join([
        '# Generated by tools/build_equipment.py. The Soul Forge board, as Princes of Darkness\'s workshop:',
        '# a board story holding step and link stories.',
        'ac_story_forge_node = { }',
        'ac_story_forge_line = { }',
        'ac_story_forge_board = {',
        '\ton_end = {',
        '\t\tif = { limit = { has_variable_list = nodes } every_in_list = { variable = nodes end_story = yes } }',
        '\t\tif = { limit = { has_variable_list = lines } every_in_list = { variable = lines end_story = yes } }',
        '\t}',
        '\ton_owner_death = { end_story = yes }',
        '}',
    ])


def create_item(kind):
    """Character (owner) scope: the piece-in-progress for $kind$."""
    return (f'create_artifact = {{ name = ac_eq_unfinished_{kind} description = ac_eq_desc_unfinished type = ac_{kind} visuals = {VISUAL[kind]} '
            f'creator = scope:ac_forge_smith wealth = 20 quality = 20 modifier = artifact_placeholder_modifier save_scope_as = ac_forge_item }} '
            # An artifact must be created with a modifier; vanilla uses a placeholder and removes it.
            'scope:ac_forge_item = { remove_artifact_modifier = artifact_placeholder_modifier }')


def node_effect(key):
    """Story scope, scope:ac_forge_item/owner/smith: what a step does."""
    gold = NODES[key][2]
    pay = f'scope:ac_forge_owner = {{ remove_short_term_gold = {gold} }} ' if gold else ''
    item = 'scope:ac_forge_item'
    if key == 'start':
        return (f'{item} = {{ set_max_durability = {{ value = scope:ac_forge_owner.ac_forge_base_durability }} '
                'if = { limit = { var:ac_forged_kind = flag:armor } add_artifact_modifier = ac_eq_armor_modifier } }')
    if key == 'temper':
        return pay + f'{item} = {{ set_max_durability = {{ value = artifact_max_durability add = 15 }} }}'
    if key in ('hone', 'plates'):
        return pay + f'{item} = {{ ac_forge_add_quality_effect = yes }}'
    if key == 'fold':
        return pay + f'{item} = {{ ac_forge_add_quality_effect = yes set_max_durability = {{ value = artifact_max_durability add = -10 min = 10 }} }}'
    if key == 'balance':
        return pay + f'{item} = {{ add_artifact_modifier = ac_forge_balance_modifier set_variable = ac_forge_did_balance }}'
    if key == 'decorate':
        return pay + f'{item} = {{ add_artifact_modifier = artifact_monthly_minor_prestige_2_modifier set_variable = ac_forge_did_decorate }}'
    if key == 'reinforcement':
        return f'{item} = {{ set_max_durability = {{ value = artifact_max_durability add = 40 }} }}'
    if key == 'armory':
        return pay + f'{item} = {{ add_artifact_modifier = artifact_knight_effectiveness_3_modifier set_variable = ac_forge_did_armory }}'
    if key == 'runes':
        return pay + f'{item} = {{ add_artifact_modifier = ac_forge_runes_modifier set_variable = ac_forge_did_runes }}'
    if key == 'refine':
        return pay + f'{item} = {{ ac_forge_add_quality_effect = yes set_max_durability = {{ value = artifact_max_durability add = 20 }} }}'
    if key.startswith('mat_'):
        mat = key[4:]
        cores = MATERIALS[mat][3]
        sets = ' '.join(f'set_variable = {{ name = ac_core_{c} value = 1 }}' for c in cores)
        return pay + f'{item} = {{ set_variable = {{ name = ac_forged_material value = flag:{mat} }} {sets} set_artifact_description = ac_eq_desc_{mat} }}'
    if key.startswith('treasure_'):
        skill = key[9:]
        return (f'scope:ac_forge_owner = {{ ac_forge_take_treasure_effect = yes }} '
                f'{item} = {{ set_variable = {{ name = ac_soul_treasure_ap value = scope:ac_forge_treasure_ap }} '
                f'add_artifact_modifier = ac_eq_treasure_{skill}_modifier }}')
    if key.startswith('infuse_'):
        element = key[7:]
        return pay + f'{item} = {{ set_variable = {{ name = ac_infused value = flag:{element} }} add_artifact_modifier = ac_forge_infused_modifier }}'
    raise KeyError(key)


def effects():
    out = ['# Generated by tools/build_equipment.py.', '',
           '# Artifact scope: one more grade point.',
           'ac_forge_add_quality_effect = {',
           '\tif = { limit = { has_variable = ac_forge_quality } change_variable = { name = ac_forge_quality add = 1 } }',
           '\telse = { set_variable = { name = ac_forge_quality value = 1 } }',
           '}', '',
           '# Owner scope: take the strongest Soul Treasure for the forge (scope:ac_forge_treasure_ap).',
           'ac_forge_take_treasure_effect = {',
           '\tif = {',
           '\t\tlimit = { has_variable = ac_soul_treasure_1 ac_soul_treasure_1_value >= ac_soul_treasure_2_value ac_soul_treasure_1_value >= ac_soul_treasure_3_value }',
           '\t\tsave_scope_value_as = { name = ac_forge_treasure_ap value = var:ac_soul_treasure_1 } remove_variable = ac_soul_treasure_1',
           '\t}',
           '\telse_if = {',
           '\t\tlimit = { has_variable = ac_soul_treasure_2 ac_soul_treasure_2_value >= ac_soul_treasure_3_value }',
           '\t\tsave_scope_value_as = { name = ac_forge_treasure_ap value = var:ac_soul_treasure_2 } remove_variable = ac_soul_treasure_2',
           '\t}',
           '\telse_if = {',
           '\t\tlimit = { has_variable = ac_soul_treasure_3 }',
           '\t\tsave_scope_value_as = { name = ac_forge_treasure_ap value = var:ac_soul_treasure_3 } remove_variable = ac_soul_treasure_3',
           '\t}',
           '\telse = { save_scope_value_as = { name = ac_forge_treasure_ap value = 0 } }',
           '}', '',
           '# Player scope: save the forge\'s scopes for steps and triggers.',
           'ac_forge_save_scopes_effect = {',
           '\tsave_scope_as = ac_forge_owner',
           '\tvar:ac_forge_smith ?= { save_scope_as = ac_forge_smith }',
           '\tvar:ac_forge_item ?= { save_scope_as = ac_forge_item }',
           '}', '',
           '# Story scope (a step): choose what it does, from what the smith and owner can offer.',
           'ac_forge_pick_node_effect = {', '\trandom_list = {']
    for key, (_, _, gold, weight, kind, req) in NODES.items():
        if key == 'start':
            continue
        conds = []
        if kind == 'weapon':
            conds.append('NOT = { scope:ac_forge_owner.var:ac_forge_template = flag:armor }')
        if kind == 'armor':
            conds.append('scope:ac_forge_owner.var:ac_forge_template = flag:armor')
        if req:
            conds.append(req)
        trig = f'trigger = {{ {" ".join(conds)} }} ' if conds else ''
        out.append(f'\t\t{weight} = {{ {trig}set_variable = {{ name = ac_forge_node value = flag:{key} }} }}')
    out += ['\t}', '}', '',
            '# Player scope: lay out a fresh board and an unfinished piece of the chosen kind.',
            'ac_forge_create_board_effect = {',
            '\tac_forge_save_scopes_effect = yes',
            '\tcreate_story = { type = ac_story_forge_board save_scope_as = ac_forge_board }',
            '\tset_variable = { name = ac_forge_board value = scope:ac_forge_board }']
    for i, kind in enumerate(KINDS):
        out.append(f'\t{"if" if i == 0 else "else_if"} = {{ limit = {{ var:ac_forge_template = flag:{kind} }} {create_item(kind)} }}')
    out += ['\tscope:ac_forge_item = {',
            '\t\tset_variable = { name = ac_forged_kind value = scope:ac_forge_owner.var:ac_forge_template }',
            '\t\tset_variable = ac_forge_unfinished',
            '\t}',
            '\tset_variable = { name = ac_forge_item value = scope:ac_forge_item }',
            '\tsave_scope_value_as = { name = ac_forge_size value = ac_forge_board_size }',
            f'\tsave_scope_value_as = {{ name = ac_forge_cell_x value = {{ value = {BOARD_WIDTH} divide = scope:ac_forge_size }} }}',
            f'\tsave_scope_value_as = {{ name = ac_forge_cell_y value = {{ value = {BOARD_HEIGHT} divide = scope:ac_forge_size }} }}',
            '\tsave_scope_value_as = { name = ac_forge_row value = 0 }',
            '\twhile = {',
            '\t\tlimit = { scope:ac_forge_row < scope:ac_forge_size }',
            '\t\tsave_scope_value_as = { name = ac_forge_column value = 0 }',
            '\t\twhile = {',
            '\t\t\tlimit = { scope:ac_forge_column < scope:ac_forge_size }',
            '\t\t\trandom = {',
            f'\t\t\t\tchance = {NODE_CHANCE}',
            '\t\t\t\tcreate_story = { type = ac_story_forge_node save_scope_as = ac_forge_new_node }',
            '\t\t\t\tscope:ac_forge_new_node = {',
            f'\t\t\t\t\tset_variable = {{ name = coord_x value = {{ value = {{ 0 1 }} multiply = {{ value = scope:ac_forge_cell_x subtract = {2 * BOARD_PADDING} }} add = {BOARD_PADDING} add = {{ value = scope:ac_forge_cell_x multiply = scope:ac_forge_column }} }} }}',
            f'\t\t\t\t\tset_variable = {{ name = coord_y value = {{ value = {{ 0 1 }} multiply = {{ value = scope:ac_forge_cell_y subtract = {2 * BOARD_PADDING} }} add = {BOARD_PADDING} add = {{ value = scope:ac_forge_cell_y multiply = scope:ac_forge_row }} }} }}',
            '\t\t\t\t\tac_forge_pick_node_effect = yes',
            '\t\t\t\t}',
            '\t\t\t\tscope:ac_forge_board = { add_to_variable_list = { name = nodes target = scope:ac_forge_new_node } }',
            '\t\t\t}',
            '\t\t\tchange_variable_dummy = yes',
            '\t\t\tsave_scope_value_as = { name = ac_forge_column value = { value = scope:ac_forge_column add = 1 } }',
            '\t\t}',
            '\t\tsave_scope_value_as = { name = ac_forge_row value = { value = scope:ac_forge_row add = 1 } }',
            '\t}',
            f'\t# {START_NODES} steps become starting points, where the piece is shaped.',
            f'\tscope:ac_forge_board = {{ while = {{ count = {START_NODES} random_in_list = {{ variable = nodes limit = {{ NOT = {{ var:ac_forge_node = flag:start }} }} set_variable = {{ name = ac_forge_node value = flag:start }} }} }} }}',
            '\t# Link every pair of nearby steps.',
            '\tscope:ac_forge_board = {',
            '\t\tevery_in_list = {',
            '\t\t\tvariable = nodes',
            '\t\t\tsave_scope_as = ac_forge_a',
            '\t\t\tscope:ac_forge_board = {',
            '\t\t\t\tevery_in_list = {',
            '\t\t\t\t\tvariable = nodes',
            '\t\t\t\t\tlimit = { NOT = { this = scope:ac_forge_a } NOT = { ac_forge_linked_trigger = { A = this B = scope:ac_forge_a } } }',
            '\t\t\t\t\tsave_scope_as = ac_forge_b',
            '\t\t\t\t\t# Squared distance between the two steps.',
            '\t\t\t\t\tsave_scope_value_as = { name = ac_forge_d2 value = {',
            '\t\t\t\t\t\tadd = { value = scope:ac_forge_a.var:coord_x subtract = scope:ac_forge_b.var:coord_x multiply = { value = scope:ac_forge_a.var:coord_x subtract = scope:ac_forge_b.var:coord_x } }',
            '\t\t\t\t\t\tadd = { value = scope:ac_forge_a.var:coord_y subtract = scope:ac_forge_b.var:coord_y multiply = { value = scope:ac_forge_a.var:coord_y subtract = scope:ac_forge_b.var:coord_y } }',
            '\t\t\t\t\t} }',
            f'\t\t\t\t\tif = {{ limit = {{ scope:ac_forge_d2 <= {LINK_REACH} }}',
            '\t\t\t\t\tscope:ac_forge_owner = { create_story = { type = ac_story_forge_line save_scope_as = ac_forge_new_line } }',
            '\t\t\t\t\tscope:ac_forge_new_line = {',
            '\t\t\t\t\t\tset_variable = { name = start_node value = scope:ac_forge_a }',
            '\t\t\t\t\t\tset_variable = { name = end_node value = scope:ac_forge_b }',
            '\t\t\t\t\t\tset_variable = { name = opacity value = 0.25 }',
            '\t\t\t\t\t}',
            '\t\t\t\t\tscope:ac_forge_a = { add_to_variable_list = { name = lines target = scope:ac_forge_new_line } }',
            '\t\t\t\t\tscope:ac_forge_b = { add_to_variable_list = { name = lines target = scope:ac_forge_new_line } }',
            '\t\t\t\t\tscope:ac_forge_board = { add_to_variable_list = { name = lines target = scope:ac_forge_new_line } }',
            '\t\t\t\t\t}',
            '\t\t\t\t}',
            '\t\t\t}',
            '\t\t}',
            '\t}',
            '}', '',
            '# Player scope: throw away the board and the unfinished piece.',
            'ac_forge_clear_board_effect = {',
            '\tif = { limit = { exists = var:ac_forge_item } destroy_artifact = var:ac_forge_item }',
            '\tvar:ac_forge_board ?= { end_story = yes }',
            '\tremove_variable = ac_forge_board', '\tremove_variable = ac_forge_item', '\tremove_variable = ac_forge_current',
            '\tremove_variable = ac_forge_moves',
            '}', '',
            '# Player scope: close the Soul Forge, abandoning any unfinished piece.',
            'ac_forge_close_effect = {',
            '\tac_forge_clear_board_effect = yes',
            '\tremove_variable = ac_forge_rerolls', '\tremove_variable = ac_forge_template', '\tremove_variable = ac_forge_smith',
            '\tremove_variable = ac_forge_open',
            '}', '',
            '# Player scope, scope:story: work the step.',
            'ac_forge_step_effect = {',
            '\tac_forge_save_scopes_effect = yes',
            '\tif = {',
            '\t\tlimit = { exists = var:ac_forge_current }',
            '\t\tvar:ac_forge_current = { every_in_list = { variable = lines limit = { OR = { var:start_node = scope:story var:end_node = scope:story } } set_variable = { name = opacity value = 1 } } }',
            '\t\tif = { limit = { has_variable = ac_forge_moves } change_variable = { name = ac_forge_moves add = 1 } }',
            '\t\telse = { set_variable = { name = ac_forge_moves value = 1 } }',
            '\t}',
            '\tscope:story = { set_variable = ac_forge_used }',
            '\tset_variable = { name = ac_forge_current value = scope:story }']
    for i, key in enumerate(NODES):
        out.append(f'\t{"if" if i == 0 else "else_if"} = {{ limit = {{ scope:story.var:ac_forge_node = flag:{key} }} custom_tooltip = ac_forge_node_{key}_desc {node_effect(key)} }}')
    out += ['}', '',
            '# Player scope: finish the piece and hand it over.',
            'ac_forge_finish_effect = {',
            '\tac_forge_save_scopes_effect = yes',
            '\tscope:ac_forge_item = {',
            '\t\tremove_variable = ac_forge_unfinished',
            '\t\tif = { limit = { NOT = { has_variable = ac_forged_material } } set_variable = { name = ac_forged_material value = flag:steel } set_artifact_description = ac_eq_desc_steel }',
            '\t\tif = { limit = { ' + ' '.join(['OR = {'] + [f'var:ac_forged_kind = flag:{k}' for k, v in WEAPONS.items() if v[2]] + ['}']) + ' } set_variable = ac_bladed }',
            '\t\t# A superior-grade Soul Treasure fuels the material\'s first Core again.',
            '\t\tif = {', '\t\t\tlimit = { has_variable = ac_soul_treasure_ap var:ac_soul_treasure_ap >= ac_eq_superior_treasure_ap }']
    first = True
    for mat, (_, _, _, cores) in MATERIALS.items():
        if cores:
            out.append(f'\t\t\t{"if" if first else "else_if"} = {{ limit = {{ var:ac_forged_material = flag:{mat} }} change_variable = {{ name = ac_core_{cores[0]} add = 1 }} }}')
            first = False
    out += ['\t\t\telse = { set_variable = { name = ac_core_power value = 1 } }', '\t\t}']
    tiers = list(TIERS.items())[::-1]
    for i, (tier, (_, minimum, _, rarity)) in enumerate(tiers):
        out.append(f'\t\t{"if" if i == 0 else "else_if"} = {{ limit = {{ ac_forge_quality_points >= {minimum} }} add_artifact_modifier = ac_eq_{tier}_modifier '
                   f'set_variable = {{ name = ac_forged_tier value = flag:{tier} }} set_artifact_rarity = {rarity} }}')
    out += ['\t\tac_eq_name_artifact_effect = yes',
            '\t\tadd_durability = artifact_max_durability',
            '\t\tremove_variable = ac_forge_quality',
            '\t}',
            '\tscope:ac_forge_smith = { add_stewardship_lifestyle_xp = 100 }',
            f'\tset_variable = {{ name = ac_forge_cooldown value = yes years = {FORGE_COOLDOWN_YEARS} }}',
            '\tsave_scope_as = ac_eq_owner',
            '\tscope:ac_forge_item = { save_scope_as = ac_eq_new }',
            '\t# The finished piece is no longer the board\'s to destroy.',
            '\tremove_variable = ac_forge_item',
            '\tac_forge_close_effect = yes',
            '\ttrigger_event = ac_forge.0020',
            '}', '',
            '# Artifact scope: name it after its kind, material and grade.',
            'ac_eq_name_artifact_effect = {']
    first = True
    for kind in KINDS:
        for mat in MATERIALS:
            for tier in TIERS:
                out.append(f'\t{"if" if first else "else_if"} = {{ limit = {{ var:ac_forged_kind = flag:{kind} var:ac_forged_material = flag:{mat} var:ac_forged_tier = flag:{tier} }} set_artifact_name = {name_key(kind, mat, tier)} }}')
                first = False
    out += ['}', '',
            '# AI and seeding: forge at once for this character in $MATERIAL$, the kind following the Style.',
            'ac_ai_forge_effect = {',
            '\tsave_scope_as = ac_smith',
            '\tsave_scope_value_as = { name = ac_eq_quality value = ac_eq_quality_value }',
            '\tsave_scope_value_as = { name = ac_eq_wealth value = ac_eq_wealth_value }']
    for i, (style, kind) in enumerate(list(STYLE_WEAPON.items()) + [(None, 'qiang')]):
        limit = f'has_trait = ac_style_{style}' if style else 'always = yes'
        out.append(f'\t{"if" if i == 0 else "else_if"} = {{ limit = {{ {limit} }} '
                   f'create_artifact = {{ name = {name_key(kind, "steel", "plain")} description = ac_eq_desc_$MATERIAL$ type = ac_{kind} visuals = {VISUAL[kind]} '
                   f'creator = this wealth = scope:ac_eq_wealth quality = scope:ac_eq_quality modifier = artifact_placeholder_modifier save_scope_as = ac_eq_new }} '
                   f'scope:ac_eq_new = {{ remove_artifact_modifier = artifact_placeholder_modifier set_variable = {{ name = ac_forged_kind value = flag:{kind} }} }} }}')
    out += ['\tscope:ac_eq_new = {',
            '\t\tset_variable = { name = ac_forged_material value = flag:$MATERIAL$ }']
    first = True
    for mat, (_, _, _, cores) in MATERIALS.items():
        if cores:
            sets = ' '.join(f'set_variable = {{ name = ac_core_{c} value = 1 }}' for c in cores)
            out.append(f'\t\t{"if" if first else "else_if"} = {{ limit = {{ var:ac_forged_material = flag:{mat} }} {sets} }}')
            first = False
    out.append('\t\tif = { limit = { ' + ' '.join(['OR = {'] + [f'var:ac_forged_kind = flag:{k}' for k, v in WEAPONS.items() if v[2]] + ['}']) + ' } set_variable = ac_bladed }')
    for i, (tier, (_, minimum, _, rarity)) in enumerate(tiers):
        q = {'mastercrafted': 80, 'superior': 60, 'improved': 40, 'plain': 0}[tier]
        out.append(f'\t\t{"if" if i == 0 else "else_if"} = {{ limit = {{ scope:ac_eq_quality >= {q} }} add_artifact_modifier = ac_eq_{tier}_modifier set_variable = {{ name = ac_forged_tier value = flag:{tier} }} }}')
    out += ['\t\tac_eq_name_artifact_effect = yes', '\t}', '}', '',
            '# AI cultivators with spare gold forge a weapon in the material that fuels their strongest Cores.',
            'ac_ai_equipment_routine_effect = {',
            '\tif = {',
            '\t\tlimit = {',
            '\t\t\thas_trait = ac_cultivator', '\t\t\tis_adult = yes', '\t\t\tis_ai = yes',
            '\t\t\tNOT = { any_character_artifact = { has_variable = ac_forged_kind artifact_slot_type = primary_armament } }',
            '\t\t\tshort_term_gold >= 250',
            '\t\t}',
            '\t\trandom_list = {',
            '\t\t\t1 = { modifier = { add = ac_core_soul_rating } modifier = { add = ac_core_power_rating } remove_short_term_gold = ac_eq_jade_shards ac_ai_forge_effect = { MATERIAL = jade } }',
            '\t\t\t1 = { modifier = { add = ac_core_fortitude_rating } modifier = { add = ac_core_agility_rating } remove_short_term_gold = ac_eq_beastbone_shards ac_ai_forge_effect = { MATERIAL = beastbone } }',
            '\t\t\t1 = { modifier = { add = ac_core_fortitude_rating } modifier = { add = ac_core_soul_rating } remove_short_term_gold = ac_eq_snowsteel_shards ac_ai_forge_effect = { MATERIAL = snowsteel } }',
            '\t\t\t1 = { modifier = { add = ac_core_power_rating } modifier = { add = ac_core_agility_rating } remove_short_term_gold = ac_eq_truegold_shards ac_ai_forge_effect = { MATERIAL = truegold } }',
            '\t\t}',
            '\t}',
            '}', '',
            '# Duel: a critical blow on a foe in plain steel armour breaks it. Winner scope, foe in var:ac_duel_foe.',
            'ac_eq_critical_effect = {',
            '\tvar:ac_duel_foe = {',
            '\t\trandom_equipped_character_artifact = {',
            '\t\t\tlimit = { artifact_slot_type = armor NOT = { has_variable = ac_core_fortitude } NOT = { has_variable = ac_core_soul } NOT = { has_variable = ac_core_power } NOT = { has_variable = ac_core_agility } }',
            '\t\t\tadd_durability = -50',
            '\t\t}',
            '\t}',
            '}']
    # Drop the drafting placeholder.
    return '\n'.join(l for l in out if 'change_variable_dummy' not in l)


def link_helpers():
    return '\n'.join([
        '# Generated by tools/build_equipment.py. Story scopes $A$ and $B$ (board steps).',
        'ac_forge_linked_trigger = {',
        '\t$A$ = { has_variable_list = lines any_in_list = { variable = lines OR = { var:start_node = $B$ var:end_node = $B$ } } }',
        '}',
    ])


def reach_value():
    return '\n'.join([
        '# Generated by tools/build_equipment.py. Squared distance between two board steps.',
        'ac_forge_reach_value = {',
        '\tvalue = 0',
        '\tadd = { value = $A$.var:coord_x subtract = $B$.var:coord_x multiply = { value = $A$.var:coord_x subtract = $B$.var:coord_x } }',
        '\tadd = { value = $A$.var:coord_y subtract = $B$.var:coord_y multiply = { value = $A$.var:coord_y subtract = $B$.var:coord_y } }',
        '}',
    ])


def scripted_guis():
    root = ('save_temporary_scope_as = ac_forge_owner var:ac_forge_smith ?= { save_temporary_scope_as = ac_forge_smith } '
            'var:ac_forge_item ?= { save_temporary_scope_as = ac_forge_item }')
    return '\n'.join([
        '# Generated by tools/build_equipment.py. The Soul Forge window (player scope).',
        'ac_forge_close = { scope = character effect = { ac_forge_close_effect = yes } }',
        'ac_forge_choose = {',
        '\tscope = character',
        '\tsaved_scopes = { flag }',
        '\tis_shown = { var:ac_forge_template ?= scope:flag }',
        '\tis_valid = { NOT = { has_variable = ac_forge_board } }',
        # Each flag is set by name, so the engine knows every kind's flag is in use.
        '\teffect = {',
        *[f'\t\t{"if" if i == 0 else "else_if"} = {{ limit = {{ scope:flag = flag:{k} }} set_variable = {{ name = ac_forge_template value = flag:{k} }} }}'
          for i, k in enumerate(KINDS)],
        '\t}',
        '}',
        'ac_forge_prepare = {',
        '\tscope = character',
        '\tis_valid = {',
        '\t\tcustom_tooltip = { text = ac_forge_choose_first_tt has_variable = ac_forge_template }',
        '\t\tcustom_tooltip = { text = ac_forge_cooldown_tt NOT = { has_variable = ac_forge_cooldown } }',
        '\t\tNOT = { has_variable = ac_forge_board }',
        '\t}',
        '\teffect = { custom_tooltip = ac_forge_prepare_tt hidden_effect = { ac_forge_create_board_effect = yes } }',
        '}',
        'ac_forge_reroll = {',
        '\tscope = character',
        '\tis_valid = {',
        '\t\thas_variable = ac_forge_board',
        '\t\tcustom_tooltip = { text = ac_forge_no_rerolls_tt ac_forge_rerolls_left > 0 }',
        '\t\tcustom_tooltip = { text = ac_forge_reroll_started_tt NOT = { has_variable = ac_forge_current } }',
        '\t}',
        '\teffect = {',
        '\t\tcustom_tooltip = ac_forge_reroll_tt',
        '\t\thidden_effect = {',
        '\t\t\tac_forge_clear_board_effect = yes',
        '\t\t\tif = { limit = { has_variable = ac_forge_rerolls } change_variable = { name = ac_forge_rerolls add = 1 } }',
        '\t\t\telse = { set_variable = { name = ac_forge_rerolls value = 1 } }',
        '\t\t\tac_forge_create_board_effect = yes',
        '\t\t}',
        '\t}',
        '}',
        'ac_forge_node = {',
        '\tscope = character',
        '\tsaved_scopes = { story }',
        '\tis_shown = { var:ac_forge_current ?= scope:story }',
        '\tis_valid = {',
        f'\t\t{root}',
        '\t\tcustom_tooltip = { text = ac_forge_used_tt scope:story = { NOT = { has_variable = ac_forge_used } } }',
        '\t\ttrigger_if = {',
        '\t\t\tlimit = { NOT = { has_variable = ac_forge_current } }',
        '\t\t\tcustom_tooltip = { text = ac_forge_start_here_tt scope:story.var:ac_forge_node = flag:start }',
        '\t\t}',
        '\t\ttrigger_else = {',
        '\t\t\tcustom_tooltip = { text = ac_forge_not_start_tt NOT = { scope:story.var:ac_forge_node = flag:start } }',
        '\t\t\tcustom_tooltip = { text = ac_forge_too_far_tt ac_forge_linked_trigger = { A = var:ac_forge_current B = scope:story } }',
        '\t\t\tcustom_tooltip = { text = ac_forge_no_moves_tt ac_forge_moves_left > 0 }',
        '\t\t}',
        '\t\tscope:story = { ac_forge_node_requirement_trigger = yes }',
        '\t}',
        '\teffect = { ac_forge_step_effect = yes }',
        '}',
        'ac_forge_hover_enter = {',
        '\tscope = character',
        '\tsaved_scopes = { story }',
        '\teffect = { scope:story = { every_in_list = { variable = lines limit = { NOT = { var:opacity = 1 } } set_variable = { name = opacity value = 0.6 } } } }',
        '}',
        'ac_forge_hover_leave = {',
        '\tscope = character',
        '\tsaved_scopes = { story }',
        '\teffect = { scope:story = { every_in_list = { variable = lines limit = { NOT = { var:opacity = 1 } } set_variable = { name = opacity value = 0.25 } } } }',
        '}',
        'ac_forge_finish = {',
        '\tscope = character',
        '\tis_valid = { custom_tooltip = { text = ac_forge_unstarted_tt has_variable = ac_forge_current } }',
        '\teffect = { custom_tooltip = ac_forge_finish_tt hidden_effect = { ac_forge_finish_effect = yes } }',
        '}',
    ])


def gui():
    kinds = list(KINDS)
    rows = [kinds[:6], kinds[6:]]
    choose = lambda k: f"GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('flag', MakeScopeFlag('{k}')).End"
    out = ['# Generated by tools/build_equipment.py. The Soul Forge: a crafting board after Princes of Darkness\'s workshop.',
           'widget = {',
           '\tname = "ac_forge_window"',
           '\tlayer = windows_layer',
           '\tsize = { 100% 100% }',
           '\talwaystransparent = yes',
           '\tvisible = "[GetPlayer.IsValid]"',
           '\twindow = {',
           '\t\tname = "ac_forge_window_inner"',
           '\t\tlayer = windows_layer',
           '\t\tparentanchor = center',
           '\t\tsize = { 800 880 }',
           '\t\tusing = Window_Movable',
           '\t\tusing = Window_Background',
           '\t\tusing = Window_Decoration',
           "\t\tvisible = \"[GetPlayer.MakeScope.Var('ac_forge_open').IsSet]\"",
           '\t\tvbox = {',
           '\t\t\tusing = Window_Margins',
           '\t\t\tspacing = 8',
           '\t\t\theader_pattern = {',
           '\t\t\t\tlayoutpolicy_horizontal = expanding',
           '\t\t\t\tblockoverride "header_text" { text = "ac_forge_title" }',
           "\t\t\t\tblockoverride \"button_close\" { onclick = \"[GetScriptedGui('ac_forge_close').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)]\" }",
           '\t\t\t}',
           '\t\t\ttext_single = { text = "ac_forge_smith_line" }']
    for row in rows:
        out += ['\t\t\thbox = {', '\t\t\t\tspacing = 4']
        for k in row:
            out += ['\t\t\t\tbutton_standard = {', '\t\t\t\t\tsize = { 118 32 }',
                    f'\t\t\t\t\ttext = "ac_forge.kind_{k}"',
                    f"\t\t\t\t\tdown = \"[GetScriptedGui('ac_forge_choose').IsShown({choose(k)})]\"",
                    f"\t\t\t\t\tenabled = \"[GetScriptedGui('ac_forge_choose').IsValid({choose(k)})]\"",
                    f"\t\t\t\t\tonclick = \"[GetScriptedGui('ac_forge_choose').Execute({choose(k)})]\"",
                    '\t\t\t\t}']
        out.append('\t\t\t}')
    p = "GuiScope.SetRoot(GetPlayer.MakeScope).End"
    out += ['\t\t\tbutton_primary = {',
            "\t\t\t\tvisible = \"[Not(GetPlayer.MakeScope.Var('ac_forge_board').IsSet)]\"",
            '\t\t\t\tsize = { 300 40 }', '\t\t\t\ttext = "ac_forge_prepare_button"',
            f"\t\t\t\tenabled = \"[GetScriptedGui('ac_forge_prepare').IsValid({p})]\"",
            f"\t\t\t\ttooltip = \"[GetScriptedGui('ac_forge_prepare').BuildTooltip({p})]\"",
            f"\t\t\t\tonclick = \"[GetScriptedGui('ac_forge_prepare').Execute({p})]\"",
            '\t\t\t}',
            '\t\t\twidget = {',
            "\t\t\t\tvisible = \"[GetPlayer.MakeScope.Var('ac_forge_board').IsSet]\"",
            f'\t\t\t\tsize = {{ {BOARD_WIDTH} {BOARD_HEIGHT} }}',
            '\t\t\t\tbackground = {',
            '\t\t\t\t\ttexture = "gfx/interface/illustrations/event_scenes/armory_night.dds"',
            '\t\t\t\t\tfittype = centercrop',
            '\t\t\t\t\talpha = 0.6',
            '\t\t\t\t}',
            '\t\t\t\tbackground = { using = Background_Frame }',
            '\t\t\t\twidget = {',
            '\t\t\t\t\tsize = { 100% 100% }',
            '\t\t\t\t\talwaystransparent = yes',
            "\t\t\t\t\tdatamodel = \"[GetPlayer.MakeScope.Var('ac_forge_board').GetList('lines')]\"",
            '\t\t\t\t\titem = { ac_forge_line = {} }',
            '\t\t\t\t}',
            '\t\t\t\twidget = {',
            '\t\t\t\t\tsize = { 100% 100% }',
            '\t\t\t\t\talwaystransparent = yes',
            "\t\t\t\t\tdatamodel = \"[GetPlayer.MakeScope.Var('ac_forge_board').GetList('nodes')]\"",
            '\t\t\t\t\titem = { ac_forge_node = {} }',
            '\t\t\t\t}',
            '\t\t\t}',
            '\t\t\thbox = {',
            "\t\t\t\tvisible = \"[GetPlayer.MakeScope.Var('ac_forge_board').IsSet]\"",
            '\t\t\t\tspacing = 16',
            "\t\t\t\ttext_single = { text = \"ac_forge_moves_line\" }",
            "\t\t\t\ttext_single = { text = \"ac_forge_rerolls_line\" }",
            '\t\t\t\tbutton_standard = {',
            '\t\t\t\t\tsize = { 140 32 }', '\t\t\t\t\ttext = "ac_forge_reroll_button"',
            f"\t\t\t\t\tenabled = \"[GetScriptedGui('ac_forge_reroll').IsValid({p})]\"",
            f"\t\t\t\t\ttooltip = \"[GetScriptedGui('ac_forge_reroll').BuildTooltip({p})]\"",
            f"\t\t\t\t\tonclick = \"[GetScriptedGui('ac_forge_reroll').Execute({p})]\"",
            '\t\t\t\t}',
            '\t\t\t\tbutton_primary = {',
            '\t\t\t\t\tsize = { 180 36 }', '\t\t\t\t\ttext = "ac_forge_finish_button"',
            f"\t\t\t\t\tenabled = \"[GetScriptedGui('ac_forge_finish').IsValid({p})]\"",
            f"\t\t\t\t\ttooltip = \"[GetScriptedGui('ac_forge_finish').BuildTooltip({p})]\"",
            f"\t\t\t\t\tonclick = \"[GetScriptedGui('ac_forge_finish').Execute({p})]\"",
            '\t\t\t\t}',
            '\t\t\t}',
            '\t\t\tvbox = {',
            "\t\t\t\tvisible = \"[GetPlayer.MakeScope.Var('ac_forge_item').IsSet]\"",
            '\t\t\t\tlayoutpolicy_horizontal = expanding',
            '\t\t\t\tbackground = { using = Background_Area }',
            '\t\t\t\tmargin = { 10 6 }',
            '\t\t\t\ttext_single = { text = "ac_forge_piece_title" default_format = "#T" }',
            '\t\t\t\ttext_single = { text = "ac_forge_piece_status" }',
            '\t\t\t\ttext_multi = {',
            '\t\t\t\t\tautoresize = yes', '\t\t\t\t\tmax_width = 700',
            "\t\t\t\t\tdatacontext = \"[GetPlayer.MakeScope.Var('ac_forge_item').Artifact]\"",
            '\t\t\t\t\traw_text = "[Artifact.GetModifierEffects]"',
            '\t\t\t\t}',
            '\t\t\t}',
            '\t\t\texpand = {}',
            '\t\t}',
            '\t}',
            '}', '',
            'types AcForgeTypes',
            '{',
            '\ttype ac_forge_node = widget',
            '\t{',
            '\t\tallow_outside = yes',
            "\t\tstate = { name = _mouse_hierarchy_enter on_start = \"[GetScriptedGui('ac_forge_hover_enter').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('story', Scope.Story.MakeScope).End)]\" }",
            "\t\tstate = { name = _mouse_hierarchy_leave on_start = \"[GetScriptedGui('ac_forge_hover_leave').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('story', Scope.Story.MakeScope).End)]\" }",
            '\t\tbutton_standard = {',
            '\t\t\tsize = { 96 34 }',
            "\t\t\tposition = \"[Subtract_CVector2f( FloatToCVector2f( FixedPointToFloat(Scope.Var('coord_x').GetValue), FixedPointToFloat(Scope.Var('coord_y').GetValue) ), '(CVector2f)48,17' )]\"",
            "\t\t\ttext = \"[Localize(Concatenate('ac_forge_node_', Scope.Var('ac_forge_node').GetFlagKey))]\"",
            '\t\t\tdefault_format = "#high"',
            "\t\t\tdown = \"[GetScriptedGui('ac_forge_node').IsShown(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('story', Scope.Story.MakeScope).End)]\"",
            "\t\t\tenabled = \"[And(Not(Scope.Var('ac_forge_used').IsSet), GetScriptedGui('ac_forge_node').IsValid(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('story', Scope.Story.MakeScope).End))]\"",
            "\t\t\tonclick = \"[GetScriptedGui('ac_forge_node').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('story', Scope.Story.MakeScope).End)]\"",
            "\t\t\ttooltip = \"[GetScriptedGui('ac_forge_node').BuildTooltip(GuiScope.SetRoot(GetPlayer.MakeScope).AddScope('story', Scope.Story.MakeScope).End)]\"",
            '\t\t}',
            '\t}',
            '\ttype ac_forge_line = widget',
            '\t{',
            "\t\talpha = \"[Scope.Var('opacity').GetValue]\"",
            '\t\tsize = { 100% 100% }',
            '\t\tline = {',
            '\t\t\tusing = Line_Lifestyles_Unlocked',
            '\t\t\twidth = 5',
            "\t\t\tfrom = \"[FloatToCVector2f( FixedPointToFloat(Scope.Var('start_node').Var('coord_x').GetValue), FixedPointToFloat(Scope.Var('start_node').Var('coord_y').GetValue) )]\"",
            "\t\t\tto = \"[FloatToCVector2f( FixedPointToFloat(Scope.Var('end_node').Var('coord_x').GetValue), FixedPointToFloat(Scope.Var('end_node').Var('coord_y').GetValue) )]\"",
            '\t\t}',
            '\t}',
            '}']
    return '\n'.join(out)


def interactions():
    return '\n'.join([
        '# Generated by tools/build_equipment.py.',
        'ac_commission_forging_interaction = {',
        '\tcategory = interaction_category_friendly',
        '\tcommon_interaction = yes',
        '\ticon = icon_combat',
        '\tdesc = ac_commission_forging_interaction_desc',
        '\tauto_accept = yes',
        '\tis_shown = {',
        '\t\tscope:actor = { is_adult = yes is_ai = no }',
        '\t\tOR = {',
        '\t\t\tscope:recipient = scope:actor',
        '\t\t\tscope:recipient = { is_courtier_of = scope:actor }',
        '\t\t}',
        '\t}',
        '\tis_valid_showing_failures_only = {',
        '\t\tscope:actor = {',
        '\t\t\tis_imprisoned = no',
        '\t\t\tcustom_tooltip = { text = ac_forge_cooldown_tt NOT = { has_variable = ac_forge_cooldown } }',
        '\t\t\tcustom_tooltip = { text = ac_forge_busy_tt NOT = { has_variable = ac_forge_open } }',
        '\t\t}',
        '\t\tscope:recipient = { ac_can_be_smith_trigger = yes }',
        '\t}',
        '\ton_accept = {',
        '\t\tscope:actor = {',
        '\t\t\tcustom_tooltip = ac_commission_forging_open_tt',
        '\t\t\tset_variable = { name = ac_forge_smith value = scope:recipient }',
        '\t\t\tset_variable = ac_forge_open',
        '\t\t}',
        '\t}',
        '\tai_will_do = { base = 0 }',
        '}',
    ])


def events():
    return '\n'.join([
        '# Generated by tools/build_equipment.py.', 'namespace = ac_forge', '',
        '# 0020 the finished piece.',
        'ac_forge.0020 = {', '\ttype = character_event', '\ttitle = ac_forge.0020.t', '\tdesc = ac_forge.0020.desc',
        '\ttheme = martial', '\ttrigger = { is_ai = no }', '\tleft_portrait = { character = root animation = happiness }',
        '\tartifact = { target = scope:ac_eq_new position = lower_center_portrait }',
        '\toption = { name = ac_forge.0020.a }', '}'])


def on_actions():
    return '\n'.join([
        '# Generated by tools/build_equipment.py.',
        'random_yearly_everyone_pulse = { on_actions = { ac_equipment_ai_pulse } }',
        'ac_equipment_ai_pulse = {',
        '\ttrigger = { has_trait = ac_cultivator is_ai = yes }',
        '\teffect = { random = { chance = 20 ac_ai_equipment_routine_effect = yes } }',
        '}',
        '# The world\'s strongest cultivators start with forged weapons in their materials.',
        'on_game_start = { on_actions = { ac_equipment_seed } }',
        'ac_equipment_seed = {',
        '\teffect = {',
        '\t\tevery_living_character = {',
        '\t\t\t# Sect Masters and stronger (40+ Core dots); Aura Pressure is not yet counted at game start.',
        '\t\t\tlimit = { has_trait = ac_cultivator ac_core_dots >= 40 }',
        '\t\t\trandom_list = {',
        '\t\t\t\t1 = { ac_ai_forge_effect = { MATERIAL = jade } }',
        '\t\t\t\t1 = { ac_ai_forge_effect = { MATERIAL = beastbone } }',
        '\t\t\t\t1 = { ac_ai_forge_effect = { MATERIAL = snowsteel } }',
        '\t\t\t\t1 = { ac_ai_forge_effect = { MATERIAL = truegold } }',
        '\t\t\t}',
        '\t\t}',
        '\t}',
        '}',
    ])


def localization():
    out = ['l_english:',
           ' ac_commission_forging_interaction:0 "Commission Forged Equipment"',
           ' ac_commission_forging_interaction_desc:0 "Open the Soul Forge with [recipient.GetShortUIName] at the anvil, to forge a weapon or armour in steel or a precious material, perhaps around a Soul Treasure."',
           ' ac_commission_forging_open_tt:0 "Opens the Soul Forge."',
           ' ac_forge_title:0 "The Soul Forge"',
           " ac_forge_smith_line:0 \"Smith: [GetPlayer.MakeScope.Var('ac_forge_smith').Char.GetUIName]. Their [stewardship|E] (Craft) sets the board and the moves, their [learning|E] the rerolls. Choose the piece, then prepare the forge.\"",
           ' ac_forge_prepare_button:0 "Prepare the Forge"',
           ' ac_forge_prepare_tt:0 "The smith lays out the work: a board of linked steps. Begin on a #V Shape#! step, then follow the links, one step per move."',
           ' ac_forge_choose_first_tt:0 "Choose the piece to forge"',
           ' ac_forge_cooldown_tt:0 "The forge is still cooling from the last commission"',
           ' ac_forge_busy_tt:0 "The Soul Forge is already open"',
           ' ac_forge_reroll_button:0 "Rethink the Work"',
           ' ac_forge_reroll_tt:0 "Lay out a new board."',
           ' ac_forge_no_rerolls_tt:0 "No rerolls left"',
           ' ac_forge_reroll_started_tt:0 "The work has already begun"',
           ' ac_forge_finish_button:0 "Forge"',
           ' ac_forge_finish_tt:0 "Finish the piece as it stands. Its grade follows the grade points earned on the board."',
           ' ac_forge_unstarted_tt:0 "Shape the piece first"',
           " ac_forge_moves_line:0 \"Moves left: #V [GetPlayer.MakeScope.ScriptValue('ac_forge_moves_left')|0]#!\"",
           " ac_forge_rerolls_line:0 \"Rerolls: #V [GetPlayer.MakeScope.ScriptValue('ac_forge_rerolls_left')|0]#!\"",
           ' ac_forge_piece_title:0 "The piece so far"',
           " ac_forge_piece_status:0 \"Grade points: #V [GetPlayer.MakeScope.Var('ac_forge_item').Artifact.MakeScope.ScriptValue('ac_forge_quality_points')|0]#! (Improved 1, Superior 3, Mastercrafted 5)\"",
           ' ac_forge_used_tt:0 "This step is done"',
           ' ac_forge_start_here_tt:0 "Begin on a Shape step"',
           ' ac_forge_not_start_tt:0 "A Shape step only begins the work"',
           ' ac_forge_too_far_tt:0 "Not linked to the current step"',
           ' ac_forge_no_moves_tt:0 "No moves left"',
           ' ac_forge_needs_gold_tt:0 "Not enough Shards"',
           ' ac_forge_weapon_only_tt:0 "Weapons only"',
           ' ac_forge_armor_only_tt:0 "Armour only"',
           ' ac_forge_one_material_tt:0 "The piece already has its material"',
           ' ac_forge_one_treasure_tt:0 "Only one Soul Treasure goes into a piece"',
           ' ac_forge_needs_treasure_tt:0 "I hold no Soul Treasure"',
           ' ac_forge_one_infusion_tt:0 "The piece is already infused"',
           ' ac_forge_once_tt:0 "Already done to this piece"',
           ' ac_eq_desc_unfinished:0 "Unfinished work at the Soul Forge."',
           ' ac_forge.0020.t:0 "Fresh from the Forge"',
           ' ac_forge.0020.desc:0 "The smith presents the finished piece: [ac_eq_new.GetName]."',
           ' ac_forge.0020.a:0 "It feels right in my hands."']
    for kind, name in KINDS.items():
        out.append(f' ac_forge.kind_{kind}:0 "{name}"')
        out.append(f' artifact_ac_{kind}:0 "{name.lower()}"')
        out.append(f' ac_eq_unfinished_{kind}:0 "Unfinished {name}"')
    for key, (label, desc, gold, _w, _k, _r) in NODES.items():
        cost = f' Costs {gold} Shards.' if gold and not key.startswith('mat_') else ''
        out.append(f' ac_forge_node_{key}:0 "{label}"')
        out.append(f' ac_forge_node_{key}_desc:0 "{desc.format(kind="piece")}{cost}"')
    for mat, (name, shards, craft, cores) in MATERIALS.items():
        desc = (f'Forged of {name}, which fuels its wielder\'s #V {cores[0].title()}#! and #V {cores[1].title()}#! Cores (+1 rating each in a Clash of Auras).'
                if cores else 'Forged of plain steel and wood. In a Clash of Auras a weapon lends the Armed bonus; plain armour can break under a critical blow.')
        out.append(f' ac_eq_desc_{mat}:0 "{desc}"')
    for kind, name in KINDS.items():
        for mat, (mname, _, _, _) in MATERIALS.items():
            for tier, (prefix, _, _, _) in TIERS.items():
                material = '' if mat == 'steel' else f'{mname} '
                out.append(f' {name_key(kind, mat, tier)}:0 "{prefix}{material}{name}"')
    return '\n'.join(out)


def render():
    texts = {
        'common/script_values/ac_equipment_values.txt': values(),
        'common/scripted_triggers/ac_equipment_triggers.txt': triggers() + '\n' + link_helpers(),
        'common/modifiers/ac_equipment_modifiers.txt': modifiers(),
        'common/artifacts/types/ac_equipment_types.txt': artifact_types(),
        'common/story_cycles/ac_forge_story_cycles.txt': story_cycles(),
        'common/scripted_effects/ac_equipment_effects.txt': effects(),
        'common/scripted_guis/ac_forge_guis.txt': scripted_guis(),
        'common/character_interactions/ac_equipment_interactions.txt': interactions(),
        'common/on_action/ac_equipment_on_actions.txt': on_actions(),
        'events/ac_forge_events.txt': events(),
        'gui/ac_forge_window.gui': gui(),
        'gui/scripted_widgets/ac_forge_widgets.txt': 'gui/ac_forge_window.gui = ac_forge_window',
        'localization/english/ac_equipment_l_english.yml': localization(),
    }
    return {k: (BOM + v.rstrip('\n') + '\n').encode('utf-8') for k, v in texts.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = render()
    stale_inspiration = OUT / 'common/inspirations/ac_equipment_inspirations.txt'
    if args.check:
        stale = [r for r, d in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != d]
        if stale or stale_inspiration.exists():
            raise SystemExit('Stale generated files: ' + ', '.join(stale + ([str(stale_inspiration)] if stale_inspiration.exists() else [])))
    else:
        if stale_inspiration.exists():
            stale_inspiration.unlink()
        for relative, data in files.items():
            path = OUT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'Equipment: {len(files)} files, {len(KINDS)} kinds, {len(MATERIALS)} materials, {len(NODES)} forge steps.')


if __name__ == '__main__':
    main()
