"""Generate Aura Clash Techniques for CK3: catalogue, Focus slots, Chi Pool and Surge values.

Follows the IF's own technique system (menu-cultivation-techs, <<learntech>>, <<focuscore>>):
- Techniques are typed by Core (Power, Fortitude, Agility, Soul) or Innate; up to 25 are known.
- Each Core has one Focus slot. A focused Technique grants its focus effect: +1 Surge value
  to its Core, +1 to the Core's rating, or +1 Chi Pool.
- Learning grants the passive effect (Aura Pressure, Chi Pool, Health Pool or a skill).
- Innate Techniques (Thunderfall, Iron Body, Flash Step, Energy Tide) raise Surge values.
IF skills map to CK3: Athletics -> prowess, Insight/Lore -> learning, Deception/Thievery/Stealth
-> intrigue, Persuasion -> diplomacy, Craft -> stewardship, Survival -> epidemic resistance,
Perception -> scheme detection, Handseals/Alchemy/Seals -> lifestyle experience.
Usage: python tools/build_techniques.py [--check]
"""
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'AuraClash'
CORES = ('power', 'fortitude', 'agility', 'soul')
MAX_KNOWN = 25
SKILL = {
    'athletics': ('prowess', 2, 'Athletics'), 'insight': ('learning', 1, 'Insight'),
    'deception': ('intrigue', 1, 'Deception'), 'thievery': ('intrigue', 1, 'Thievery'),
    'stealth': ('intrigue', 1, 'Stealth'), 'persuasion': ('diplomacy', 1, 'Persuasion'),
    'craft': ('stewardship', 1, 'Craft'), 'survival': ('epidemic_resistance', 5, 'Survival'),
    'perception': ('enemy_hostile_scheme_success_chance_add', -5, 'Perception'),
    'handseals': ('monthly_lifestyle_xp_gain_mult', 0.03, 'Handseals'),
    'alchemy': ('monthly_lifestyle_xp_gain_mult', 0.03, 'Alchemy'),
    'seals': ('monthly_lifestyle_xp_gain_mult', 0.03, 'Seals'),
}
STYLE = lambda s: f'has_trait = ac_style_{s}'
ELEMENT = lambda e: f'has_trait = ac_element_{e}'

