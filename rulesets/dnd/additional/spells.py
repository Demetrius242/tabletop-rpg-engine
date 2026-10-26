from __future__ import annotations

from dataclasses import dataclass

BARD, CLERIC, DRUID, PALADIN, RANGER, SORCERER, WARLOCK, WIZARD = (
    "bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard")
CASTERS = (BARD, CLERIC, DRUID, PALADIN, RANGER, SORCERER, WARLOCK, WIZARD)


@dataclass(frozen=True)
class Spell:
    key: str
    name: str
    level: int
    school: str
    classes: tuple
    desc: str


def _s(name, level, school, classes, desc):
    key = name.lower().replace(" ", "_").replace("'", "")
    return Spell(key, name, level, school, tuple(classes), desc)


_ALL = [
    _s("Fire Bolt", 0, "evocation", (SORCERER, WIZARD), "Hurl a mote of fire at a target."),
    _s("Ray of Frost", 0, "evocation", (SORCERER, WIZARD), "A frigid beam that damages and slows."),
    _s("Shocking Grasp", 0, "evocation", (SORCERER, WIZARD), "Lightning leaps from your hand; deny reactions."),
    _s("Mage Hand", 0, "conjuration", (BARD, SORCERER, WARLOCK, WIZARD), "A spectral hand manipulates objects at range."),
    _s("Prestidigitation", 0, "transmutation", (BARD, SORCERER, WARLOCK, WIZARD), "Minor sensory and cleaning tricks."),
    _s("Minor Illusion", 0, "illusion", (BARD, SORCERER, WARLOCK, WIZARD), "Create a small sound or image."),
    _s("Light", 0, "evocation", (BARD, CLERIC, SORCERER, WIZARD), "An object sheds bright light."),
    _s("Vicious Mockery", 0, "enchantment", (BARD,), "Cutting words wound and impose disadvantage."),
    _s("Sacred Flame", 0, "evocation", (CLERIC,), "Radiant flame strikes, ignoring cover (DEX save)."),
    _s("Guidance", 0, "divination", (CLERIC, DRUID), "An ally adds 1d4 to one ability check."),
    _s("Thaumaturgy", 0, "transmutation", (CLERIC,), "A minor wonder: booming voice, tremors, flickering flame."),
    _s("Druidcraft", 0, "transmutation", (DRUID,), "Small nature effects: weather hints, bloom a flower."),
    _s("Shillelagh", 0, "transmutation", (DRUID,), "Your club or staff becomes a magic weapon using WIS."),
    _s("Produce Flame", 0, "conjuration", (DRUID,), "A flame for light or to hurl at a foe."),
    _s("Eldritch Blast", 0, "evocation", (WARLOCK,), "Crackling beams of force (more beams as you level)."),
    _s("Chill Touch", 0, "necromancy", (SORCERER, WARLOCK, WIZARD), "A spectral hand harms and stops healing."),
    _s("Toll the Dead", 0, "necromancy", (CLERIC, WARLOCK, WIZARD), "A mournful bell deals necrotic damage."),
    _s("Mending", 0, "transmutation", (BARD, CLERIC, DRUID, SORCERER, WIZARD), "Repair a single break or tear."),

    _s("Cure Wounds", 1, "evocation", (BARD, CLERIC, DRUID, PALADIN, RANGER), "Heal a creature you touch."),
    _s("Healing Word", 1, "evocation", (BARD, CLERIC, DRUID), "Heal at range as a bonus action."),
    _s("Bless", 1, "enchantment", (CLERIC, PALADIN), "Allies add 1d4 to attacks and saves."),
    _s("Shield of Faith", 1, "abjuration", (CLERIC, PALADIN), "+2 AC to a creature for the duration."),
    _s("Command", 1, "enchantment", (CLERIC, PALADIN), "A one-word order a creature must obey."),
    _s("Detect Magic", 1, "divination", (BARD, CLERIC, DRUID, PALADIN, RANGER, SORCERER, WIZARD), "Sense magic auras nearby."),
    _s("Shield", 1, "abjuration", (SORCERER, WIZARD), "A reaction: +5 AC and block magic missile."),
    _s("Magic Missile", 1, "evocation", (SORCERER, WIZARD), "Darts of force that strike unerringly."),
    _s("Burning Hands", 1, "evocation", (SORCERER, WIZARD), "A cone of searing flame (DEX save)."),
    _s("Charm Person", 1, "enchantment", (BARD, DRUID, SORCERER, WARLOCK, WIZARD), "Make a humanoid regard you as friendly."),
    _s("Sleep", 1, "enchantment", (BARD, SORCERER, WIZARD), "Send weaker creatures into magical slumber."),
    _s("Thunderwave", 1, "evocation", (BARD, DRUID, SORCERER, WIZARD), "A wave of force damages and shoves."),
    _s("Faerie Fire", 1, "evocation", (BARD, DRUID), "Outline creatures; attackers gain advantage."),
    _s("Disguise Self", 1, "illusion", (BARD, SORCERER, WIZARD), "Change your appearance."),
    _s("Hex", 1, "enchantment", (WARLOCK,), "Curse a target: bonus damage and a weakened ability."),
    _s("Hunter's Mark", 1, "divination", (RANGER,), "Mark a quarry for bonus damage and easy tracking."),
    _s("Hellish Rebuke", 1, "evocation", (WARLOCK,), "A reaction: wreath your attacker in flame."),
    _s("Goodberry", 1, "transmutation", (DRUID, RANGER), "Berries that each restore a little health."),
    _s("Entangle", 1, "conjuration", (DRUID, RANGER), "Grasping weeds restrain creatures in an area."),
    _s("Fog Cloud", 1, "conjuration", (DRUID, RANGER, SORCERER, WIZARD), "A sphere of obscuring mist."),
    _s("Detect Evil and Good", 1, "divination", (CLERIC, PALADIN), "Sense aberrations, celestials, fiends, fey, elementals, undead."),
    _s("Protection from Evil and Good", 1, "abjuration", (CLERIC, PALADIN, WARLOCK, WIZARD), "Ward against the six otherworldly types."),

    _s("Misty Step", 2, "conjuration", (SORCERER, WARLOCK, WIZARD), "Teleport 30 feet as a bonus action."),
    _s("Invisibility", 2, "illusion", (BARD, SORCERER, WARLOCK, WIZARD), "A creature you touch becomes invisible."),
    _s("Hold Person", 2, "enchantment", (BARD, CLERIC, DRUID, SORCERER, WARLOCK, WIZARD), "Paralyze a humanoid (WIS save)."),
    _s("Scorching Ray", 2, "evocation", (SORCERER, WIZARD), "Three rays of fire at one or more targets."),
    _s("Spiritual Weapon", 2, "evocation", (CLERIC,), "A floating spectral weapon attacks as a bonus action."),
    _s("Lesser Restoration", 2, "abjuration", (BARD, CLERIC, DRUID, PALADIN, RANGER), "End a disease or a condition."),
    _s("Aid", 2, "abjuration", (CLERIC, PALADIN), "Raise allies' current and maximum HP."),
    _s("Web", 2, "conjuration", (SORCERER, WIZARD), "Fill an area with restraining webs."),
    _s("Mirror Image", 2, "illusion", (SORCERER, WARLOCK, WIZARD), "Duplicates that foil attacks against you."),
    _s("Suggestion", 2, "enchantment", (BARD, SORCERER, WARLOCK, WIZARD), "Magically urge a reasonable course of action."),
    _s("Moonbeam", 2, "evocation", (DRUID,), "A searing beam you can move each turn."),
    _s("Pass without Trace", 2, "abjuration", (DRUID, RANGER), "Your party gains a large bonus to stealth."),
    _s("Darkness", 2, "evocation", (SORCERER, WARLOCK, WIZARD), "Magical darkness fills a sphere."),
    _s("Enhance Ability", 2, "transmutation", (BARD, CLERIC, DRUID, SORCERER), "Grant advantage on one ability's checks."),

    _s("Fireball", 3, "evocation", (SORCERER, WIZARD), "A roaring blast of flame in a 20-ft sphere."),
    _s("Lightning Bolt", 3, "evocation", (SORCERER, WIZARD), "A stroke of lightning in a line."),
    _s("Counterspell", 3, "abjuration", (SORCERER, WARLOCK, WIZARD), "A reaction: interrupt another's spell."),
    _s("Dispel Magic", 3, "abjuration", (BARD, CLERIC, DRUID, PALADIN, SORCERER, WARLOCK, WIZARD), "End ongoing magic on a target."),
    _s("Fly", 3, "transmutation", (SORCERER, WARLOCK, WIZARD), "Grant a creature a flying speed."),
    _s("Haste", 3, "transmutation", (SORCERER, WIZARD), "Double speed, +2 AC, and an extra action."),
    _s("Revivify", 3, "necromancy", (CLERIC, PALADIN), "Return the recently dead to life."),
    _s("Mass Healing Word", 3, "evocation", (CLERIC,), "Heal several allies at range as a bonus action."),
    _s("Spirit Guardians", 3, "conjuration", (CLERIC,), "Wheeling spirits harm foes around you."),
    _s("Call Lightning", 3, "conjuration", (DRUID,), "Summon a storm cloud and call bolts down."),
    _s("Conjure Animals", 3, "conjuration", (DRUID, RANGER), "Summon fey spirits in animal form to fight."),
    _s("Hypnotic Pattern", 3, "illusion", (BARD, SORCERER, WARLOCK, WIZARD), "A twisting pattern charms and incapacitates."),
    _s("Major Image", 3, "illusion", (BARD, SORCERER, WARLOCK, WIZARD), "A detailed, lasting illusion with sound and smell."),
    _s("Vampiric Touch", 3, "necromancy", (WARLOCK, WIZARD), "Drain life and heal yourself."),

    _s("Polymorph", 4, "transmutation", (BARD, DRUID, SORCERER, WIZARD), "Transform a creature into a beast."),
    _s("Dimension Door", 4, "conjuration", (BARD, SORCERER, WARLOCK, WIZARD), "Teleport yourself and one other a long way."),
    _s("Banishment", 4, "abjuration", (CLERIC, PALADIN, SORCERER, WARLOCK, WIZARD), "Send a creature to another plane."),
    _s("Greater Invisibility", 4, "illusion", (BARD, SORCERER, WIZARD), "Invisible even while attacking or casting."),
    _s("Wall of Fire", 4, "evocation", (DRUID, SORCERER, WIZARD), "A burning wall that scorches those near it."),
    _s("Ice Storm", 4, "evocation", (DRUID, SORCERER, WIZARD), "Hail and cold batter an area."),
    _s("Guardian of Faith", 4, "conjuration", (CLERIC,), "A spectral guardian punishes foes that approach."),
    _s("Freedom of Movement", 4, "abjuration", (BARD, CLERIC, DRUID, RANGER), "Ignore restraints and difficult terrain."),

    _s("Cone of Cold", 5, "evocation", (SORCERER, WIZARD), "A blast of frigid air in a cone."),
    _s("Wall of Force", 5, "evocation", (WIZARD,), "An invisible, nearly indestructible barrier."),
    _s("Hold Monster", 5, "enchantment", (BARD, SORCERER, WARLOCK, WIZARD), "Paralyze any creature (WIS save)."),
    _s("Mass Cure Wounds", 5, "evocation", (BARD, CLERIC, DRUID), "Heal several creatures at once."),
    _s("Raise Dead", 5, "necromancy", (BARD, CLERIC, PALADIN), "Restore a dead creature to life."),
    _s("Flame Strike", 5, "evocation", (CLERIC,), "A column of divine fire (DEX save)."),
    _s("Greater Restoration", 5, "abjuration", (BARD, CLERIC, DRUID), "Undo curses, drain, and reduction."),
    _s("Commune", 5, "divination", (CLERIC,), "Ask your deity yes-or-no questions."),
    _s("Scrying", 5, "divination", (BARD, CLERIC, DRUID, WARLOCK, WIZARD), "Spy on a distant creature or place."),
    _s("Insect Plague", 5, "conjuration", (CLERIC, DRUID, SORCERER), "A swarm of biting locusts fills an area."),

    _s("Disintegrate", 6, "transmutation", (SORCERER, WIZARD), "A green ray that can reduce a target to dust."),
    _s("Chain Lightning", 6, "evocation", (SORCERER, WIZARD), "Lightning leaps from target to target."),
    _s("Heal", 6, "evocation", (CLERIC, DRUID), "A surge of positive energy fully mends a creature."),
    _s("Harm", 6, "necromancy", (CLERIC,), "Inflict grievous necrotic damage and disease."),
    _s("True Seeing", 6, "divination", (BARD, CLERIC, SORCERER, WARLOCK, WIZARD), "See through illusions and into the unseen."),
    _s("Sunbeam", 6, "evocation", (DRUID, SORCERER, WIZARD), "A beam of blinding radiant light."),
    _s("Mass Suggestion", 6, "enchantment", (BARD, SORCERER, WARLOCK, WIZARD), "Suggest a course to many at once."),

    _s("Finger of Death", 7, "necromancy", (SORCERER, WARLOCK, WIZARD), "Searing negative energy; the slain rise as zombies."),
    _s("Plane Shift", 7, "conjuration", (CLERIC, DRUID, SORCERER, WARLOCK, WIZARD), "Travel to another plane of existence."),
    _s("Teleport", 7, "conjuration", (BARD, SORCERER, WIZARD), "Instantly travel a great distance."),
    _s("Regenerate", 7, "transmutation", (BARD, CLERIC, DRUID), "Restore HP each turn and regrow lost limbs."),
    _s("Fire Storm", 7, "evocation", (CLERIC, DRUID, SORCERER), "Roaring flame engulfs an area you shape."),
    _s("Resurrection", 7, "necromancy", (BARD, CLERIC), "Return a long-dead creature to life."),

    _s("Power Word Stun", 8, "enchantment", (BARD, SORCERER, WARLOCK, WIZARD), "Stun a creature outright if its HP is low."),
    _s("Sunburst", 8, "evocation", (DRUID, SORCERER, WIZARD), "Blinding radiance bursts in a wide sphere."),
    _s("Dominate Monster", 8, "enchantment", (BARD, SORCERER, WARLOCK, WIZARD), "Seize control of a creature's actions."),
    _s("Holy Aura", 8, "abjuration", (CLERIC,), "Allies gain protection and can blind attackers."),
    _s("Earthquake", 8, "evocation", (CLERIC, DRUID, SORCERER), "The ground heaves, toppling and rending."),

    _s("Wish", 9, "conjuration", (SORCERER, WIZARD), "Alter reality within limits -- the mightiest spell."),
    _s("Meteor Swarm", 9, "evocation", (SORCERER, WIZARD), "Blazing meteors devastate a wide area."),
    _s("Power Word Kill", 9, "enchantment", (BARD, SORCERER, WARLOCK, WIZARD), "Slay a creature outright if its HP is low."),
    _s("Mass Heal", 9, "evocation", (CLERIC,), "A flood of healing restores many creatures."),
    _s("True Resurrection", 9, "necromancy", (CLERIC, DRUID), "Restore life even to the long-dead and destroyed."),
    _s("Foresight", 9, "divination", (BARD, DRUID, WARLOCK, WIZARD), "Advantage on everything; can't be surprised."),
    _s("Storm of Vengeance", 9, "conjuration", (DRUID,), "A vast storm of thunder, acid, and ice."),
]

