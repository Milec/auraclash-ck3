"""Lore data for Imperial Rasen: peoples, faiths, holy sites and the starting cast.

Canon (from the Aura Clash game text): Zenshin culture and its Cathayan origins; Oni,
Yokai and Kitsune; the Devanic Temple, its Saints and Fiend-hunters; Shugendo; Wild
Gods such as Gazhurra; the Exalted Council's five Exalts (Bladed Exalt Ryuuzan
Masaru, the Wild Exalt); the Ozaki shinobi clan; Magistrates Khan and Fuyu.
Names marked "generated" are placeholders for characters the game has not named.

Vanilla graphics keys (coa/building/clothing/unit gfx) and doctrine/tenet keys must
exist in CK3 1.20; verify them in-game and swap in East Asian assets when available.
"""

START = (3000, 3, 1)

# Personality pairs; each character takes one trait from three different pairs.
TRAIT_GROUPS = [
    ['brave', 'craven'], ['calm', 'wrathful'], ['diligent', 'lazy'], ['honest', 'deceitful'],
    ['ambitious', 'content'], ['generous', 'greedy'], ['just', 'arbitrary'], ['zealous', 'cynical'],
    ['patient', 'impatient'], ['humble', 'arrogant'], ['gregarious', 'shy'], ['trusting', 'paranoid'],
    ['compassionate', 'callous'],
]

STEPPE_GFX = {
    'coa_gfx': ['mongol_coa_gfx', 'steppe_coa_gfx'],
    'building_gfx': ['steppe_building_gfx'],
    'clothing_gfx': ['mongol_clothing_gfx'],
    'unit_gfx': ['mongol_unit_gfx'],
}

CULTURES = {
    'zenshin': dict(name='Zenshin', prefix='Zen', plural='Zenshin', colour=(200, 60, 50),
                    desc='The people of Imperial Rasen, descended from Cathayan settlers. For three millennia the katana has set Zenshin warriors apart from their Cathayan forebears.',
                    heritage='heritage_zenshin', heritage_name='Zenshin', language='language_zenshin', language_name='Zenshin',
                    ethos='ethos_bellicose', martial_custom='martial_custom_equal', name_list='name_list_zenshin', ethnicity='asian',
                    traditions=['tradition_martial_admiration', 'tradition_ruling_caste', 'tradition_castle_keepers', 'tradition_legalistic'], **STEPPE_GFX),
    'cathayan': dict(name='Cathayan', prefix='Cathay', plural='Cathayans', colour=(210, 160, 60),
                     desc='Heirs of the Cathayan Empire, shattered by the Calamity. Their hanfu robes, qiang and jian survive across the Mystic and Sacred Lands.',
                     heritage='heritage_cathayan', heritage_name='Cathayan', language='language_cathayan', language_name='Old Cathayan',
                     ethos='ethos_bureaucratic', martial_custom='martial_custom_equal', name_list='name_list_cathayan', ethnicity='asian',
                     traditions=['tradition_philosopher_culture', 'tradition_poetry', 'tradition_legalistic'], **STEPPE_GFX),
    'oni': dict(name='Oni', prefix='Oni', plural='Oni', colour=(170, 40, 40),
                desc='Spirits who longed for a human form. Oni are horned, often red-skinned, and formidable in body.',
                heritage='heritage_oni', heritage_name='Oni', language='language_zenshin', language_name='Zenshin',
                ethos='ethos_stoic', martial_custom='martial_custom_equal', name_list='name_list_zenshin', ethnicity='asian',
                traditions=['tradition_warrior_culture', 'tradition_mountain_homes', 'tradition_stalwart_defenders'], **STEPPE_GFX),
    'yokai': dict(name='Yokai', prefix='Yokai', plural='Yokai', colour=(90, 130, 50),
                  desc='Beasts who longed for a human form: wolf, monkey and stranger kin. Many roam the Wild Lands, where strength alone earns respect.',
                  heritage='heritage_yokai', heritage_name='Yokai', language='language_zenshin', language_name='Zenshin',
                  ethos='ethos_bellicose', martial_custom='martial_custom_equal', name_list='name_list_zenshin', ethnicity='asian',
                  traditions=['tradition_forest_folk', 'tradition_hit_and_run', 'tradition_warrior_culture'], **STEPPE_GFX),
    'lunargoth': dict(name='Lunargoth', prefix='Luna', plural='Lunargoths', colour=(170, 190, 220),
                      desc='Fair-haired northerners of Outer North who fill the Northern Army. They answer to the Divine General, call him Emperor of all ten Provinces, and treat boons and debts as cowardice.',
                      heritage='heritage_lunargoth', heritage_name='Lunargoth', language='language_lunargoth', language_name='Lunargothic',
                      ethos='ethos_stoic', martial_custom='martial_custom_equal', name_list='name_list_lunargoth', ethnicity='caucasian',
                      traditions=['tradition_stalwart_defenders', 'tradition_warrior_culture', 'tradition_mountain_homes'], **STEPPE_GFX),
    'kitsune': dict(name='Kitsune', prefix='Kitsune', plural='Kitsune', colour=(220, 120, 40),
                    desc='The rarest people of Rasen: part beast, part spirit, part human. Many sects treat Kitsune as trickster spirits rather than a race.',
                    heritage='heritage_kitsune', heritage_name='Kitsune', language='language_zenshin', language_name='Zenshin',
                    ethos='ethos_courtly', martial_custom='martial_custom_equal', name_list='name_list_zenshin', ethnicity='asian',
                    traditions=['tradition_xenophilic', 'tradition_hit_and_run', 'tradition_poetry'], **STEPPE_GFX),
}

