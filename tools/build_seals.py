"""Generate Aura Clash Seals: the Core Rulebook's out-of-combat rituals, cast as character interactions.

Rulebook, chapter 7, "Seals": twelve zodiac handsigns, cast with chi infused into the hands.
- Every Seal needs a Handseals rank and/or Aura Pressure invested in a Style or Element.
  Here: Handseals +1d6/+2d6/+3d6 = 2/5/8 Handseals perks; "300/500-600/700/900 AP in a
  Style's Techniques" = that Style with 0/3/5/7 of its perks.
- The listed AP cost is Flipped (spent) at the end of the casting; it may be paid in Shards
  at a tenth. Here: 1 Chi per 100 AP, or AP/10 gold ("Pay in Shards").
- The Handseals roll decides the strength: 2 dice plus 1 per Handseals rank, each a success on
  5-6, sixes exploding. Durations "per success" become months (or years) per success.
- Contested Seals (Charm, Hex, Counterseal, Puppetmaster) roll against the target.
All 22 Seals of the Freestyle, Akakiru, Aoyusumu, Kiihakai, Kurokonton and Midorikatai lists are
here, in their own "Seals" interaction category. Scry and Hex replace the older perk-only
versions; their perks (Scrying Sphere, Hex) still teach them.

Usage: python tools/build_seals.py [--check]
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'AuraClash'
BOM = '﻿'
STYLES = ('akakiru', 'aoyusumu', 'kiihakai', 'kurokonton', 'midorikatai')
HANDSEALS_PERKS = {0: 0, 1: 2, 2: 5, 3: 8}
STYLE_AP_PERKS = {300: 0, 500: 3, 600: 3, 700: 5, 900: 7}
SKILLS = ('diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess')
BEASTS = ('sabretooth', 'quadrafang', 'mawcharger', 'shakengara', 'drake', 'wyrm')
FOUNDATIONS = ('dragon', 'rabbit', 'tiger', 'snake', 'stallion', 'ram', 'monkey', 'crane', 'wolf', 'boar', 'rat', 'ox')
PUPPET_DAYS = (30, 90, 180, 365, 1825, None)


def months(per='scope:ac_seal_successes', mult=1):
    # CK3 reads a duration only as a number or a named script value (see values()).
    return f'ac_seal_m{mult}'


# key: dict(name, school, style_ap, handseals, ap (int or expression), target ('self'/'other'/'any'),
#           cooldown, extra validity, options [(flag, loc)], effect, rulebook summary)
SEALS = {}


def seal(key, **kw):
    SEALS[key] = kw


# --- Freestyle Seals ---
seal('craft_shard', name='Craft Shard', school=None, style_ap=0, handseals=1, ap=100, target='self', cooldown='months = 3',
     effect='scope:actor = { add_gold = scope:ac_seal_ten }',
     text='Create Shards: 10 gold per success.', ai=20)
seal('reinforcement', name='Reinforcement', school=None, style_ap=0, handseals=1, ap=100, target='any', cooldown='months = 6',
     effect=('scope:recipient = { add_character_modifier = { modifier = ac_seal_reinforced_modifier months = ' + months() + ' } '
             'every_equipped_character_artifact = { add_durability = scope:ac_seal_ten } }'),
     text='Harden the target\'s arms and armour: +2 prowess and +5% knight effectiveness for a month per success; their equipment regains 10 durability per success.')
seal('four_winds', name='Four Winds Enhancement', school=None, style_ap=0, handseals=2, ap=100, target='any', cooldown='years = 1',
     options=[(f'ac_seal_skill_{s}', f'ac_seal_skill_{s}') for s in SKILLS],
     effect='FOUR_WINDS',
     text='+1d10 to a skill (here +3, or +5 prowess) for the caster, the target and one more courtier per extra success, for three months.')
seal('keystone', name='Keystone', school=None, style_ap=0, handseals=2, ap=300, target='self', cooldown='years = 5',
     effect='scope:actor = { add_character_modifier = ac_seal_keystone_modifier }',
     text='A mystical lock on your chambers that only your keystones open: enemy schemes against you -10%, permanently (until Counterseal).')
seal('counterseal', name='Counterseal', school=None, style_ap=0, handseals=3, ap=200, target='any', cooldown_recipient='years = 1',
     effect='COUNTERSEAL',
     text='End the Seals on the target, if your successes match the caster\'s. Whether it works or not, you cannot try again on them for a year.')
# --- Akakiru Seals ---
seal('reinforcement_improved', name='Reinforcement (Improved)', school='akakiru', style_ap=300, handseals=0, ap=100, target='self', cooldown='years = 5',
     valid='custom_tooltip = { text = ac_seal_needs_weapon_tt scope:actor = { ac_is_armed_trigger = yes } }',
     effect=('scope:actor = { random_equipped_character_artifact = { limit = { artifact_slot_type = primary_armament NOT = { has_variable = ac_seal_reinforced } } '
             'add_artifact_modifier = ac_seal_reinforced_artifact_modifier set_variable = ac_seal_reinforced } '
             'add_character_modifier = { modifier = ac_seal_crowd_modifier years = 5 } }'),
     text='The Reinforcement on your weapon is permanent (+2 prowess), and your soldiers\' weapons gain +1 Power (+10% pikemen and heavy infantry damage) for 5 years.')
seal('soulsoak', name='Soulsoak Imbuement', school='akakiru', style_ap=600, handseals=1, ap=200, target='self', cooldown='months = 6',
     valid='custom_tooltip = { text = ac_seal_needs_blade_tt scope:actor = { ac_wields_blade_trigger = yes } }',
     options=[('ac_seal_soulsoak_deep', 'ac_seal_soulsoak_deep')],
     effect=('scope:actor = { if = { limit = { scope:ac_seal_soulsoak_deep ?= yes } set_variable = { name = ac_soulsoak value = 4 months = ' + months() + ' } } '
             'else = { set_variable = { name = ac_soulsoak value = 2 months = ' + months() + ' } } }'),
     text='Infuse chi into your blade (200 AP, or 400 for twice the charges). In a Clash of Auras, release a charge for +3 to a roll; outside combat, release one to heal a wound (Release Soulsoak). Lasts a month per success.')
seal('celestial_forge', name='Celestial Forge', school='akakiru', style_ap=900, handseals=2, ap=200, target='self', cooldown='years = 5',
     valid='scope:actor = { ac_has_foundation_trigger = yes }',
     effect='scope:actor = { ac_seal_store_foundation_tier_effect = yes trigger_event = ac_seal.0010 }',
     text='Exchange your Foundation for a different one, keeping its tempering.')
# --- Aoyusumu Seals ---
seal('exorcism', name='Exorcism', school='aoyusumu', style_ap=300, handseals=0, ap=200, target='self', cooldown='years = 1',
     options=[(f'ac_seal_skill_{s}', f'ac_seal_skill_{s}') for s in SKILLS],
     effect='EXORCISM',
     text='Lay the dead of this county to rest (fewer Wraiths and malicious Kami: +5 county opinion, +5% development growth, a year per success). The thankful spirits lend +3 to a skill, a month per success.')
seal('prayer_engine', name='Prayer Engine', school='aoyusumu', style_ap=500, handseals=1, ap=100, target='self', cooldown='months = 6',
     effect='scope:actor = { add_character_modifier = { modifier = ac_seal_prayer_engine_modifier months = ' + months(mult=2) + ' } }',
     text='Hear the thoughts of those who pray to you: +1 piety and +5 same-faith opinion a month, for two months per success. The basis of many religions.', ai=10)
seal('heavenly_message', name='Heavenly Message', school='aoyusumu', style_ap=700, handseals=1, ap=100, target='self', cooldown='years = 1',
     effect='HEAVENLY_MESSAGE',
     text='Meditate upon the Celestial Bureaucracy for a clue: vague (1-2 successes), helpful (3-4), valuable secrets (5-7) or forbidden knowledge (8+). A botch misleads.')
seal('divine_intervention', name='Divine Intervention', school='aoyusumu', style_ap=900, handseals=2, ap=100, target='other', cooldown='months = 1',
     valid='custom_tooltip = { text = ac_seal_knows_or_prays_tt OR = { scope:actor = { has_character_modifier = ac_seal_prayer_engine_modifier } scope:recipient = { opinion = { target = scope:actor value >= 20 } } } }',
     effect='scope:recipient = { add_character_modifier = { modifier = ac_seal_divine_lock_modifier months = 3 } }',
     text='Lock a success for someone anywhere who knows you or prays to you: +5 prowess, +10% scheme success and +1 to Clash rolls for three months.')
# --- Kiihakai Seals ---
seal('scry', name='Scry', school='kiihakai', style_ap=300, handseals=0, ap=100, target='other', cooldown='years = 1', perk='ac_3_style_kiihakai_d_perk',
     effect='SCRY',
     text='A sphere of aura shows any place within 10 miles per success: reveal the target\'s secrets (Ward and Thousand-Face Mask resist).')
seal('ward', name='Ward', school='kiihakai', style_ap=500, handseals=0, ap=200, target='any', cooldown='months = 6',
     options=[('ac_seal_ward_building', 'ac_seal_ward_building')],
     effect='WARD',
     text='Ward a person (enemy schemes against them -25%, a month per success) or, cast on yourself, the county you stand in (+2 fort level, +25% garrison, a year per success).')
seal('charm', name='Charm', school='kiihakai', style_ap=700, handseals=1, ap=200, target='other', cooldown_recipient='years = 1',
     effect='CHARM',
     text='Contested by the target\'s Persuasion or Survival: on success they treat you as a good friend (+40 opinion for a year); on failure they turn hostile.')
seal('spiritbinding', name='Spiritbinding', school='kiihakai', style_ap=900, handseals=2, ap=300, target='any', cooldown='years = 1',
     options=[('ac_seal_spirit_earth', 'ac_seal_spirit_earth'), ('ac_seal_spirit_water', 'ac_seal_spirit_water'),
              ('ac_seal_spirit_wisp', 'ac_seal_spirit_wisp'), ('ac_seal_spirit_kami', 'ac_seal_spirit_kami')],
     effect='SPIRITBINDING',
     text='Bind a spirit to a task: an Earth Elemental builds walls, a Water Elemental cleanses the land, Wisps shriek at intruders, or a Kami possesses a rival\'s tools. A day per success becomes a month; 5 successes binds it for good.')
# --- Kurokonton Seals ---
seal('hex', name='Hex', school='kurokonton', style_ap=300, handseals=0, ap=100, target='other', cooldown_recipient='years = 1', perk='ac_3_style_kurokonton_c_perk',
     options=[(f'ac_seal_skill_{s}', f'ac_seal_skill_{s}') for s in SKILLS],
     effect='HEX',
     text='A Power Clash against the target (Aura Pressure decides): on success, a skill of your choice drops by 1 plus 2 per success (up to 12) for a year.')
seal('thousand_face_mask', name='Thousand-Face Mask', school='kurokonton', style_ap=600, handseals=1, ap=100, target='self', cooldown='months = 3',
     effect='scope:actor = { add_character_modifier = { modifier = ac_seal_mask_modifier months = 3 } }',
     text='Change your appearance and mask your aura: +10% scheme success, and +20 scheme secrecy for three months; Scry fails on you.', ai=5)
seal('puppetmaster', name='Puppetmaster', school='kurokonton', style_ap=900, handseals=1, ap='PUPPET', target='other', cooldown_recipient='years = 1',
     valid=('custom_tooltip = { text = ac_seal_puppet_weak_tt OR = { scope:recipient.ac_aura_pressure_value <= { value = scope:actor.ac_aura_pressure_value multiply = 0.1 } '
            'AND = { scope:recipient = { is_imprisoned_by = scope:actor } scope:recipient.ac_aura_pressure_value <= { value = scope:actor.ac_aura_pressure_value multiply = 0.5 } } } }'),
     effect='PUPPET',
     text='Bind a much weaker humanoid as your Minion (a strong hook). Needs 3 successes; each extra success lengthens it, from a day (a month) to permanent. Costs the target\'s Aura Pressure.')
# --- Midorikatai Seals ---
seal('subjugation_domain', name='Subjugation Domain', school='midorikatai', style_ap=300, handseals=0, ap=300, target='self', cooldown='years = 1',
     effect=('scope:actor = { every_held_county = { limit = { has_county_modifier = ac_seal_domain_county_modifier } remove_county_modifier = ac_seal_domain_county_modifier } '
             'location.county = { add_county_modifier = ac_seal_domain_county_modifier } add_character_modifier = ac_seal_domain_modifier }'),
     text='Claim the county you stand in as a Beast claims territory: Beasts keep away (+10% levies, +5 county opinion, +10% development growth) and you gain Advantage on Perception and Survival. One Domain at a time.')
seal('alpha_seal', name='Alpha Seal', school='midorikatai', style_ap=600, handseals=1, ap=200, target='self', cooldown='years = 1',
     valid='custom_tooltip = { text = ac_seal_needs_beast_tt scope:actor = { has_variable = ac_beast_defeated } }',
     effect='ALPHA',
     text='Seal a Beast you have just brought down: it serves you as its Master (prowess, dread and knight effectiveness). Only one Beast at a time.')
seal('unlock_potential', name='Unlock Potential', school='midorikatai', style_ap=900, handseals=2, ap='UNLOCK', target='other', cooldown_recipient='years = 1',
     valid=('scope:recipient = { has_trait = ac_cultivator } custom_tooltip = { text = ac_seal_unlock_weak_tt '
            'scope:recipient.ac_aura_pressure_value < { value = scope:actor.ac_aura_pressure_value multiply = 0.5 } }'),
     effect='UNLOCK',
     text='Grant 100 Aura Pressure, plus 100 per 1,000 of your own, to someone with less than half of yours. Costs as much as it grants.')


def ap_value(s, who='scope:actor'):
    ap = s['ap']
    if ap == 'PUPPET':
        return '{ value = scope:recipient.ac_aura_pressure_value min = 100 }'
    if ap == 'UNLOCK':
        return '{ value = scope:actor.ac_aura_pressure_value divide = 1000 floor = yes multiply = 100 add = 100 }'
    return str(ap)


def special_effect(key, s):
    eff = s['effect']
    succ = 'scope:ac_seal_successes'
    if eff == 'FOUR_WINDS':
        out = []
        for skill in SKILLS:
            out.append(f'if = {{ limit = {{ scope:ac_seal_skill_{skill} ?= yes }} '
                       f'scope:actor = {{ add_character_modifier = {{ modifier = ac_seal_four_winds_{skill} months = 3 }} }} '
                       f'scope:recipient = {{ add_character_modifier = {{ modifier = ac_seal_four_winds_{skill} months = 3 }} }} '
                       f'scope:actor = {{ while = {{ count = scope:ac_seal_extra random_courtier = {{ limit = {{ NOT = {{ has_character_modifier = ac_seal_four_winds_{skill} }} }} '
                       f'add_character_modifier = {{ modifier = ac_seal_four_winds_{skill} months = 3 }} }} }} }} }}')
        return ' '.join(out)
    if eff == 'COUNTERSEAL':
        removable = ['ac_seal_warded_modifier', 'ac_seal_keystone_modifier', 'ac_seal_mask_modifier', 'ac_seal_kami_modifier',
                     'ac_seal_divine_lock_modifier', 'ac_seal_reinforced_modifier'] + \
                    [f'ac_hex_{s}_{n}' for s in SKILLS for n in range(1, 13)]
        removes = ' '.join(f'remove_character_modifier = {m}' for m in removable)
        return (f'scope:recipient = {{ if = {{ limit = {{ OR = {{ NOT = {{ has_variable = ac_seal_power }} var:ac_seal_power <= {succ} }} }} {removes} remove_variable = ac_seal_power '
                'custom_tooltip = ac_seal_counterseal_done_tt } else = { custom_tooltip = ac_seal_counterseal_failed_tt } }')
    if eff == 'EXORCISM':
        boons = ' '.join(f'if = {{ limit = {{ scope:ac_seal_skill_{skill} ?= yes }} add_character_modifier = {{ modifier = ac_seal_exorcism_{skill} months = {months()} }} }}'
                         for skill in SKILLS)
        return (f'scope:actor = {{ location.county = {{ add_county_modifier = {{ modifier = ac_seal_exorcised_county_modifier years = {months()} }} }} {boons} }}')
    if eff == 'HEAVENLY_MESSAGE':
        return ('scope:actor = { '
                f'if = {{ limit = {{ {succ} >= 8 }} ac_gain_cultivation_study_xp_effect = {{ XP = 500 }} custom_tooltip = ac_seal_message_forbidden_tt }} '
                f'else_if = {{ limit = {{ {succ} >= 5 }} every_relation = {{ type = rival every_secret = {{ reveal_to = scope:actor }} }} '
                'liege ?= { every_secret = { reveal_to = scope:actor } } custom_tooltip = ac_seal_message_secrets_tt } '
                f'else_if = {{ limit = {{ {succ} >= 3 }} random_relation = {{ type = rival random_secret = {{ reveal_to = scope:actor }} }} add_learning_lifestyle_xp = 200 custom_tooltip = ac_seal_message_helpful_tt }} '
                f'else_if = {{ limit = {{ {succ} >= 1 }} add_learning_lifestyle_xp = 100 custom_tooltip = ac_seal_message_vague_tt }} '
                'else = { add_stress = 20 custom_tooltip = ac_seal_message_botch_tt } }')
    if eff == 'SCRY':
        return ('scope:recipient = { if = { limit = { OR = { has_character_modifier = ac_seal_warded_modifier has_character_modifier = ac_seal_mask_modifier } '
                f'has_variable = ac_seal_power var:ac_seal_power > {succ} }} custom_tooltip = ac_seal_scry_blocked_tt }} '
                'else_if = { limit = { any_secret = { always = yes } } every_secret = { reveal_to = scope:actor } custom_tooltip = ac_seal_scry_found_tt } '
                'else = { custom_tooltip = ac_seal_scry_nothing_tt } }')
    if eff == 'WARD':
        return ('if = { limit = { scope:ac_seal_ward_building ?= yes scope:recipient = scope:actor } '
                f'scope:actor.location.county = {{ add_county_modifier = {{ modifier = ac_seal_ward_county_modifier years = {months()} }} }} }} '
                f'else = {{ scope:recipient = {{ add_character_modifier = {{ modifier = ac_seal_warded_modifier months = {months()} }} set_variable = {{ name = ac_seal_power value = {succ} months = {months()} }} }} }}')
    if eff == 'CHARM':
        return ('scope:recipient = { ac_seal_resist_roll_effect = { SKILL = diplomacy } } '
                f'if = {{ limit = {{ {succ} > scope:recipient.var:ac_seal_resist }} scope:recipient = {{ add_opinion = {{ target = scope:actor modifier = ac_seal_charmed_opinion }} }} custom_tooltip = ac_seal_charm_success_tt }} '
                'else = { scope:recipient = { add_opinion = { target = scope:actor modifier = ac_seal_charm_attempt_opinion } } custom_tooltip = ac_seal_charm_failed_tt } '
                'scope:recipient = { remove_variable = ac_seal_resist }')
    if eff == 'SPIRITBINDING':
        return ('if = { limit = { scope:ac_seal_spirit_earth ?= yes } scope:actor.location.county = { add_county_modifier = { modifier = ac_seal_earth_spirit_county_modifier months = ac_seal_spirit_months } } } '
                'else_if = { limit = { scope:ac_seal_spirit_water ?= yes } scope:actor.location.county = { add_county_modifier = { modifier = ac_seal_water_spirit_county_modifier months = ac_seal_spirit_months } } } '
                'else_if = { limit = { scope:ac_seal_spirit_kami ?= yes NOT = { scope:recipient = scope:actor } } scope:recipient = { add_character_modifier = { modifier = ac_seal_kami_modifier months = ac_seal_spirit_months } set_variable = { name = ac_seal_power value = scope:ac_seal_successes months = ac_seal_spirit_months } } } '
                'else = { scope:recipient = { add_character_modifier = { modifier = ac_seal_wisp_modifier months = ac_seal_spirit_months } } }')
    if eff == 'HEX':
        out = ['scope:recipient = { ac_seal_power_clash_effect = yes }',
               f'if = {{ limit = {{ {succ} > scope:recipient.var:ac_seal_resist }}',
               f'\tsave_scope_value_as = {{ name = ac_seal_hex value = {{ value = {succ} multiply = 2 add = 1 max = 12 }} }}']
        for skill in SKILLS:
            chain = ' '.join(f'{"if" if n == 12 else "else_if"} = {{ limit = {{ scope:ac_seal_hex >= {n} }} add_character_modifier = {{ modifier = ac_hex_{skill}_{n} years = 1 }} }}'
                             for n in range(12, 0, -1))
            out.append(f'\tif = {{ limit = {{ scope:ac_seal_skill_{skill} ?= yes }} scope:recipient = {{ {chain} set_variable = {{ name = ac_seal_power value = {succ} years = 1 }} }} }}')
        out += ['\tcustom_tooltip = ac_seal_hex_success_tt', '}',
                'else = { scope:recipient = { add_opinion = { target = scope:actor modifier = ac_seal_charm_attempt_opinion } } custom_tooltip = ac_seal_hex_failed_tt }',
                'scope:recipient = { remove_variable = ac_seal_resist }']
        return ' '.join(out)
    if eff == 'PUPPET':
        chain = []
        for i, days in enumerate(PUPPET_DAYS):
            n = 3 + i
            cond = f'{succ} >= {n}' if i < len(PUPPET_DAYS) - 1 else f'{succ} >= {n}'
            chain.append((n, f'scope:actor = {{ add_hook = {{ type = ac_puppet_hook_{i + 1} target = scope:recipient }} }}'))
        body = ' '.join(f'{"if" if j == 0 else "else_if"} = {{ limit = {{ {succ} >= {n} }} {e} }}' for j, (n, e) in enumerate(reversed(chain)))
        return (f'if = {{ limit = {{ {succ} >= 3 }} {body} custom_tooltip = ac_seal_puppet_success_tt }} '
                'else = { scope:recipient = { add_opinion = { target = scope:actor modifier = ac_seal_charm_attempt_opinion } } custom_tooltip = ac_seal_puppet_failed_tt }')
    if eff == 'ALPHA':
        removes = ' '.join(f'remove_character_modifier = ac_seal_alpha_{b}_modifier' for b in BEASTS)
        adds = ' '.join(f'if = {{ limit = {{ var:ac_beast_defeated = flag:{b} }} add_character_modifier = ac_seal_alpha_{b}_modifier }}' for b in BEASTS)
        return f'scope:actor = {{ {removes} {adds} remove_variable = ac_beast_defeated }}'
    if eff == 'UNLOCK':
        return ('save_scope_value_as = { name = ac_seal_grant value = ' + ap_value(s) + ' } '
                'scope:recipient = { ac_init_aura_effect = yes change_variable = { name = ac_aura_pressure add = scope:ac_seal_grant } '
                'set_variable = { name = ac_unlocked_by value = scope:actor } } custom_tooltip = ac_seal_unlock_tt')
    return eff


def requirement_trigger(key, s):
    conds = ['has_trait = ac_cultivator', 'age >= 16']
    if s['handseals']:
        conds.append(f'ac_handseals_rank >= {s["handseals"]}')
    style_req = []
    if s['school']:
        style_req.append(f'AND = {{ has_trait = ac_style_{s["school"]} ac_{s["school"]}_perk_count >= {STYLE_AP_PERKS[s["style_ap"]]} }}')
    if s.get('perk'):
        style_req.append(f'has_perk = {s["perk"]}')
    if style_req:
        conds.append('OR = { ' + ' '.join(style_req) + ' }' if len(style_req) > 1 else style_req[0])
    return f'ac_seal_{key}_known_trigger = {{ ' + ' '.join(conds) + ' }'


def interaction(key, s):
    ap = ap_value(s)
    chi = f'{{ value = {ap} divide = 100 ceiling = yes min = 1 }}'
    shards = f'{{ value = {ap} divide = 10 ceiling = yes }}'
    target = {'self': 'scope:recipient = scope:actor', 'other': 'NOT = { scope:recipient = scope:actor }', 'any': 'always = yes'}[s['target']]
    out = [f'ac_seal_{key}_interaction = {{', '\tcategory = interaction_category_ac_seals', '\tcommon_interaction = no',
           '\ticon = secret', f'\tdesc = ac_seal_{key}_interaction_desc', '\tauto_accept = yes']
    if s.get('cooldown'):
        out.append(f'\tcooldown = {{ {s["cooldown"]} }}')
    if s.get('cooldown_recipient'):
        out.append(f'\tcooldown_against_recipient = {{ {s["cooldown_recipient"]} }}')
    out += ['\tis_shown = {', f'\t\tscope:actor = {{ ac_seal_{key}_known_trigger = yes }}', f'\t\t{target}',
            '\t\tscope:recipient = { is_alive = yes }', '\t}',
            '\tis_valid_showing_failures_only = {', '\t\tscope:actor = { is_imprisoned = no }']
    if s.get('valid'):
        out.append(f'\t\t{s["valid"]}')
    out += ['\t}',
            '\tsend_options_exclusive = no',
            '\tsend_option = { flag = ac_seal_pay_shards localization = ac_seal_pay_shards_option }']
    exclusive = s.get('options', [])
    for flag, loc in exclusive:
        out.append(f'\tsend_option = {{ flag = {flag} localization = {loc} }}')
    out += ['\tcan_send = {',
            '\t\tcustom_description = {', '\t\t\ttext = ac_seal_cost_tt',
            f'\t\t\tOR = {{ AND = {{ scope:ac_seal_pay_shards ?= yes scope:actor.short_term_gold >= {shards} }} '
            f'AND = {{ NOT = {{ scope:ac_seal_pay_shards ?= yes }} scope:actor.ac_chi_available >= {chi} }} }}',
            '\t\t}']
    if exclusive and s['effect'] in ('FOUR_WINDS', 'EXORCISM', 'HEX'):
        out.append('\t\tcustom_description = { text = ac_seal_pick_skill_tt OR = { ' + ' '.join(f'scope:{f} ?= yes' for f, _ in exclusive) + ' } }')
    if s['effect'] == 'SPIRITBINDING':
        out.append('\t\tcustom_description = { text = ac_seal_pick_spirit_tt OR = { ' + ' '.join(f'scope:{f} ?= yes' for f, _ in exclusive) + ' } }')
    out += ['\t}',
            '\ton_accept = {',
            '\t\tscope:actor = {',
            f'\t\t\tif = {{ limit = {{ scope:ac_seal_pay_shards ?= yes }} remove_short_term_gold = {shards} }}',
            # A scripted effect's parameter must be a single token, so the cost is saved first.
            f'\t\t\telse = {{ save_scope_value_as = {{ name = ac_seal_chi value = {chi} }} ac_spend_chi_effect = {{ CHI = scope:ac_seal_chi }} }}',
            '\t\t\tac_seal_roll_effect = yes',
            '\t\t\tsave_scope_value_as = { name = ac_seal_successes value = var:ac_seal_successes }',
            '\t\t\tsave_scope_value_as = { name = ac_seal_extra value = { value = var:ac_seal_successes subtract = 1 min = 0 } }',
            '\t\t\tsave_scope_value_as = { name = ac_seal_ten value = { value = var:ac_seal_successes multiply = 10 } }',
            '\t\t}',
            f'\t\tcustom_tooltip = ac_seal_{key}_effect_tt',
            '\t\tshow_as_tooltip = { scope:actor = { custom_tooltip = ac_seal_roll_tt } }',
            f'\t\thidden_effect = {{ {special_effect(key, s)} }}',
            '\t\tscope:actor = {',
            '\t\t\tsend_interface_toast = {', '\t\t\t\ttype = event_toast_effect_neutral', f'\t\t\t\ttitle = ac_seal_{key}_toast',
            '\t\t\t\tleft_icon = scope:actor', '\t\t\t\tright_icon = scope:recipient', '\t\t\t\tcustom_tooltip = ac_seal_successes_tt', '\t\t\t}',
            # Kept for a day so the toast can show the roll.
            '\t\t\tset_variable = { name = ac_seal_successes value = scope:ac_seal_successes days = 1 }',
            '\t\t}',
            '\t}']
    if s.get('ai'):
        out += ['\tai_targets = { ai_recipients = self }', '\tai_frequency = 12',
                f'\tai_potential = {{ ac_seal_{key}_known_trigger = yes }}', f'\tai_will_do = {{ base = {s["ai"]} }}']
    else:
        out.append('\tai_will_do = { base = 0 }')
    out.append('}')
    return '\n'.join(out)


def interactions():
    release = '\n'.join([
        '# Soulsoak, outside combat: "End the Seal to heal" (here, one wound per charge).',
        'ac_seal_release_soulsoak_interaction = {',
        '\tcategory = interaction_category_ac_seals',
        '\tcommon_interaction = no',
        '\ticon = wound',
        '\tdesc = ac_seal_release_soulsoak_interaction_desc',
        '\tauto_accept = yes',
        '\tis_shown = { scope:recipient = scope:actor scope:actor = { has_variable = ac_soulsoak } }',
        '\tis_valid_showing_failures_only = { scope:actor = { custom_tooltip = { text = ac_chi_healing_needs_wound_tt has_trait = wounded } } }',
        '\ton_accept = { scope:actor = { ac_seal_release_soulsoak_effect = yes remove_character_flag = ac_duel_soulsoak ac_heal_one_wound_effect = yes } }',
        '\tai_targets = { ai_recipients = self }',
        '\tai_frequency = 6',
        '\tai_potential = { has_variable = ac_soulsoak }',
        '\tai_will_do = { base = 100 }',
        '}'])
    return ('# Generated by tools/build_seals.py. Rulebook chapter 7, Seals.\n' + '\n\n'.join(interaction(k, s) for k, s in SEALS.items())
            + '\n\n' + release)


def category():
    return '\n'.join([
        '# Generated by tools/build_seals.py. The next free index after vanilla\'s 0-15 (no gaps allowed).',
        'interaction_category_ac_seals = {',
        '\tindex = 16',
        '\tdesc = "AC_SEAL_ACTIONS"',
        '\tcolor = { 0.55 0.75 0.95 1 }',
        '\ticon = "secret"',
        '}',
    ])


def values():
    out = ['# Generated by tools/build_seals.py. Character scope.',
           '# Handseals rank: +1d6, +2d6 and +3d6 at 2, 5 and 8 Handseals perks.',
           'ac_handseals_perks = {', '\tvalue = 0',
           *[f'\tif = {{ limit = {{ has_perk = ac_2_handseals_{l}_perk }} add = 1 }}' for l in 'abcdefghij'], '}',
           'ac_handseals_rank = {', '\tvalue = 0',
           *[f'\tif = {{ limit = {{ ac_handseals_perks >= {p} }} value = {r} }}' for r, p in HANDSEALS_PERKS.items() if r], '}',
           'ac_seal_dice = { value = ac_handseals_rank add = 2 }',
           '# Durations, from the successes saved by the casting (scope:ac_seal_successes).',
           'ac_seal_m1 = { value = scope:ac_seal_successes min = 1 }',
           'ac_seal_m2 = { value = scope:ac_seal_successes multiply = 2 min = 1 }',
           '# Spiritbinding: a day per success becomes a month; 3, 6 and 12 months; 5 successes binds for good.',
           'ac_seal_spirit_months = { value = 1 if = { limit = { scope:ac_seal_successes >= 2 } value = 3 } '
           'if = { limit = { scope:ac_seal_successes >= 3 } value = 6 } if = { limit = { scope:ac_seal_successes >= 4 } value = 12 } '
           'if = { limit = { scope:ac_seal_successes >= 5 } value = 240 } }',
           '# Resisting: dice from a skill (rulebook Survival, Persuasion or Power).',
           'ac_seal_resist_dice_diplomacy = { value = diplomacy if = { limit = { prowess > diplomacy } value = prowess } divide = 5 floor = yes add = 1 max = 8 }',
           'ac_seal_power_dice = { value = ac_aura_pressure_value divide = 500 floor = yes add = 1 max = 10 }']
    return '\n'.join(out)


def effects():
    out = ['# Generated by tools/build_seals.py.', '',
           '# Character scope: a d6 pool; each 5-6 is a success, and sixes explode.',
           'ac_seal_dice_effect = {',
           '\tset_variable = { name = $OUT$ value = 0 }',
           '\tset_variable = { name = ac_seal_dice_left value = $DICE$ }',
           '\twhile = {',
           '\t\tlimit = { var:ac_seal_dice_left > 0 }',
           '\t\trandom_list = {',
           '\t\t\t4 = { }',
           '\t\t\t1 = { change_variable = { name = $OUT$ add = 1 } }',
           '\t\t\t1 = { change_variable = { name = $OUT$ add = 1 } random = { chance = 33 change_variable = { name = $OUT$ add = 1 } } }',
           '\t\t}',
           '\t\tchange_variable = { name = ac_seal_dice_left add = -1 }',
           '\t}',
           '\tremove_variable = ac_seal_dice_left',
           '}',
           'ac_seal_roll_effect = { ac_seal_dice_effect = { OUT = ac_seal_successes DICE = ac_seal_dice } }',
           'ac_seal_resist_roll_effect = { ac_seal_dice_effect = { OUT = ac_seal_resist DICE = ac_seal_resist_dice_$SKILL$ } }',
           'ac_seal_power_clash_effect = { ac_seal_dice_effect = { OUT = ac_seal_resist DICE = ac_seal_power_dice } }', '',
           '# Celestial Forge: remember the Foundation\'s tempering (25 per tier).',
           'ac_seal_store_foundation_tier_effect = {',
           '\tset_variable = { name = ac_forge_foundation_xp value = 0 }']
    for f in FOUNDATIONS:
        for xp in (25, 50, 75, 100):
            out.append(f'\tif = {{ limit = {{ has_trait = ac_foundation_{f} has_trait_xp = {{ trait = ac_foundation_{f} value >= {xp} }} }} set_variable = {{ name = ac_forge_foundation_xp value = {xp} }} }}')
    out += ['}', '',
            '# Duel: release a Soulsoak charge (fighter scope).',
            'ac_seal_release_soulsoak_effect = {',
            '\tchange_variable = { name = ac_soulsoak add = -1 }',
            '\tif = { limit = { var:ac_soulsoak <= 0 } remove_variable = ac_soulsoak }',
            '\t# "Untap 100 AP per 100 AP spent": a spent Chi returns.',
            '\tif = { limit = { has_variable = ac_chi_spent var:ac_chi_spent > 0 } change_variable = { name = ac_chi_spent add = -1 } }',
            '\tadd_character_flag = ac_duel_soulsoak',
            '}']
    return '\n'.join(out)


def events():
    out = ['# Generated by tools/build_seals.py.', 'namespace = ac_seal', '',
           '# 0010 Celestial Forge: choose the new Foundation.',
           'ac_seal.0010 = {', '\ttype = character_event', '\ttitle = ac_seal.0010.t', '\tdesc = ac_seal.0010.desc', '\ttheme = learning',
           '\tleft_portrait = { character = root animation = personality_rational }']
    for f in FOUNDATIONS:
        removes = ' '.join(f'remove_trait = ac_foundation_{o}' for o in FOUNDATIONS if o != f)
        out += ['\toption = {', f'\t\tname = ac_seal.0010.{f}', f'\t\ttrigger = {{ NOT = {{ has_trait = ac_foundation_{f} }} }}',
                f'\t\t{removes}', f'\t\tadd_trait = ac_foundation_{f}',
                f'\t\tif = {{ limit = {{ var:ac_forge_foundation_xp > 0 }} add_trait_xp = {{ trait = ac_foundation_{f} value = var:ac_forge_foundation_xp }} }}',
                '\t\tremove_variable = ac_forge_foundation_xp', '\t}']
    out += ['\toption = { name = ac_seal.0010.keep remove_variable = ac_forge_foundation_xp }', '}']
    return '\n'.join(out)


def modifiers():
    out = ['# Generated by tools/build_seals.py.',
           'ac_seal_reinforced_modifier = { icon = prowess_positive prowess = 2 knight_effectiveness_mult = 0.05 }',
           'ac_seal_reinforced_artifact_modifier = { icon = prowess_positive prowess = 2 }',
           'ac_seal_crowd_modifier = { icon = martial_positive pikemen_damage_mult = 0.1 heavy_infantry_damage_mult = 0.1 }',
           'ac_seal_keystone_modifier = { icon = intrigue_positive enemy_hostile_scheme_success_chance_add = -10 }',
           'ac_seal_prayer_engine_modifier = { icon = piety_positive monthly_piety = 1 same_faith_opinion = 5 }',
           'ac_seal_divine_lock_modifier = { icon = prowess_positive prowess = 5 owned_hostile_scheme_success_chance_add = 10 }',
           'ac_seal_warded_modifier = { icon = intrigue_positive enemy_hostile_scheme_success_chance_add = -25 }',
           'ac_seal_wisp_modifier = { icon = intrigue_positive enemy_hostile_scheme_success_chance_add = -15 }',
           'ac_seal_kami_modifier = { icon = stewardship_negative stewardship = -3 martial = -2 }',
           'ac_seal_mask_modifier = { icon = intrigue_positive owned_hostile_scheme_success_chance_add = 10 owned_scheme_secrecy_add = 20 }',
           'ac_seal_domain_modifier = { icon = prowess_positive epidemic_resistance = 10 enemy_hostile_scheme_success_chance_add = -5 }',
           'ac_seal_exorcised_county_modifier = { icon = county_modifier_opinion_positive county_opinion_add = 5 development_growth_factor = 0.05 }',
           'ac_seal_ward_county_modifier = { icon = county_modifier_control_positive fort_level = 2 garrison_size = 0.25 }',
           'ac_seal_earth_spirit_county_modifier = { icon = county_modifier_development_positive build_speed = -0.25 fort_level = 1 }',
           'ac_seal_water_spirit_county_modifier = { icon = county_modifier_development_positive development_growth_factor = 0.2 county_opinion_add = 5 }',
           'ac_seal_domain_county_modifier = { icon = county_modifier_development_positive levy_size = 0.1 county_opinion_add = 5 development_growth_factor = 0.1 }']
    for skill in SKILLS:
        amount = 5 if skill == 'prowess' else 3
        out.append(f'ac_seal_four_winds_{skill} = {{ icon = {skill if skill != "prowess" else "prowess"}_positive {skill} = {amount} }}')
        out.append(f'ac_seal_exorcism_{skill} = {{ icon = {skill if skill != "prowess" else "prowess"}_positive {skill} = {amount} }}')
    for beast in BEASTS:
        out.append(f'ac_seal_alpha_{beast}_modifier = {{ icon = prowess_positive prowess = 4 dread_baseline_add = 10 knight_effectiveness_mult = 0.05 }}')
    return '\n'.join(out)


def opinions():
    return '\n'.join([
        '# Generated by tools/build_seals.py.',
        'ac_seal_charmed_opinion = { opinion = 40 years = 1 }',
        'ac_seal_charm_attempt_opinion = { opinion = -20 years = 2 }',
    ])


def hooks():
    out = ['# Generated by tools/build_seals.py. Puppetmaster: a Minion, from a day (here a month) to permanent.']
    for i, days in enumerate(PUPPET_DAYS, 1):
        exp = f' expiration_days = {days}' if days else ''
        out.append(f'ac_puppet_hook_{i} = {{ strong = yes{exp} }}')
    return '\n'.join(out)


def localization():
    out = ['l_english:',
           ' AC_SEAL_ACTIONS:0 "Seals"',
           ' interaction_category_ac_seals:0 "Seals"',
           ' ac_seal_release_soulsoak_interaction:0 "Release Soulsoak"',
           ' ac_seal_release_soulsoak_interaction_desc:0 "End a charge of the Soulsoak Imbuement in my blade to heal a wound."',
           ' ac_seal_pay_shards_option:0 "Pay in Shards (a tenth of the Aura Pressure, in gold) instead of Chi"',
           ' ac_seal_cost_tt:0 "Enough Chi (1 per 100 Aura Pressure), or Shards"',
           ' ac_seal_pick_skill_tt:0 "Choose a skill"',
           ' ac_seal_pick_spirit_tt:0 "Choose a spirit"',
           ' ac_seal_roll_tt:0 "A Handseals roll: 2 dice plus 1 per Handseals rank; each 5-6 is a success, and sixes explode."',
           " ac_seal_successes_tt:0 \"Handseals successes: #V [GetPlayer.MakeScope.Var('ac_seal_successes').GetValue|0]#!\"",
           ' ac_seal_needs_weapon_tt:0 "Wielding a weapon"',
           ' ac_seal_needs_blade_tt:0 "Wielding a bladed weapon"',
           ' ac_seal_knows_or_prays_tt:0 "They know me (opinion 20+), or my Prayer Engine hears them"',
           ' ac_seal_puppet_weak_tt:0 "Their Aura Pressure is no more than a tenth of mine (half, if they are my prisoner)"',
           ' ac_seal_unlock_weak_tt:0 "Their Aura Pressure is less than half of mine"',
           ' ac_seal_needs_beast_tt:0 "I have brought down a Spirit Beast this year"',
           ' ac_seal_counterseal_done_tt:0 "The Seals on them unravel."',
           ' ac_seal_counterseal_failed_tt:0 "The original Seal holds."',
           ' ac_seal_message_forbidden_tt:0 "Potentially forbidden knowledge: +500 cultivation experience."',
           ' ac_seal_message_secrets_tt:0 "Valuable secrets: my rivals\' and my liege\'s secrets are revealed."',
           ' ac_seal_message_helpful_tt:0 "Helpful information: a rival\'s secret."',
           ' ac_seal_message_vague_tt:0 "A vague and possibly useless answer."',
           ' ac_seal_message_botch_tt:0 "A purposefully misleading answer."',
           ' ac_seal_scry_blocked_tt:0 "A Ward or mask clouds the sphere."',
           ' ac_seal_scry_found_tt:0 "Their secrets are revealed."',
           ' ac_seal_scry_nothing_tt:0 "They hide nothing."',
           ' ac_seal_charm_success_tt:0 "They now treat me as a good friend."',
           ' ac_seal_charm_failed_tt:0 "They notice the attempt and turn hostile."',
           ' ac_seal_hex_success_tt:0 "The Hex takes hold."',
           ' ac_seal_hex_failed_tt:0 "They resist the Hex, and notice."',
           ' ac_seal_puppet_success_tt:0 "They act as my Minion."',
           ' ac_seal_puppet_failed_tt:0 "They resist the binding, and notice."',
           ' ac_seal_unlock_tt:0 "Their potential unlocks."',
           ' ac_seal_soulsoak_deep:0 "Infuse 400 Aura Pressure (four charges)"',
           ' ac_seal_ward_building:0 "Ward the county I stand in (cast on myself)"',
           ' ac_seal_spirit_earth:0 "Earth Elemental: build walls here"',
           ' ac_seal_spirit_water:0 "Water Elemental: cleanse the land here"',
           ' ac_seal_spirit_wisp:0 "Wisps: shriek at intruders around the target"',
           ' ac_seal_spirit_kami:0 "Kami: possess the target\'s tools"',
           ' ac_seal_charmed_opinion:0 "Charmed"',
           ' ac_seal_charm_attempt_opinion:0 "Tried to Bewitch Me"',
           ' ac_seal.0010.t:0 "Celestial Forge"',
           ' ac_seal.0010.desc:0 "The Seal reaches into the foundations of my cultivation. For a moment they are malleable, and I may forge them anew."',
           ' ac_seal.0010.keep:0 "Keep my Foundation after all."']
    for skill in SKILLS:
        out.append(f' ac_seal_skill_{skill}:0 "[{skill}|E]"')
        out.append(f' ac_seal_four_winds_{skill}:0 "Four Winds Enhancement"')
        out.append(f' ac_seal_exorcism_{skill}:0 "Thankful Spirits"')
    for beast in BEASTS:
        out.append(f' ac_seal_alpha_{beast}_modifier:0 "Alpha of a {beast.title()}"')
        out.append(f' ac_seal_alpha_{beast}_modifier_desc:0 "A {beast.title()} serves this cultivator as its Master under the Alpha Seal."')
    for f in FOUNDATIONS:
        out.append(f' ac_seal.0010.{f}:0 "$trait_ac_foundation_{f}$"')
    for i in range(1, len(PUPPET_DAYS) + 1):
        out.append(f' ac_puppet_hook_{i}:0 "Puppet"')
    for key, s in SEALS.items():
        ap = s['ap'] if isinstance(s['ap'], int) else ('the target\'s Aura Pressure' if s['ap'] == 'PUPPET' else 'the Aura Pressure granted')
        cost = f'{ap} Aura Pressure ({ap // 100} Chi or {ap // 10} Shards)' if isinstance(ap, int) else ap
        reqs = []
        if s['school']:
            n = STYLE_AP_PERKS[s['style_ap']]
            reqs.append(f'{s["style_ap"]} AP in {s["school"].title()} Techniques ({s["school"].title()}' + (f' with {n} of its perks' if n else '') + ')')
        if s['handseals']:
            reqs.append(f'Handseals +{s["handseals"]}d6 ({HANDSEALS_PERKS[s["handseals"]]} Handseals perks)')
        req = '; '.join(reqs) if reqs else 'none'
        out += [f' ac_seal_{key}_interaction:0 "{s["name"]}"',
                f' ac_seal_{key}_interaction_desc:0 "#bold {s["name"]}#! (Seal). {s["text"]}\\nRequires: {req}. Cost: {cost}."',
                f' ac_seal_{key}_effect_tt:0 "{s["text"]}"',
                f' ac_seal_{key}_toast:0 "{s["name"]}"']
    for name in ['ac_seal_reinforced_modifier', 'ac_seal_reinforced_artifact_modifier', 'ac_seal_crowd_modifier', 'ac_seal_keystone_modifier',
                 'ac_seal_prayer_engine_modifier', 'ac_seal_divine_lock_modifier', 'ac_seal_warded_modifier', 'ac_seal_wisp_modifier',
                 'ac_seal_kami_modifier', 'ac_seal_mask_modifier', 'ac_seal_domain_modifier', 'ac_seal_exorcised_county_modifier',
                 'ac_seal_ward_county_modifier', 'ac_seal_earth_spirit_county_modifier', 'ac_seal_water_spirit_county_modifier',
                 'ac_seal_domain_county_modifier']:
        label = {'ac_seal_reinforced_modifier': 'Reinforced Arms', 'ac_seal_reinforced_artifact_modifier': 'Permanent Reinforcement',
                 'ac_seal_crowd_modifier': 'Reinforced Armoury', 'ac_seal_keystone_modifier': 'Keystone Seal',
                 'ac_seal_prayer_engine_modifier': 'Prayer Engine', 'ac_seal_divine_lock_modifier': 'Divine Intervention',
                 'ac_seal_warded_modifier': 'Warded', 'ac_seal_wisp_modifier': 'Bound Wisps', 'ac_seal_kami_modifier': 'Possessed Tools',
                 'ac_seal_mask_modifier': 'Thousand-Face Mask', 'ac_seal_domain_modifier': 'Subjugation Domain',
                 'ac_seal_exorcised_county_modifier': 'Exorcised', 'ac_seal_ward_county_modifier': 'Warded Holdings',
                 'ac_seal_earth_spirit_county_modifier': 'Earth Elemental', 'ac_seal_water_spirit_county_modifier': 'Water Elemental',
                 'ac_seal_domain_county_modifier': 'Beast Domain'}[name]
        out.append(f' {name}:0 "{label}"')
        out.append(f' {name}_desc:0 "A Seal\'s effect."')
    return '\n'.join(out)


def triggers():
    return '# Generated by tools/build_seals.py. Character scope: knows the Seal.\n' + '\n'.join(requirement_trigger(k, s) for k, s in SEALS.items())


def render():
    texts = {
        'common/character_interactions/ac_seal_interactions.txt': interactions(),
        'common/character_interaction_categories/ac_seal_category.txt': category(),
        'common/script_values/ac_seal_values.txt': values(),
        'common/scripted_triggers/ac_seal_triggers.txt': triggers(),
        'common/scripted_effects/ac_seal_effects.txt': effects(),
        'common/modifiers/ac_seal_modifiers.txt': modifiers(),
        'common/opinion_modifiers/ac_seal_opinions.txt': opinions(),
        'common/hook_types/ac_seal_hooks.txt': hooks(),
        'events/ac_seal_events.txt': events(),
        'localization/english/ac_seal_l_english.yml': localization(),
    }
    return {k: (BOM + v.rstrip('\n') + '\n').encode('utf-8') for k, v in texts.items()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = render()
    if args.check:
        stale = [r for r, d in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != d]
        if stale:
            raise SystemExit('Stale generated files: ' + ', '.join(stale))
    else:
        for relative, data in files.items():
            path = OUT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f'Seals: {len(files)} files, {len(SEALS)} Seals.')


if __name__ == '__main__':
    main()