SPELLS = {s.key: s for s in _ALL}


def get(key: str) -> Spell | None:
    return SPELLS.get((key or "").lower())


def spells_for_class(class_key: str) -> list:
    ck = (class_key or "").lower()
    return sorted((s for s in _ALL if ck in s.classes), key=lambda s: (s.level, s.name))


def by_level(class_key: str) -> dict:
    out: dict = {}
    for s in spells_for_class(class_key):
        out.setdefault(s.level, []).append(s)
    return out


def cantrips_for(class_key: str) -> list:
    return [s for s in spells_for_class(class_key) if s.level == 0]


_CANTRIPS_KNOWN = {
    BARD: {1: 2, 4: 3, 10: 4}, CLERIC: {1: 3, 4: 4, 10: 5}, DRUID: {1: 2, 4: 3, 10: 4},
    SORCERER: {1: 4, 4: 5, 10: 6}, WARLOCK: {1: 2, 4: 3, 10: 4}, WIZARD: {1: 3, 4: 4, 10: 5},
    PALADIN: {}, RANGER: {},
}
_SPELLS_KNOWN = {
    BARD: {1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14, 11: 15,
           13: 16, 14: 18, 15: 19, 17: 20, 18: 22},
    SORCERER: {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 10: 11, 11: 12,
               13: 13, 15: 14, 17: 15},
    RANGER: {2: 2, 3: 3, 5: 4, 7: 5, 9: 6, 11: 7, 13: 8, 15: 9, 17: 10, 19: 11},
    WARLOCK: {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10, 11: 11, 13: 12,
              15: 13, 17: 14, 19: 15},
}
_PREPARED = {CLERIC: ("wis", 1.0), DRUID: ("wis", 1.0), WIZARD: ("int", 1.0),
             PALADIN: ("cha", 0.5)}