NAME_LISTS = {
    'name_list_zenshin': dict(
        label='Zenshin',
        male=['Masaru', 'Kenji', 'Haruto', 'Ryo', 'Daichi', 'Kosuke', 'Shuichi', 'Takeshi', 'Hiroshi', 'Kaito', 'Ren', 'Sora', 'Yuto', 'Jiro',
              'Isamu', 'Kazuki', 'Makoto', 'Noboru', 'Riku', 'Satoshi', 'Tadashi', 'Tetsuo', 'Yasuo', 'Akio', 'Daisuke', 'Goro', 'Hayato',
              'Ichiro', 'Katsu', 'Minoru', 'Osamu', 'Ryota', 'Shin', 'Tomoya', 'Yoshiro', 'Kagerou', 'Jun', 'Mao', 'Raiden', 'Hideo'],
        female=['Sakura', 'Misuka', 'Rin', 'Aiko', 'Hana', 'Yuki', 'Mei', 'Haruka', 'Kaede', 'Natsuki', 'Ayame', 'Chiyo', 'Emi', 'Fuyu',
                'Hikari', 'Izumi', 'Kana', 'Mariko', 'Nanami', 'Reiko', 'Sayuri', 'Tomoe', 'Yoko', 'Akane', 'Asuka', 'Kiyomi', 'Midori',
                'Noriko', 'Shizuka', 'Umeko', 'Amane', 'Kasumi', 'Ran', 'Suzume'],
        dynasties=['Ryuuzan', 'Ozaki', 'Nakamoto', 'Takeda', 'Kurosawa', 'Hoshino', 'Ishida', 'Kiba', 'Fujiwara', 'Arakawa', 'Shimizu',
                   'Kagemori', 'Amatsu', 'Tsukimura', 'Hayashi', 'Matsuda', 'Okami', 'Sanada', 'Yamabe', 'Inoue', 'Mizuhara', 'Kanzaki']),
    'name_list_lunargoth': dict(
        label='Lunargoth',
        male=['Rufus', 'Alaric', 'Theodoric', 'Gunther', 'Ulfric', 'Wulfgar', 'Ansgar', 'Hildebrand', 'Roderic', 'Athanaric', 'Fritigern',
              'Gaiseric', 'Odvar', 'Sigeric', 'Thrasamund', 'Brannoc'],
        female=['Brunhild', 'Amalasuntha', 'Gisela', 'Hilda', 'Ingunde', 'Matasuntha', 'Ragnhild', 'Sigrun', 'Theodelinda', 'Ulfhild', 'Wiliburga'],
        dynasties=['Amaling', 'Balthing', 'Frostmark', 'Hrothing', 'Wintermantle', 'Icewarden', 'Northvale', 'Greycloak']),
    'name_list_cathayan': dict(
        label='Cathayan',
        male=['Wenyao', 'Taio', 'Chu', 'Bo', 'Wei', 'Jian', 'Liang', 'Hao', 'Zhen', 'Ming', 'Rui', 'Feng', 'Guang', 'Yong', 'Kun', 'Lei',
              'Shen', 'Tao', 'Xun', 'Yi', 'Zhao', 'Heng', 'Jun', 'Long'],
        female=['Lan', 'Mei', 'Xiu', 'Lian', 'Hua', 'Jing', 'Ling', 'Yun', 'Qing', 'Ruolan', 'Shu', 'Ting', 'Wen', 'Xia', 'Yan', 'Zhi', 'Desdemona'],
        dynasties=['Lan', 'Dou', 'Bai', 'Zhou', 'Su', 'Hou', 'Long', 'Xuan', 'Ming', 'Jin', 'Luo', 'Yao']),
}

