# Cultivation sects

Sects are persistent provincial societies. Their members can also hold secular titles. Open **Decisions → Cultivation → Consult the Sect Register** to express interest in joining a sect or manage your existing membership.

## Geography and membership

Each eligible de-jure kingdom receives one sect at its historical capital county. The kingdom does not need to exist as a held title. Titular kingdoms, titles without a populated capital, and titles sharing a province already assigned to a sect are skipped. The headquarters remains in its original province through conquest and changes of master. Existing saves initialize on the next quarterly playable-character pulse; a new game is recommended for testing.

A new sect starts with one Master, eight Upper Disciples and sixteen Lower Disciples. Recruitment can fill the ten upper and twenty lower places. All members are adult cultivators. A mortal who passes admission awakens as a cultivator. Joining preserves an existing foundation, style and elements; an untrained recruit learns the sect's lineage. A cultivator belongs to one sect at a time. Leaving clears contribution and merit and prevents rejoining for one year.

The geographic policy is isolated in `ac_sect_kingdom_eligible_trigger` and the initialization on-action. Replace that policy when the custom map is introduced, while retaining the society and province data model.

## Martial identities

These are initial templates, not unique global organizations. A kingdom name distinguishes sects sharing a template.

| Lineage | Elements | Style | Foundation |
|---|---|---|---|
| Ember Peak | Fire, Earth | Akakiru | Tiger |
| Mirror Tide | Water, Ice | Aoyusumu | Crane |
| Thunder Hoof | Storm, Wind | Kiihakai | Stallion |
| Jade Mountain | Earth, Light | Midorikatai | Ox |
| Veiled Moon | Darkness, Ice | Kurokonton | Snake |
| Dawn Lotus | Light, Water | Aoyusumu | Dragon |
| Ashen Blade | Fire, Darkness | Akakiru | Wolf |
| Sky Palm | Wind, Storm | Midorikatai | Monkey |

## Provincial estate

The **Sect Estate** screen displays the headquarters, treasury, construction, roster, contribution, merit and relationships. Estate management is also available through the ledger's event menu.

This is a custom province-bound estate with its own buildings and inheritance. It is not a native government domicile or a barony title. CK3's government-bound domicile system cannot give every existing ruler an additional independently inherited estate without changing their government or title structure. The society owns this estate, allowing its master to remain a feudal ruler, administrative ruler or unlanded character.

Buildings have three levels. Each upgrade costs 100 × the new level in sect gold and takes 180 days, completing on the next monthly maintenance check. Only one building can be under construction. The treasury starts at 300, receives 60 annually and gains mission proceeds and donations. Annual maintenance caps accumulated reserves at 2,000.

| Building | Benefit |
|---|---|
| Cultivation Hall | 20 Cultivation lifestyle XP per level annually |
| Alchemy Pavilion | Unlocks medicinal pills in the exchange |
| Martial Training Ground | Power Core XP per level annually; battle strength |
| Scripture Library | 20 Cultivation lifestyle XP per level annually; manual exchange |
| Spirit Garden | Fortitude Core XP per level annually |
| Formation Hall | Agility Core XP per level annually; battle strength |

On a master's death, the available Upper Disciple with the greatest merit, prowess and learning succeeds. A Lower Disciple can succeed if no upper is available. A caretaker preserves the sect if no member can serve. The estate, treasury, construction and diplomacy remain with the society. The successor retains their secular titles. Masters can voluntarily hand over to an upper disciple. An upper disciple with 400 lifetime merit and 200 available contribution can petition an AI master, with a 60% success chance and a five-year cooldown.

## Trials

For a nonmember, **Consult the Sect Register** records interest in joining. It does not select an activity location, start a trial, or charge a hosting fee. Interested players receive announcements of trials within diplomatic reach and can review the invitation in the native activity screen, then choose whether to travel. They may withdraw interest through the register. Expressing interest through a particular master's character interaction instead requests news from that sect.

**Sect Masters host trials.** NPC masters consider opening one every three months, with a 30% random chance when a Lower Disciple place is available or an eligible disciple has requested promotion to a vacant Upper Disciple place. This schedule runs independently of player interest. A sect has a one-year trial cooldown and one activity or pending activity plan at a time. A player who becomes Sect Master can host through **Activities → Sect Trial**; ordinary disciples and applicants cannot host it.

The sect treasury pays 50 gold when a trial is created. Applicants do not pay a hosting fee. All three phases use the same permanent headquarters, selected once by a player Master or automatically by the NPC master's planner. Native invitations and travel remain in use; the examinations test understanding, martial form and spiritual control.

Admission requires 40 points and a lower-disciple vacancy. Promotion requires 55 points, a vacancy among upper disciples, a promotion request and 150 contribution. Candidates compete by examination score for available places. Promotions are resolved first, freeing lower-disciple places for admission. The fee is charged when the examination begins. An interrupted or invalid promotion trial refunds it once. A completed failed examination consumes the fee. Candidates have a one-year cooldown after a completed trial. A successful upper disciple can learn another sect element while respecting the mod's two-element limit.