def _step(table: dict, level: int):
    val = None
    for lvl in sorted(table):
        if level >= lvl:
            val = table[lvl]
    return val


def cantrips_known(class_key: str, level: int) -> int:
    return _step(_CANTRIPS_KNOWN.get(class_key, {}), level) or 0


def spells_known_or_prepared(class_key: str, level: int, ability_mod: int = 0) -> dict:
    ck = (class_key or "").lower()
    cantrips = cantrips_known(ck, level)
    if ck in _SPELLS_KNOWN:
        return {"method": "known", "spells": _step(_SPELLS_KNOWN[ck], level) or 0, "cantrips": cantrips}
    if ck in _PREPARED:
        _, mult = _PREPARED[ck]
        eff = level if mult >= 1.0 else level // 2
        return {"method": "prepared", "spells": max(1, ability_mod + eff), "cantrips": cantrips}
    return {"method": "none", "spells": 0, "cantrips": 0}


def spell_keys_for_class(class_key: str, min_level: int = 1, max_level: int = 9) -> list:
    return [s.key for s in spells_for_class(class_key) if min_level <= s.level <= max_level]


def cantrip_keys_for_class(class_key: str) -> list:
    return [s.key for s in cantrips_for(class_key)]


def validate_selection(chosen, allowed_keys, cap: int) -> list:
    allowed = set(allowed_keys)
    seen: list = []
    for k in (chosen or ()):
        kk = (k or "").lower()
        if kk in allowed and kk not in seen:
            seen.append(kk)
    return seen[:cap]