FAITHS = {
    'ancestral_rites': dict(religion='rasen_ancestral_religion', name='Ancestral Rites', adjective='Ancestral', adherent='Rite-keeper', adherents='Rite-keepers',
                            colour=(190, 50, 50), icon='custom_faith_1', holy_sites=['rasen_leyline_nexus', 'rasen_bladed_forge', 'rasen_rabbit_trial_valley'],
                            tenets=['tenet_ancestor_worship', 'tenet_ritual_hospitality', 'tenet_struggle_submission'],
                            desc='Kowtow before the graves of your ancestors and thank them for your birth. The common faith of Imperial Rasen honours lineage, caste and the Exalted Council.'),
    'celestial_order': dict(religion='rasen_ancestral_religion', name='Celestial Order', adjective='Celestial', adherent='Scholar', adherents='Scholars',
                            colour=(220, 180, 40), icon='custom_faith_2', holy_sites=['rasen_leyline_nexus', 'rasen_mystic_spires'],
                            tenets=['tenet_esotericism', 'tenet_ancestor_worship', 'tenet_ritual_celebrations'],
                            desc='The Mystic Lands hold that heaven is a hierarchy of knowledge, and that those who know more stand closer to it.'),
    'veiled_ancestors': dict(religion='rasen_ancestral_religion', name='Veiled Ancestors', adjective='Veiled', adherent='Veiled One', adherents='Veiled Ones',
                             colour=(130, 60, 150), icon='custom_faith_3', holy_sites=['rasen_leyline_nexus', 'rasen_cursed_hollow'],
                             tenets=['tenet_sacred_shadows', 'tenet_ancestor_worship', 'tenet_esotericism'],
                             desc='In the Cursed Lands, the ancestors are honoured in secret, and results matter more than how they are achieved.'),
    'devanic_temple': dict(religion='rasen_devanic_religion', name='Devanic Temple', adjective='Devanic', adherent='Devanite', adherents='Devanites',
                           colour=(70, 130, 210), icon='custom_faith_4', holy_sites=['rasen_devanic_temple', 'rasen_sacred_sanctum', 'rasen_heavenly_storm_gate'],
                           tenets=['tenet_monasticism', 'tenet_unrelenting_faith', 'tenet_mendicant_preachers'],
                           desc='Monks and shrinemaidens of the Devanic Temple have banished Fiends from the mortal world for all of written history. They value respectability, mercy to the innocent and retribution upon the wicked.'),
    'shugendo': dict(religion='rasen_devanic_religion', name='Shugendō', adjective='Shugendō', adherent='Yamabushi', adherents='Yamabushi',
                     colour=(150, 200, 230), icon='custom_faith_5', holy_sites=['rasen_devanic_temple', 'rasen_dead_mountain', 'rasen_ice_front'],
                     tenets=['tenet_asceticism', 'tenet_sanctity_of_nature', 'tenet_esotericism'],
                     desc='Born of meditations across mountains that no longer exist, Shugendō binds one of nature\'s elements to the spirit.'),
    'wild_pacts': dict(religion='rasen_wild_religion', name='Pacts of the Wild Gods', adjective='Wild-Pact', adherent='Pact-bearer', adherents='Pact-bearers',
                       colour=(60, 140, 50), icon='custom_faith_6', holy_sites=['rasen_burning_forest', 'rasen_wild_arena'],
                       tenets=['tenet_warmonger', 'tenet_sanctity_of_nature', 'tenet_ritual_celebrations'],
                       desc='The Wild Lands bargain with beast-gods such as Gazhurra. Only the strong are worth a god\'s attention.'),
}