Native AI planning needs a ruler controller, so an unlanded master can use a ruler member, the ruler at the headquarters, or an available ruler in that realm or kingdom to arrange the activity. This also works when a player personally owns the headquarters. Once the activity exists, its actual host is transferred to the Sect Master. The society retains its buildings, membership and treasury. A request can be deferred by the ruler's other activity plans; an unfulfilled plan expires after 90 days so the master can try again.

## Missions and contribution

The ledger's mission board creates native task contracts, assigns the disciple as taker and resolves the contract after its assignment period. These are timed commissions without an automatic travel route. One mission can be active per disciple. The timer retains the exact contract, so abandoning an assignment and starting another cannot claim an old reward.

| Mission | Duration | Main skill | Success contribution |
|---|---:|---|---:|
| Patrol the Sect Roads | 90 days | Prowess | 50 |
| Gather Spiritual Herbs | 90 days | Learning | 50 |
| Recover a Lost Manual | 120 days | Intrigue | 70 |
| Settle a Local Dispute | 60 days | Diplomacy | 40 |
| Aid the Local Villages | 90 days | Stewardship | 50 |
| Guard a Sect Delegation | 120 days | Martial | 70 |

Contribution and Sect Merit are saved separately on each member; they do not use the native Merit currency. Contribution is spendable. Sect Merit records contribution earned during the current membership and supports succession. Spending contribution does not reduce Sect Merit. Both totals appear in the Sect Register; the estate screen shows contribution and its roster lists merit. Missions have skill-based success chances, cultivation benefits, failure consequences and cooldowns. Leaving cancels the active commission.

| Exchange | Contribution | Requirement and result |
|---|---:|---|
| Medicinal pill | 50 | Alchemy Pavilion; consume through a decision for stress relief, Fortitude XP and six months of improved health; six-month use cooldown |
| Manual study | 75 | Scripture Library; 150 Cultivation lifestyle XP; six-month cooldown |
| Stipend | 50 | 40 gold transferred from the sect treasury |

## Relationships, battle and joint training

Alliances and rivalries link societies, so they survive a master's succession. Masters negotiate through character interactions or the ledger's neighboring-sect menu. An alliance replaces a rivalry; declaring rivalry ends an alliance. NPC sects occasionally form relationships with neighboring kingdoms' sects.

A master may challenge a rival sect to battle. The clash resolves after 30 days on monthly maintenance, using available disciples' prowess, buildings, allied support and joint-training preparation. Winners earn contribution and Power XP, and take up to 75 gold from the defeated treasury. Participants risk nonfatal wounds. Both sects receive a two-year battle cooldown. An ally of both sides remains neutral. These are group sect clashes, without territorial conquest or the separate single-combat system.

**Joint Sect Training** costs 75 gold and has a two-year cooldown. It invites the host sect and allied disciples for two phases at the host's headquarters. Completing it alongside an actual allied attendee grants 30 contribution, 100 Cultivation lifestyle XP, 5 Power Core XP, +2 prowess for two years and a temporary formation advantage. Attendance from a former ally does not qualify.

## Development and validation

`tools/build_sect_content.py` generates repeated identities, estate upgrades, contracts and localization. Lifecycle, activities, diplomacy and their event choices remain hand-authored. Balance values live in `common/script_values/ac_sect_values.txt`.

Run the repository checks with `python -m unittest discover -s tools -p "test_*.py"`. Generate with `python tools/build_sect_content.py`; verify generated content with `--check`.

`AuraClash/tests/ac_sect_tests.txt` contains native CK3 integration scenarios. The tests deliberately alter England's, Scotland's, Denmark's, Bohemia's and Bavaria's sects, a master and a ruler. `tools/prepare_sect_engine_checks.py` prepares an isolated user folder and a QA-only startup overlay. Launch with the command it prints, then unpause the disposable game so the AI planner and delayed checks can run. The overlay is never enabled in the normal installed mod. Its log distinguishes actual PASS and FAIL conditions. Activity requests are asynchronous; the complete suite uses this staged harness rather than a single immediate console call. Individual scenarios can also be invoked with `scripted_tests <scenario_name>` after their prerequisites are established. Use `--master-ui` for a separate player Master fixture: open Activities, plan a Sect Trial, select the Welsh headquarters once and start it. Its delayed assertion checks the actual host and headquarters after creation.

The design references the installed CK3 1.20.1.1 examination activities, administrative estate rules, task contracts and story cycles. [Monks and Mystics v1.5.2](https://steamcommunity.com/sharedfiles/filedetails/?id=3786025000) informed the society concept through its public description; no code or assets from that mod are included.

Verified against the installed CK3 1.20.1.1 build: 65 repository checks and 28 native assertions passed, plus two player Master planner assertions. The native run includes actual owner death, ruler succession, native contracts, activity creation, a full ranked admission trial and completed allied training. The estate screen, interest registration, invitation flow, player Master activity planner and mission board were inspected in-game. Player hosting was started after selecting the headquarters once. The event override generator also accepts 1.20.1.1: all 143 referenced native event blocks are unchanged from the reviewed 1.20.1 versions. Long-campaign balance and multiplayer still need broader testing.