# key: (name, core, focus, passive, requirement, IF description)
# focus: surge | core | chi; passive: ('ap', n) | ('chi', 1) | ('health', 1) | ('battle_ap', 5) | (skill, 1)
CATALOGUE = {
    'cleave': ('Cleave', 'power', 'surge', ('athletics', 1), None, 'Melee Physical Attack.'),
    'hidden_dragon': ('Hidden Dragon', 'power', 'surge', ('chi', 1), None, 'Hidden power coils within the spirit.'),
    'spiritwell': ('Spiritwell', 'power', 'surge', ('ap', 10), None, 'A well of spiritual power.'),
    'palm_of_endless_beating': ('Palm of Endless Beating', 'power', 'surge', ('battle_ap', 5), None, 'The relentless palm of the Endless Beating School.'),
    'wrathful_fist': ('Wrathful Fist', 'power', 'surge', ('seals', 1), 'ac_has_martial_style_trigger = yes', 'Energy Melee Attack that deepens your Style.'),
    'inferno': ('Inferno', 'power', 'surge', ('ap', 15), ELEMENT('fire'), 'Area Energy Attack.'),
    'shockblast': ('Shockblast', 'power', 'surge', ('ap', 15), ELEMENT('storm'), 'Melee Energy Attack.'),
    'apex_hunter': ('Apex Hunter', 'power', 'core', ('perception', 1), STYLE('midorikatai'), 'The instincts of the strongest beast.'),
    'arctic_pillar': ('Arctic Pillar', 'power', 'core', None, ELEMENT('ice'), 'Ranged Physical Attack.'),
    'sacred_armor': ('Sacred Armor', 'fortitude', 'surge', ('health', 1), None, 'Chi woven into protective armor.'),
    'chi_hardened_skin': ('Chi-Hardened Skin', 'fortitude', 'surge', ('health', 1), None, 'Skin hardened by circulating chi.'),
    'frostguard': ('Frostguard', 'fortitude', 'surge', ('ap', 15), ELEMENT('ice'), 'A guard of living frost.'),
    'sandshield': ('Sandshield', 'fortitude', 'surge', ('ap', 15), ELEMENT('earth'), 'A shield of hardened sand.'),
    'blade_barrier': ('Blade Barrier', 'fortitude', 'surge', ('craft', 1), STYLE('akakiru'), 'Area Physical Attack.'),
    'sacred_breathing': ('Sacred Breathing', 'fortitude', 'surge', ('persuasion', 1), None, 'Breathing forms of the temples.'),
    'crouching_tiger': ('Crouching Tiger', 'fortitude', 'surge', ('stealth', 1), None, 'A coiled, hidden stance.'),
    'seismic_closing_palms': ('Seismic Closing Palms', 'fortitude', 'core', None, ELEMENT('earth'), 'Ranged Physical Attack.'),
    'danger_sense': ('Danger Sense', 'agility', 'surge', ('insight', 1), None, 'Sense the attack before it comes.'),
    'iaijutsu': ('Iaijutsu', 'agility', 'surge', ('thievery', 1), STYLE('akakiru'), 'The lightning draw of the blade.'),
    'bloodhunt': ('Bloodhunt', 'agility', 'surge', ('survival', 1), None, 'Track prey by the scent of its blood.'),
    'wavewalking': ('Wavewalking', 'agility', 'surge', ('ap', 15), ELEMENT('water'), 'Run across water as if it were stone.'),
    'grand_skyfall': ('Grand Skyfall', 'agility', 'surge', ('ap', 15), ELEMENT('wind'), 'Ranged Physical Attack.'),
    'imbued_bodyhammer': ('Imbued Bodyhammer', 'agility', 'surge', ('athletics', 1), None, 'Melee Physical-Energy Attack.'),
    'mist_clone': ('Mist Clone', 'agility', 'core', None, STYLE('kurokonton'), 'Create temporary Clones of mist.'),
    'apex_predator': ('Apex Predator', 'agility', 'core', ('stealth', 1), None, 'Move as the predator moves.'),
    'zen_focus': ('Zen Focus', 'soul', 'surge', ('deception', 1), None, 'A mind like still water.'),
    'commanding_presence': ('Commanding Presence', 'soul', 'surge', ('persuasion', 1), None, 'An aura that bends wills.'),
    'prayer_talisman': ('Prayer Talisman', 'soul', 'surge', ('seals', 1), STYLE('aoyusumu'), 'Talismans of the exorcist-monks.'),
    'poisonmaster': ('Poisonmaster', 'soul', 'surge', ('alchemy', 1), None, 'Mastery of venom and remedy.'),
    'combat_seals': ('Combat Seals', 'soul', 'surge', ('handseals', 1), STYLE('kiihakai'), 'Handseals cast in the heat of battle.'),
    'midnight_blade': ('Midnight Blade', 'soul', 'surge', ('ap', 15), ELEMENT('darkness'), 'Melee Energy-Physical Attack.'),
    'searing_light': ('Searing Light', 'soul', 'surge', ('ap', 15), ELEMENT('light'), 'Ranged Energy Attack.'),
    'tenebrous_rift': ('Tenebrous Rift', 'soul', 'core', None, ELEMENT('darkness'), 'Melee Energy Attack.'),
    'fox_charm': ('Fox Charm', 'soul', 'surge', ('deception', 1), 'has_trait = ac_race_kitsune', 'Kitsune Technique. Charms and illusions of the fox.'),
    'daggerfalling_hailstorm': ('Daggerfalling Hailstorm', 'soul', 'core', ('insight', 1), None, 'Ranged Energy Attack.'),
}
# Innate: granted when a Core reaches rating 5 through training; +1 Surge value.
INNATE = {'thunderfall': ('Thunderfall', 'power'), 'iron_body': ('Iron Body', 'fortitude'),
          'flash_step': ('Flash Step', 'agility'), 'energy_tide': ('Energy Tide', 'soul')}
INNATE_RATING = 5
FOCUS_TEXT = {'surge': 'Increases {Core} Surge by +1 when focused.', 'core': 'Increases {Core} Core by +1 when focused.',
              'chi': 'Increases Chi Pool by +1 when focused.'}