COMMON_DOCTRINES = ['doctrine_gender_equal', 'doctrine_pluralism_pluralistic', 'doctrine_theocracy_lay_clergy', 'doctrine_divorce_allowed',
                    'doctrine_bastardry_legitimization', 'doctrine_consanguinity_cousins', 'doctrine_homosexuality_shunned',
                    'doctrine_adultery_men_shunned', 'doctrine_adultery_women_shunned', 'doctrine_kinslaying_close_kin_crime',
                    'doctrine_deviancy_shunned', 'doctrine_witchcraft_shunned', 'doctrine_clerical_gender_either',
                    'doctrine_clerical_marriage_allowed', 'doctrine_clerical_succession_temporal_appointment']

RELIGIONS = {
    'rasen_ancestral_religion': dict(
        name='Rasenese Rites', adjective='Rasenese', adherent='Rasenese', adherents='Rasenese', family='rf_eastern',
        graphical_faith='dharmic_gfx', piety_icon_group='eastern', holy_order='rasen_holy_order_archons', holy_order_name='Archons of the Council',
        doctrines=['doctrine_no_head', 'doctrine_concubines', 'doctrine_clerical_function_taxation', *COMMON_DOCTRINES],
        virtues=['just', 'brave', 'diligent'], sins=['craven', 'arbitrary', 'lazy'], good_gods=['the Ancestors', 'the Leyline Mother'],
        evil_gods=['the Calamity'], desc='The ancestral faiths of Imperial Rasen, centred on lineage and the leylines of Azuma Honsha.',
        loc=dict(HighGodName='the Ancestors', god_pronoun=('they', 'their', 'them', 'themselves'), DevilName='the Calamity',
                 DeathDeityName='the Grave-Keeper', WitchGodName='the Fox Spirit', priest='shrine-keeper', bishop='rite-master',
                 devotee='ancestor-keeper', paradise='the Halls of the Ancestors', hell='the Hungry Dark', realm='the Ancestral Heaven',
                 holy_war='Righteous Campaign', temple='shrine', ReligiousSymbol='ancestral tablet', ReligiousText='Book of Lineages',
                 ReligiousHeadName='Exalted Council', ReligiousHeadTitleName='Exalt', PantheonTerm='the Ancestors')),
    'rasen_devanic_religion': dict(
        name='Devanic Faith', adjective='Devanic', adherent='Devanite', adherents='Devanites', family='rf_eastern',
        graphical_faith='dharmic_gfx', piety_icon_group='eastern', holy_order='rasen_holy_order_fiend_hunters', holy_order_name='Fiend-Hunters of the Temple',
        doctrines=['doctrine_spiritual_head', 'doctrine_monogamy', 'doctrine_clerical_function_alms_and_pacification', *COMMON_DOCTRINES],
        virtues=['compassionate', 'humble', 'temperate'], sins=['callous', 'arrogant', 'gluttonous'], good_gods=['the Saints', 'the Deva'],
        evil_gods=['the Fiends', 'the Wights'], desc='The faith of the Devanic Temple and its Saints, partnered with the Sacred Lands and sworn against the Fiends.',
        loc=dict(HighGodName='the Deva', god_pronoun=('it', 'its', 'it', 'itself'), DevilName='the Fiend-King', DeathDeityName='the Pale Saint',
                 WitchGodName='the Fiend-Witch', priest='monk', bishop='Saint', devotee='shrinemaiden', paradise='the Pure Land',
                 hell='the Fiend Realms', realm='the Pure Land', holy_war='Exorcism Crusade', temple='temple', ReligiousSymbol='prayer talisman',
                 ReligiousText='Devanic Sutras', ReligiousHeadName='Devanic Temple', ReligiousHeadTitleName='High Saint', PantheonTerm='the Saints')),
    'rasen_wild_religion': dict(
        name='Wild Gods', adjective='Wild', adherent='Pact-bearer', adherents='Pact-bearers', family='rf_pagan', pagan_roots=True,
        graphical_faith='pagan_gfx', piety_icon_group='pagan', holy_order='rasen_holy_order_beast_riders', holy_order_name='Beast-Riders of Gazhurra',
        doctrines=['doctrine_no_head', 'doctrine_polygamy', 'doctrine_clerical_function_recruitment', *COMMON_DOCTRINES],
        virtues=['brave', 'wrathful', 'strong'], sins=['craven', 'content', 'weak'], good_gods=['Gazhurra', 'the Great Wolf'],
        evil_gods=['the Ice Demons'], desc='Pacts with the beast-gods of the Wild Lands, who answer only to strength.',
        loc=dict(HighGodName='Gazhurra', god_pronoun=('she', 'her', 'her', 'herself'), DevilName='the Ice Demon', DeathDeityName='the Bone Wolf',
                 WitchGodName='the Moon Fox', priest='beast-speaker', bishop='pact-elder', devotee='hunter', paradise='the Endless Hunt',
                 hell='the Cold Pit', realm='the Endless Hunt', holy_war='Great Hunt', temple='arena', ReligiousSymbol='fang totem',
                 ReligiousText='Oral Pacts', ReligiousHeadName='Wild Exalt', ReligiousHeadTitleName='Pact-Lord', PantheonTerm='the Wild Gods')),
}

