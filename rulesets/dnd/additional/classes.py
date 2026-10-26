from __future__ import annotations

from dataclasses import dataclass

ALL_SKILLS = (
    "athletics", "acrobatics", "sleight_of_hand", "stealth", "arcana", "history",
    "investigation", "nature", "religion", "animal_handling", "insight", "medicine",
    "perception", "survival", "deception", "intimidation", "performance", "persuasion",
)


@dataclass(frozen=True)
class CharClass:
    key: str
    label: str
    hit_die: int
    primary: tuple
    saving_throws: tuple
    attack_ability: str
    weapon: tuple
    ac_base: int
    ac_adds_dex: bool
    skill_list: tuple
    skill_choices: int
    armor: str = ""
    reach: str = "melee"
    spellcasting: tuple | None = None
    features: tuple = ()
    detail: str = ""


CLASSES = {
    "barbarian": CharClass(
        "barbarian", "Barbarian", 12, ("str",), ("str", "con"), "str", ("greataxe", "1d12"),
        ac_base=13, ac_adds_dex=True, armor="Unarmored Defense (10 + DEX + CON)",
        skill_list=("animal_handling", "athletics", "intimidation", "nature", "perception", "survival"),
        skill_choices=2,
        features=(("Rage", "Bonus-action fury: bonus melee damage, resistance to physical damage."),
                  ("Unarmored Defense", "AC = 10 + DEX mod + CON mod when not wearing armor.")),
        detail="d12 HP, raging Strength; the unarmored brawler."),
    "bard": CharClass(
        "bard", "Bard", 8, ("cha",), ("dex", "cha"), "dex", ("rapier", "1d8"),
        ac_base=12, ac_adds_dex=True, armor="Light armor",
        skill_list=ALL_SKILLS, skill_choices=3,
        spellcasting=("full", "cha"),
        features=(("Bardic Inspiration", "Bonus action: give an ally a d6 to add to a roll."),
                  ("Spellcasting", "Full CHA caster drawing on the College's repertoire."),
                  ("Jack of All Trades", "Half proficiency to non-proficient checks (L2).")),
        detail="d8 HP, CHA magic and inspiration; the versatile face."),
    "cleric": CharClass(
        "cleric", "Cleric", 8, ("wis",), ("wis", "cha"), "wis", ("mace", "1d6"),
        ac_base=16, ac_adds_dex=False, armor="Chain mail (heavy)",
        skill_list=("history", "insight", "medicine", "persuasion", "religion"), skill_choices=2,
        spellcasting=("prepared", "wis"),
        features=(("Spellcasting", "Prepared WIS divine caster."),
                  ("Divine Domain", "A domain (Life, War, ...) granting bonus spells and powers."),
                  ("Channel Divinity", "Turn Undead and a domain effect (L2).")),
        detail="d8 HP, WIS faith and heavy armor; the divine support."),
    "druid": CharClass(
        "druid", "Druid", 8, ("wis",), ("int", "wis"), "wis", ("quarterstaff", "1d6"),
        ac_base=13, ac_adds_dex=True, armor="Leather (no metal armor)",
        skill_list=("arcana", "animal_handling", "insight", "medicine", "nature",
                    "perception", "religion", "survival"), skill_choices=2,
        spellcasting=("prepared", "wis"),
        features=(("Druidic", "The secret tongue of druids."),
                  ("Spellcasting", "Prepared WIS nature caster."),
                  ("Wild Shape", "Transform into beasts you've seen (L2).")),
        detail="d8 HP, WIS nature magic; shapeshifter and healer."),
    "fighter": CharClass(
        "fighter", "Fighter", 10, ("str", "dex"), ("str", "con"), "str", ("longsword", "1d8"),
        ac_base=16, ac_adds_dex=False, armor="Chain mail (heavy)",
        skill_list=("acrobatics", "animal_handling", "athletics", "history", "insight",
                    "intimidation", "perception", "survival"), skill_choices=2,
        features=(("Fighting Style", "A combat specialty (Defense, Dueling, Archery, ...)."),
                  ("Second Wind", "Bonus action: heal 1d10 + level, once per rest."),
                  ("Action Surge", "Take an extra action on your turn (L2).")),
        detail="d10 HP, martial mastery and heavy armor; steel and discipline."),
    "monk": CharClass(
        "monk", "Monk", 8, ("dex", "wis"), ("str", "dex"), "dex", ("unarmed/shortsword", "1d6"),
        ac_base=13, ac_adds_dex=True, armor="Unarmored Defense (10 + DEX + WIS)",
        skill_list=("acrobatics", "athletics", "history", "insight", "religion", "stealth"),
        skill_choices=2,
        features=(("Unarmored Defense", "AC = 10 + DEX mod + WIS mod when unarmored."),
                  ("Martial Arts", "Use DEX for unarmed strikes; a bonus unarmed strike."),
                  ("Ki", "A pool of focus fueling Flurry, Patient Defense, Step of the Wind (L2).")),
        detail="d8 HP, DEX & WIS; the unarmored martial artist."),
    "paladin": CharClass(
        "paladin", "Paladin", 10, ("str", "cha"), ("wis", "cha"), "str", ("longsword", "1d8"),
        ac_base=18, ac_adds_dex=False, armor="Plate & shield (heavy)",
        skill_list=("athletics", "insight", "intimidation", "medicine", "persuasion", "religion"),
        skill_choices=2,
        spellcasting=("half", "cha"),
        features=(("Divine Sense", "Detect celestials, fiends, and undead nearby."),
                  ("Lay on Hands", "A pool of healing equal to 5 x level."),
                  ("Divine Smite", "Spend a spell slot to add radiant damage on a hit (L2).")),
        detail="d10 HP, STR & CHA, half-caster; the holy warrior."),
    "ranger": CharClass(
        "ranger", "Ranger", 10, ("dex", "wis"), ("str", "dex"), "dex", ("longbow", "1d8"),
        ac_base=13, ac_adds_dex=True, armor="Leather (light)", reach="ranged",
        skill_list=("animal_handling", "athletics", "insight", "investigation", "nature",
                    "perception", "stealth", "survival"), skill_choices=3,
        spellcasting=("half", "wis"),
        features=(("Favored Enemy", "Advantage to track and recall lore about a chosen foe type."),
                  ("Natural Explorer", "Mastery of a favored terrain; tireless travel."),
                  ("Spellcasting", "Half WIS nature caster from L2.")),
        detail="d10 HP, DEX & WIS, half-caster; the wilderness hunter."),
    "rogue": CharClass(
        "rogue", "Rogue", 8, ("dex",), ("dex", "int"), "dex", ("shortsword", "1d6"),
        ac_base=12, ac_adds_dex=True, armor="Leather (light)",
        skill_list=("acrobatics", "athletics", "deception", "insight", "intimidation",
                    "investigation", "perception", "performance", "persuasion",
                    "sleight_of_hand", "stealth"), skill_choices=4,
        features=(("Expertise", "Double proficiency on two chosen skills."),
                  ("Sneak Attack", "Extra damage when you have advantage or a flanking ally."),
                  ("Thieves' Cant", "A secret code of signs and slang."),
                  ("Cunning Action", "Dash, Disengage, or Hide as a bonus action (L2).")),
        detail="d8 HP, DEX and guile; expertise, stealth, and the killing strike."),
    "sorcerer": CharClass(
        "sorcerer", "Sorcerer", 6, ("cha",), ("con", "cha"), "cha", ("fire bolt", "1d10"),
        ac_base=12, ac_adds_dex=True, armor="Unarmored (mage armor)", reach="ranged",
        skill_list=("arcana", "deception", "insight", "intimidation", "persuasion", "religion"),
        skill_choices=2,
        spellcasting=("full", "cha"),
        features=(("Spellcasting", "Full CHA caster -- innate, not studied."),
                  ("Sorcerous Origin", "The source of your power (Draconic, Wild Magic, ...)."),
                  ("Font of Magic", "Sorcery Points to bend spells via Metamagic (L2).")),
        detail="d6 HP, innate CHA magic; raw arcane power."),
    "warlock": CharClass(
        "warlock", "Warlock", 8, ("cha",), ("wis", "cha"), "cha", ("eldritch blast", "1d10"),
        ac_base=13, ac_adds_dex=True, armor="Light armor", reach="ranged",
        skill_list=("arcana", "deception", "history", "intimidation", "investigation",
                    "nature", "religion"), skill_choices=2,
        spellcasting=("pact", "cha"),
        features=(("Otherworldly Patron", "A pact with a Fiend, Fey, or Great Old One."),
                  ("Pact Magic", "Few but always-max-level slots, refreshed on a short rest."),
                  ("Eldritch Invocations", "Permanent magical enhancements (L2).")),
        detail="d8 HP, pact CHA magic; eldritch blasts and bargains."),
    "wizard": CharClass(
        "wizard", "Wizard", 6, ("int",), ("int", "wis"), "int", ("fire bolt", "1d10"),
        ac_base=12, ac_adds_dex=True, armor="Unarmored (mage armor)", reach="ranged",
        skill_list=("arcana", "history", "insight", "investigation", "medicine", "religion"),
        skill_choices=2,
        spellcasting=("prepared", "int"),
        features=(("Spellcasting", "Prepared INT caster working from a spellbook."),
                  ("Arcane Recovery", "Recover some spell slots on a short rest."),
                  ("Arcane Tradition", "A school of magic (Evocation, Abjuration, ...) (L2).")),
        detail="d6 HP, studied INT magic; the spellbook scholar."),
}

ORDER = ("barbarian", "bard", "cleric", "druid", "fighter", "monk",
         "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard")


def get(key: str) -> CharClass | None:
    return CLASSES.get((key or "").lower())