def passive_text(passive):
    if not passive:
        return ''
    kind, amount = passive
    if kind == 'ap':
        return f'Passively increases Aura Pressure by +{amount}. '
    if kind == 'chi':
        return 'Passively increases Chi Pool by +1. '
    if kind == 'health':
        return 'Passively increases Health Pool by +1. '
    if kind == 'battle_ap':
        return f'Passively increases Aura Pressure gained from battle by +{amount}. '
    return f'Passively increases {SKILL[kind][2]} by +1. '


def outputs():
    out = {}
    # Modifiers: passive (learned) and focused.
    mods = ['# Generated by tools/build_techniques.py.']
    for key, (name, core, focus, passive, req, desc) in CATALOGUE.items():
        if passive and passive[0] in SKILL:
            stat, value, _ = SKILL[passive[0]]
            mods.append(f'ac_tech_{key}_modifier = {{ icon = learning_positive {stat} = {value} }}')
        elif passive and passive[0] == 'health':
            mods.append(f'ac_tech_{key}_modifier = {{ icon = health_positive health = 0.2 }}')
        if focus == 'core':
            linked = {'power': 'martial', 'fortitude': 'stewardship', 'agility': 'intrigue', 'soul': 'learning'}[core]
            mods.append(f'ac_tech_{key}_focus_modifier = {{ icon = martial_positive {linked} = 1 }}')
    out['common/modifiers/ac_combat_technique_modifiers.txt'] = '\n'.join(mods) + '\n'

    # Values: known count, Chi Pool, Surge values, focused Core bonuses, battle AP.
    vals = ['# Generated by tools/build_techniques.py.', f'ac_max_known_techniques = {MAX_KNOWN}',
            'ac_known_technique_count = {', '\tvalue = 0']
    vals += [f'\tif = {{ limit = {{ has_character_flag = ac_tech_{k} }} add = 1 }}' for k in CATALOGUE]
    vals += ['}', '# Chi Pool: 1 + half the Soul Core rating, plus Techniques (Soul Cores give +0.5 chi).',
             'ac_chi_pool = {', '\tvalue = ac_core_soul_rating', '\tdivide = 2', '\tfloor = yes', '\tadd = 1']
    vals += [f'\tif = {{ limit = {{ has_character_flag = ac_tech_{k} }} add = 1 }}' for k, v in CATALOGUE.items() if v[3] and v[3][0] == 'chi']
    vals += [f'\tif = {{ limit = {{ var:ac_focus_{v[1]} ?= flag:{k} }} add = 1 }}' for k, v in CATALOGUE.items() if v[2] == 'chi']
    vals += ['}', 'ac_chi_available = { value = ac_chi_pool if = { limit = { has_variable = ac_chi_spent } subtract = var:ac_chi_spent } min = 0 }']
    for core in CORES:
        vals += [f'ac_core_{core}_surge_value = {{', '\tvalue = 2']
        vals += [f'\tif = {{ limit = {{ var:ac_focus_{core} ?= flag:{k} }} add = 1 }}' for k, v in CATALOGUE.items() if v[1] == core and v[2] == 'surge']
        vals += [f'\tif = {{ limit = {{ has_character_flag = ac_tech_{k} }} add = 1 }}' for k, v in INNATE.items() if v[1] == core]
        vals += ['}', f'ac_core_{core}_focus_bonus = {{', '\tvalue = 0']
        vals += [f'\tif = {{ limit = {{ var:ac_focus_{core} ?= flag:{k} }} add = 1 }}' for k, v in CATALOGUE.items() if v[1] == core and v[2] == 'core']
        vals.append('}')
    vals += ['ac_battle_ap_bonus = {', '\tvalue = 0']
    vals += [f'\tif = {{ limit = {{ has_character_flag = ac_tech_{k} }} add = {v[3][1]} }}' for k, v in CATALOGUE.items() if v[3] and v[3][0] == 'battle_ap']
    vals += ['}', '# Imperial Rasen: while the Exalted Council opens the Imperial Archives, Path Manuals cost half.',
             'ac_path_manual_gold = { value = 100 if = { limit = { has_global_variable = rasen_archives_open } value = 50 } }', 'ac_sect_library_contribution = 50']
    out['common/script_values/ac_combat_technique_values.txt'] = '\n'.join(vals) + '\n'

    # Triggers.
    trig = ['# Generated by tools/build_techniques.py.']
    for key, (name, core, focus, passive, req, desc) in CATALOGUE.items():
        trig += [f'ac_can_learn_tech_{key}_trigger = {{', f'\tNOT = {{ has_character_flag = ac_tech_{key} }}']
        if req:
            trig.append(f'\t{req}')
        trig.append('}')
    trig += ['ac_can_learn_any_technique_trigger = {', '\thas_trait = ac_cultivator', '\tage >= 16',
             '\tcustom_tooltip = {', '\t\ttext = ac_tech_known_limit_tt', '\t\tac_known_technique_count < ac_max_known_techniques', '\t}',
             '\tcustom_tooltip = {', '\t\ttext = ac_tech_none_available_tt', '\t\tOR = {']
    trig += [f'\t\t\tac_can_learn_tech_{k}_trigger = yes' for k in CATALOGUE]
    trig += ['\t\t}', '\t}', '}']
    out['common/scripted_triggers/ac_combat_technique_triggers.txt'] = '\n'.join(trig) + '\n'

    # Effects.
    eff = ['# Generated by tools/build_techniques.py.']
    for key, (name, core, focus, passive, req, desc) in CATALOGUE.items():
        body = [f'ac_learn_tech_{key}_effect = {{', '\tif = {', f'\t\tlimit = {{ NOT = {{ has_character_flag = ac_tech_{key} }} }}',
                f'\t\tadd_character_flag = ac_tech_{key}',
                f'\t\tsend_interface_toast = {{ type = event_toast_effect_good title = ac_tech_{key} left_icon = this custom_tooltip = ac_tech_{key}_desc }}']
        if passive and (passive[0] in SKILL or passive[0] == 'health'):
            body.append(f'\t\tadd_character_modifier = ac_tech_{key}_modifier')
        if passive and passive[0] == 'ap':
            body += ['\t\tac_init_aura_effect = yes', f'\t\tchange_variable = {{ name = ac_aura_pressure add = {passive[1]} }}']
        body += ['\t}', '}']
        eff += body
    for core in CORES:
        techs = [k for k, v in CATALOGUE.items() if v[1] == core]
        body = [f'ac_unfocus_{core}_effect = {{']
        for k in techs:
            if CATALOGUE[k][2] == 'core':
                body.append(f'\tif = {{ limit = {{ var:ac_focus_{core} ?= flag:{k} }} remove_character_modifier = ac_tech_{k}_focus_modifier }}')
        body += [f'\tremove_variable = ac_focus_{core}', '}']
        eff += body
    for key, (name, core, focus, passive, req, desc) in CATALOGUE.items():
        body = [f'ac_focus_tech_{key}_effect = {{', f'\tac_unfocus_{core}_effect = yes', f'\tset_variable = {{ name = ac_focus_{core} value = flag:{key} }}']
        if focus == 'core':
            body.append(f'\tadd_character_modifier = ac_tech_{key}_focus_modifier')
        body.append('}')
        eff += body
    # Random study, weighted toward Techniques of the strongest Core.
    eff += ['# Learn one Technique you can learn, at random (Path Manuals, sect libraries, AI).',
            'ac_learn_random_technique_effect = {', '\trandom_list = {']
    for key, (name, core, focus, passive, req, desc) in CATALOGUE.items():
        eff.append(f'\t\t10 = {{ trigger = {{ ac_can_learn_tech_{key}_trigger = yes }} '
                   f'modifier = {{ add = 10 {"" if req is None else ""}ac_core_{core}_rating >= 4 }} '
                   f'modifier = {{ add = 20 {req or "always = no"} }} ac_learn_tech_{key}_effect = yes }}')
    eff += ['\t}', '}']
    # Innate techniques.
    eff += ['# Innate Techniques awaken when a Core reaches rating 5 (Thunderfall, Iron Body, Flash Step, Energy Tide).',
            'ac_grant_innate_techniques_effect = {']
    for key, (name, core) in INNATE.items():
        eff += ['\tif = {', f'\t\tlimit = {{ has_trait = ac_cultivator NOT = {{ has_character_flag = ac_tech_{key} }} ac_core_{core}_rating >= {INNATE_RATING} }}',
                f'\t\tadd_character_flag = ac_tech_{key}',
                '\t\tif = {', '\t\t\tlimit = { is_ai = no }',
                f'\t\t\tsend_interface_toast = {{ type = event_toast_effect_good title = ac_tech_{key} left_icon = this custom_tooltip = ac_tech_{key}_desc }}',
                '\t\t}', '\t}']
    eff.append('}')
    # AI focus: fill empty slots with any known Technique of that Core.
    eff += ['ac_ai_focus_techniques_effect = {']
    for core in CORES:
        techs = [k for k, v in CATALOGUE.items() if v[1] == core]
        eff += ['\tif = {', f'\t\tlimit = {{ NOT = {{ has_variable = ac_focus_{core} }} }}']
        for i, k in enumerate(techs):
            eff.append(f'\t\t{"if" if i == 0 else "else_if"} = {{ limit = {{ has_character_flag = ac_tech_{k} }} ac_focus_tech_{k}_effect = yes }}')
        eff.append('\t}')
    eff.append('}')
    out['common/scripted_effects/ac_combat_technique_effects.txt'] = '\n'.join(eff) + '\n'

    # Events: the IF's "Meditate upon your Techniques" menu.
    ev = ['namespace = ac_tech', '', '# 0001 Focused Techniques and the Technique list', '# 0011-0014 focus a Technique into a Core', '',
          'ac_tech.0001 = {', '\ttype = character_event', '\ttitle = ac_tech.0001.t', '\tdesc = {', '\t\tdesc = ac_tech.0001.desc']
    for core in CORES:
        ev += ['\t\tfirst_valid = {']
        for k, v in CATALOGUE.items():
            if v[1] == core:
                ev.append(f'\t\t\ttriggered_desc = {{ trigger = {{ var:ac_focus_{core} ?= flag:{k} }} desc = ac_tech.0001.focused_{core}_{k} }}')
        ev += [f'\t\t\tdesc = ac_tech.0001.unfocused_{core}', '\t\t}']
    ev += ['\t\tdesc = ac_tech.0001.list']
    for k in list(CATALOGUE) + list(INNATE):
        ev.append(f'\t\ttriggered_desc = {{ trigger = {{ has_character_flag = ac_tech_{k} }} desc = ac_tech.0001.known_{k} }}')
    ev += ['\t}', '\ttheme = learning', '\tleft_portrait = { character = root animation = personality_rational }', '']
    for i, core in enumerate(CORES, 1):
        ev += ['\toption = {', f'\t\tname = ac_tech.0001.{core}',
               '\t\ttrigger = { OR = { ' + ' '.join(f'has_character_flag = ac_tech_{k}' for k, v in CATALOGUE.items() if v[1] == core) + ' } }',
               f'\t\ttrigger_event = ac_tech.001{i}', '\t}']
    ev += ['\toption = { name = ac_tech.0001.leave }', '}', '']
    for i, core in enumerate(CORES, 1):
        ev += [f'ac_tech.001{i} = {{', '\ttype = character_event', f'\ttitle = ac_tech.001{i}.t', f'\tdesc = ac_tech.001{i}.desc',
               '\ttheme = learning', '\tleft_portrait = { character = root animation = personality_rational }', '']
        for k, v in CATALOGUE.items():
            if v[1] != core:
                continue
            ev += ['\toption = {', f'\t\tname = ac_tech.focus_{k}',
                   f'\t\ttrigger = {{ has_character_flag = ac_tech_{k} NOT = {{ var:ac_focus_{core} ?= flag:{k} }} }}',
                   f'\t\tcustom_tooltip = ac_tech_{k}_focus_tt', f'\t\tac_focus_tech_{k}_effect = yes',
                   '\t\thidden_effect = { trigger_event = ac_tech.0001 }', '\t}']
        ev += ['\toption = { name = ac_tech.back trigger_event = ac_tech.0001 }', '}', '']
    out['events/ac_combat_technique_events.txt'] = '\n'.join(ev) + '\n'

    # Decisions: meditate (menu), study a Path Manual (gold), study the sect library.
    out['common/decisions/ac_combat_technique_decisions.txt'] = '''# Generated by tools/build_techniques.py.
ac_meditate_techniques_decision = {
	decision_group_type = ac_cultivation
	picture = { reference = "gfx/interface/illustrations/decisions/decision_personal_religious.dds" }
	desc = ac_meditate_techniques_decision_desc
	selection_tooltip = ac_meditate_techniques_decision_tooltip
	confirm_text = ac_meditate_techniques_decision_confirm
	ai_check_interval = 0
	is_shown = { has_trait = ac_cultivator age >= 16 }
	effect = { trigger_event = ac_tech.0001 }
	ai_potential = { always = no }
	ai_will_do = { base = 0 }
}

ac_study_path_manual_decision = {
	decision_group_type = ac_cultivation
	picture = { reference = "gfx/interface/illustrations/decisions/decision_legend.dds" }
	desc = ac_study_path_manual_decision_desc
	selection_tooltip = ac_study_path_manual_decision_tooltip
	confirm_text = ac_study_path_manual_decision_confirm
	ai_check_interval = 0
	cooldown = { years = 1 }
	is_shown = { has_trait = ac_cultivator age >= 16 }
	is_valid = { ac_can_learn_any_technique_trigger = yes }
	cost = { gold = ac_path_manual_gold }
	effect = { custom_tooltip = ac_study_path_manual_effect_tt hidden_effect = { ac_learn_random_technique_effect = yes } }
	ai_potential = { always = no }
	ai_will_do = { base = 0 }
}

ac_study_sect_library_decision = {
	decision_group_type = ac_cultivation
	picture = { reference = "gfx/interface/illustrations/decisions/decision_legend.dds" }
	desc = ac_study_sect_library_decision_desc
	selection_tooltip = ac_study_sect_library_decision_tooltip
	confirm_text = ac_study_sect_library_decision_confirm
	ai_check_interval = 0
	cooldown = { years = 1 }
	is_shown = { has_trait = ac_cultivator ac_sect_member_trigger = yes }
	is_valid = {
		ac_can_learn_any_technique_trigger = yes
		custom_tooltip = { text = ac_sect_library_contribution_tt var:ac_sect_contribution >= ac_sect_library_contribution }
	}
	effect = {
		change_variable = { name = ac_sect_contribution add = { value = ac_sect_library_contribution multiply = -1 } }
		custom_tooltip = ac_study_path_manual_effect_tt
		hidden_effect = { ac_learn_random_technique_effect = yes }
	}
	ai_potential = { always = no }
	ai_will_do = { base = 0 }
}
'''

    # Localization.
    loc = ['l_english:']
    cap = lambda c: c.capitalize()
    for key, (name, core, focus, passive, req, desc) in CATALOGUE.items():
        text = f'{cap(core)} Technique. {desc} {passive_text(passive)}{FOCUS_TEXT[focus].format(Core=cap(core))}'
        loc += [f' ac_tech_{key}:0 "{name}"', f' ac_tech_{key}_desc:0 "{text}"',
                f' ac_tech_{key}_focus_tt:0 "Focus {name} to your {cap(core)} Core. {FOCUS_TEXT[focus].format(Core=cap(core))}"',
                f' ac_tech.focus_{key}:0 "Focus {name} ({FOCUS_TEXT[focus].format(Core=cap(core)).replace(" when focused", "").rstrip(".")})"',
                f' ac_tech.0001.focused_{core}_{key}:0 "\\n#V {cap(core)} Core:#! {name}"',
                f' ac_tech.0001.known_{key}:0 "\\n• #V {name}#! — {text}"']
        if passive and passive[0] in SKILL:
            loc.append(f' ac_tech_{key}_modifier:0 "{name}"')
        elif passive and passive[0] == 'health':
            loc.append(f' ac_tech_{key}_modifier:0 "{name}"')
        if focus == 'core':
            loc.append(f' ac_tech_{key}_focus_modifier:0 "{name} (Focused)"')
    for key, (name, core) in INNATE.items():
        text = f'Innate Technique. Passively increases {cap(core)} Surge by +1.'
        loc += [f' ac_tech_{key}:0 "{name}"', f' ac_tech_{key}_desc:0 "{text}"', f' ac_tech.0001.known_{key}:0 "\\n• #V {name}#! — {text}"']
    for i, core in enumerate(CORES, 1):
        loc += [f' ac_tech.0001.unfocused_{core}:0 "\\n#V {cap(core)} Core:#! (none)"',
                f' ac_tech.0001.{core}:0 "Focus a {cap(core)} Technique"',
                f' ac_tech.001{i}.t:0 "Focus a {cap(core)} Technique"',
                f' ac_tech.001{i}.desc:0 "Only one Technique can be focused to your {cap(core)} Core at a time. Focusing a new one replaces the old."']
    S = lambda v: f"[ROOT.Char.MakeScope.ScriptValue('{v}')|0]"
    loc += [
        ' ac_tech.0001.t:0 "Focused Techniques"',
        f' ac_tech.0001.desc:0 "In a neverending pursuit of Advancement, I meditate upon my Techniques. Certain Techniques must be Focused to a Core to gain their full benefits.\\n\\nChi Pool: #V {S("ac_chi_available")}#! of #V {S("ac_chi_pool")}#!. Surge values: Power #V {S("ac_core_power_surge_value")}#!, Fortitude #V {S("ac_core_fortitude_surge_value")}#!, Agility #V {S("ac_core_agility_surge_value")}#!, Soul #V {S("ac_core_soul_surge_value")}#!.\\n"',
        f' ac_tech.0001.list:0 "\\n\\n#T Technique List#! ({S("ac_known_technique_count")} of 25 known)"',
        ' ac_tech.0001.leave:0 "My power grows"',
        ' ac_tech.back:0 "Go back"',
        ' ac_tech_known_limit_tt:0 "You know fewer than 25 Techniques"',
        ' ac_tech_none_available_tt:0 "There is a Technique you can still learn (some require a Style or Element)"',
        ' ac_meditate_techniques_decision:0 "Meditate upon your Techniques"',
        ' ac_meditate_techniques_decision_desc:0 "Review the Techniques you know and choose which to Focus to each of your four Combat Cores."',
        ' ac_meditate_techniques_decision_tooltip:0 "Open your Focused Techniques and Technique List."',
        ' ac_meditate_techniques_decision_confirm:0 "Meditate"',
        ' ac_study_path_manual_decision:0 "Study a Path Manual"',
        ' ac_study_path_manual_decision_desc:0 "Path Manuals record the Techniques of masters for those who can pay. Some only make sense to followers of a particular Style or Element."',
        ' ac_study_path_manual_decision_tooltip:0 "Spend #V 100#! [gold|E] to learn a random Technique you can learn, favouring your strongest Cores, Style and Elements. Once per year; up to 25 Techniques."',
        ' ac_study_path_manual_decision_confirm:0 "Buy the manual"',
        ' ac_study_path_manual_effect_tt:0 "Learn a new #V Technique#!, gaining its passive effect. Focus it to a Core through #V Meditate upon your Techniques#!."',
        ' ac_study_sect_library_decision:0 "Study the Sect Library"',
        ' ac_study_sect_library_decision_desc:0 "Every Sect keeps manuals of the Techniques its masters have taught. Contribution to the Sect earns access."',
        ' ac_study_sect_library_decision_tooltip:0 "Spend #V 50#! sect contribution to learn a random Technique. Once per year."',
        ' ac_study_sect_library_decision_confirm:0 "Enter the library"',
        ' ac_sect_library_contribution_tt:0 "You have at least #V 50#! sect contribution"',
    ]
    out['localization/english/ac_combat_technique_l_english.yml'] = '\n'.join(loc) + '\n'
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for relative, text in outputs().items():
        path = MOD / relative
        data = ('﻿' + text).encode('utf-8')
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                stale.append(relative)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if stale:
        raise SystemExit('Stale technique files: ' + ', '.join(stale))
    print(f'{len(CATALOGUE)} Techniques and {len(INNATE)} Innate Techniques ' + ('verified.' if args.check else 'generated.'))


if __name__ == '__main__':
    main()