RELIGION_LOC_KEYS = [
    'HighGodName', 'HighGodNamePossessive', 'HighGodNameSheHe', 'HighGodHerselfHimself', 'HighGodHerHis', 'HighGodNameAlternate',
    'HighGodNameAlternatePossessive', 'CreatorName', 'CreatorNamePossessive', 'CreatorSheHe', 'CreatorHerHis', 'CreatorHerHim',
    'HealthGodName', 'HealthGodNamePossessive', 'HealthGodSheHe', 'HealthGodHerHis', 'HealthGodHerHim',
    'FertilityGodName', 'FertilityGodNamePossessive', 'FertilityGodSheHe', 'FertilityGodHerHis', 'FertilityGodHerHim',
    'WealthGodName', 'WealthGodNamePossessive', 'WealthGodSheHe', 'WealthGodHerHis', 'WealthGodHerHim',
    'HouseholdGodName', 'HouseholdGodNamePossessive', 'HouseholdGodSheHe', 'HouseholdGodHerHis', 'HouseholdGodHerHim',
    'FateGodName', 'FateGodNamePossessive', 'FateGodSheHe', 'FateGodHerHis', 'FateGodHerHim',
    'KnowledgeGodName', 'KnowledgeGodNamePossessive', 'KnowledgeGodSheHe', 'KnowledgeGodHerHis', 'KnowledgeGodHerHim',
    'WarGodName', 'WarGodNamePossessive', 'WarGodSheHe', 'WarGodHerHis', 'WarGodHerHim',
    'TricksterGodName', 'TricksterGodNamePossessive', 'TricksterGodSheHe', 'TricksterGodHerHis', 'TricksterGodHerHim',
    'NightGodName', 'NightGodNamePossessive', 'NightGodSheHe', 'NightGodHerHis', 'NightGodHerHim',
    'WaterGodName', 'WaterGodNamePossessive', 'WaterGodSheHe', 'WaterGodHerHis', 'WaterGodHerHim',
    'PantheonTerm', 'PantheonTermHasHave',
    'DevilName', 'DevilNamePossessive', 'DevilSheHe', 'DevilHerHis', 'DevilHerselfHimself',
    'HouseOfWorship', 'HouseOfWorshipPlural', 'ReligiousSymbol', 'ReligiousText', 'ReligiousHeadName', 'ReligiousHeadTitleName',
    'DevoteeMale', 'DevoteeMalePlural', 'DevoteeFemale', 'DevoteeFemalePlural', 'DevoteeNeuter', 'DevoteeNeuterPlural',
    'PriestMale', 'PriestMalePlural', 'PriestFemale', 'PriestFemalePlural', 'PriestNeuter', 'PriestNeuterPlural', 'AltPriestTermPlural',
    'BishopMale', 'BishopMalePlural', 'BishopFemale', 'BishopFemalePlural', 'BishopNeuter', 'BishopNeuterPlural',
    'DivineRealm', 'DivineRealm2', 'DivineRealm3', 'PositiveAfterLife', 'PositiveAfterLife2', 'PositiveAfterLife3',
    'NegativeAfterLife', 'NegativeAfterLife2', 'NegativeAfterLife3',
    'DeathDeityName', 'DeathDeityNamePossessive', 'DeathDeitySheHe', 'DeathDeityHerHis', 'DeathDeityHerHim',
    'WitchGodName', 'WitchGodHerHis', 'WitchGodSheHe', 'WitchGodHerHim', 'WitchGodMistressMaster', 'WitchGodMotherFather',
    'GHWName', 'GHWNamePlural',
]

