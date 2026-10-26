from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Race:
    key: str
    label: str
    ability_bonuses: dict
    size: str = "Medium"
    speed: int = 30
    darkvision: int = 0
    resistances: tuple = ()
    skills: tuple = ()
    languages: tuple = ("Common",)
    traits: tuple = ()
    detail: str = ""


RACES = {
    "human": Race(
        "human", "Human", {"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1},
        languages=("Common", "one extra"),
        traits=(("Versatile", "+1 to every ability score; an extra language."),),
        detail="+1 to all abilities; adaptable and ambitious."),
    "dwarf": Race(
        "dwarf", "Dwarf", {"con": 2, "wis": 1}, speed=25, darkvision=60,
        resistances=("poison",),
        traits=(("Dwarven Resilience", "Advantage vs poison; resist poison damage."),
                ("Stonecunning", "Expertise on History checks about stonework."),
                ("Combat Training", "Proficient with axes and hammers.")),
        detail="+2 CON, +1 WIS (Hill Dwarf); hardy, dark-sighted, poison-tough."),
    "elf": Race(
        "elf", "Elf", {"dex": 2, "int": 1}, speed=30, darkvision=60,
        skills=("perception",),
        traits=(("Keen Senses", "Proficiency in Perception."),
                ("Fey Ancestry", "Advantage vs charm; magic can't put you to sleep."),
                ("Trance", "Meditate 4 hours instead of sleeping 8.")),
        detail="+2 DEX, +1 INT (High Elf); keen-eyed, charm-resistant, ever-watchful."),
    "halfling": Race(
        "halfling", "Halfling", {"dex": 2, "cha": 1}, size="Small", speed=25,
        traits=(("Lucky", "Reroll a natural 1 on an attack, check, or save."),
                ("Brave", "Advantage on saves against being frightened."),
                ("Halfling Nimbleness", "Move through the space of larger creatures."),
                ("Naturally Stealthy", "Hide behind creatures larger than you (Lightfoot).")),
        detail="+2 DEX, +1 CHA; small, lucky, brave, and hard to pin down."),
    "tiefling": Race(
        "tiefling", "Tiefling", {"cha": 2, "int": 1}, speed=30, darkvision=60,
        resistances=("fire",), languages=("Common", "Infernal"),
        traits=(("Hellish Resistance", "Resistance to fire damage."),
                ("Infernal Legacy", "Know the thaumaturgy cantrip; gain infernal spells as you level."),
                ("Fiendish Heritage", "Marked by an infernal bloodline -- horns, tail, unsettling eyes.")),
        detail="+2 CHA, +1 INT; infernal blood, fire-resistant, dark-sighted."),
    "dragonborn": Race(
        "dragonborn", "Dragonborn", {"str": 2, "cha": 1}, speed=30,
        resistances=("breath-element",), languages=("Common", "Draconic"),
        traits=(("Draconic Ancestry", "Choose a dragon type; sets your breath/resistance element."),
                ("Breath Weapon", "Exhale a line or cone of elemental damage (DEX or CON save)."),
                ("Damage Resistance", "Resist the damage type of your ancestry.")),
        detail="+2 STR, +1 CHA; proud draconic blood with a breath weapon."),
    "gnome": Race(
        "gnome", "Gnome", {"int": 2, "con": 1}, size="Small", speed=25, darkvision=60,
        traits=(("Gnome Cunning", "Advantage on INT, WIS, and CHA saves vs magic."),
                ("Artificer's Lore", "Expertise on History about magic items/devices (Rock Gnome).")),
        detail="+2 INT, +1 CON; small, clever, and stubbornly magic-resistant."),
    "half_elf": Race(
        "half_elf", "Half-Elf", {"cha": 2, "dex": 1, "con": 1}, speed=30, darkvision=60,
        languages=("Common", "Elvish", "one extra"),
        traits=(("Fey Ancestry", "Advantage vs charm; immune to magical sleep."),
                ("Skill Versatility", "Proficiency in two skills of your choice (pick at the table)."),
                ("Ability Flexibility", "The +1/+1 may move to any two abilities (default DEX/CON).")),
        detail="+2 CHA and +1/+1; charming, flexible, at home in two worlds."),
    "half_orc": Race(
        "half_orc", "Half-Orc", {"str": 2, "con": 1}, speed=30, darkvision=60,
        skills=("intimidation",), languages=("Common", "Orc"),
        traits=(("Menacing", "Proficiency in Intimidation."),
                ("Relentless Endurance", "Drop to 1 HP instead of 0 once per long rest."),
                ("Savage Attacks", "Roll an extra weapon die on a melee critical hit.")),
        detail="+2 STR, +1 CON; fierce, frightening, and hard to put down."),
}

ORDER = ("human", "elf", "dwarf", "halfling", "tiefling",
         "dragonborn", "gnome", "half_elf", "half_orc")


def get(key: str) -> Race | None:
    return RACES.get((key or "").lower())