# Holy sites: a named barony, or the n-th county of a kingdom.
HOLY_SITES = {
    'rasen_devanic_temple': dict(name='The Devanic Temple', barony='b_devanic_temple', modifier={'monthly_piety_gain_mult': 0.1}),
    'rasen_dead_mountain': dict(name='Dead Mountain', barony='b_dead_mountain', modifier={'stress_loss_mult': 0.1}),
    'rasen_rabbit_trial_valley': dict(name='Rabbit Trial Valley', barony='b_rabbit_trial_valley', modifier={'prowess': 2}),
    'rasen_burning_forest': dict(name='The Burning Forest', barony='b_burning_forest', modifier={'prowess': 2}),
    'rasen_leyline_nexus': dict(name='The Leyline Nexus', barony='b_azuma', modifier={'monthly_prestige_gain_mult': 0.1}),
    'rasen_heavenly_storm_gate': dict(name='The Heavenly Storm Gate', barony='-', kingdom='k_azuma', county_index=7, modifier={'learning': 1}),
    'rasen_bladed_forge': dict(name='The Crimson Forge', barony='-', kingdom='k_bladed', modifier={'martial': 1}),
    'rasen_mystic_spires': dict(name='The Flying Spires', barony='-', kingdom='k_mystic', modifier={'learning': 1}),
    'rasen_cursed_hollow': dict(name='The Veiled Hollow', barony='-', kingdom='k_cursed', modifier={'intrigue': 1}),
    'rasen_sacred_sanctum': dict(name='The Saints\' Sanctum', barony='-', kingdom='k_sacred', modifier={'diplomacy': 1}),
    'rasen_ice_front': dict(name='The Ice Front', barony='-', kingdom='k_outer_north', county_index=3, modifier={'prowess': 2}),
    'rasen_wild_arena': dict(name='The Great Arena', barony='-', kingdom='k_wild', modifier={'martial': 1}),
}

# Peoples by region: culture and faith weights per duchy.
REGION_PEOPLES = {
    'outer_west': dict(cultures={'zenshin': 8, 'oni': 1, 'cathayan': 1}, faiths={'ancestral_rites': 7, 'devanic_temple': 3}),
    'outer_north': dict(cultures={'lunargoth': 6, 'zenshin': 3, 'oni': 1}, faiths={'shugendo': 6, 'ancestral_rites': 4}),
    'outer_east': dict(cultures={'zenshin': 6, 'oni': 3, 'kitsune': 1}, faiths={'ancestral_rites': 8, 'devanic_temple': 2}),
    'outer_south': dict(cultures={'zenshin': 7, 'cathayan': 3}, faiths={'ancestral_rites': 8, 'devanic_temple': 2}),
    'sacred': dict(cultures={'cathayan': 5, 'zenshin': 5}, faiths={'devanic_temple': 8, 'shugendo': 2}),
    'mystic': dict(cultures={'cathayan': 9, 'kitsune': 1}, faiths={'celestial_order': 1}),
    'cursed': dict(cultures={'zenshin': 7, 'kitsune': 3}, faiths={'veiled_ancestors': 1}),
    'bladed': dict(cultures={'zenshin': 1}, faiths={'ancestral_rites': 1}),
    'wild': dict(cultures={'yokai': 5, 'oni': 3, 'zenshin': 2}, faiths={'wild_pacts': 1}),
    'azuma': dict(cultures={'zenshin': 9, 'cathayan': 1}, faiths={'ancestral_rites': 1}),
}

# The five Exalts of the Exalted Council, plus the Council's High Steward on Azuma Honsha.
EXALTS = {
    'bladed': dict(name='Masaru', house='Ryuuzan', culture='zenshin', faith='ancestral_rites', age=62, traits=('honest', 'just'),
                   desc='The Bladed Exalt. Father of twenty-three sons and one daughter, master of Akakiru and of a nation of samurai.'),
    'wild': dict(name='Tetsuo', house='Kiba', culture='yokai', faith='wild_pacts', age=55, traits=('wrathful', 'ambitious'),
                 desc='The Wild Exalt (generated). A warrior-king who rules by strength and has taken an interest in the Trials at Nanhou.'),
    'cursed': dict(name='Kagerou', house='Ozaki', culture='zenshin', faith='veiled_ancestors', age=58, traits=('deceitful', 'patient'),
                   desc='The Cursed Exalt (generated), of the great Ozaki shinobi clan. Their strike teams already move among the Trials.'),
    'mystic': dict(name='Wenyao', house='Lan', culture='cathayan', faith='celestial_order', age=70, traits=('diligent', 'arrogant'),
                   desc='The Mystic Exalt (generated). A master of Kiihakai who rules from cities of endless daylight and flying towers.'),
    'sacred': dict(name='Amane', house='Hoshino', culture='cathayan', faith='devanic_temple', age=66, female=True, traits=('compassionate', 'zealous'),
                   desc='The Sacred Exalt (generated), a Saint of the Devanic Temple who values mercy to the innocent and retribution upon the wicked.'),
    'azuma': dict(name='Haruka', house='Amatsu', culture='zenshin', faith='ancestral_rites', age=60, female=True, traits=('calm', 'just'),
                  desc='High Steward of the Exalted Council (generated). Azuma Honsha has had no Emperor for centuries; the Steward keeps the capital for the Council.'),
}

# Canonical Outer West magistrates hold the duchy containing their county.
CANON_HOLDERS = {
    'c_thunderfall': dict(name='Khan', house='Khan', age=57, cultivator=2, traits=('just', 'patient')),
    'c_nanhou': dict(name='Fuyu', house='Fuyu', age=49, female=True, cultivator=2, traits=('arrogant', 'diligent')),
}

BOOKMARK = dict(
    group_name='Imperial Rasen',
    name='The Heavenly Ascension Trials',
    desc='The war in the north is won, and the Exalted Council has chosen the Outer West town of Nanhou to host the next Heavenly Ascension Trials. Ten thousand young martial artists converge on it, and the five Exalts watch for those worth claiming.',
)

# Natural aura raises the Mortal Limit (AP). Outer lands are weakest; the leylines meet at Azuma Honsha.
MORTAL_LIMIT_BONUS = {'world_rasen_azuma': 1700, 'world_rasen_inner': 700}

# Imperial Rasen is an old, organised empire: cultures begin in the Early Medieval era.
INNOVATIONS = ['innovation_motte', 'innovation_catapult', 'innovation_barracks', 'innovation_mustering_grounds',
               'innovation_bannus', 'innovation_development_01', 'innovation_currency_01', 'innovation_gavelkind',
               'innovation_crop_rotation', 'innovation_city_planning', 'innovation_casus_belli', 'innovation_ledger',
               'innovation_manorialism']

# The Divine General of the North: supreme commander of the Northern Army, who calls himself
# Emperor of all ten Provinces; the Council calls him its northern steward. (Name generated.)
DIVINE_GENERAL = dict(name='Theodoric', house='Wintermantle', culture='lunargoth', faith='shugendo', age=64,
                      traits=('brave', 'diligent'))
