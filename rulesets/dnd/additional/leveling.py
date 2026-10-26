from __future__ import annotations

HP_PER_LEVEL = {6: 4, 8: 5, 10: 6, 12: 7}


def _mod(score: int) -> int:
    return (score - 10) // 2


def proficiency_bonus(level: int) -> int:
    return 2 + (max(1, min(20, level)) - 1) // 4


def _step(table: dict, level: int):
    val = None
    for lvl in sorted(table):
        if level >= lvl:
            val = table[lvl]
    return val


FULL_CASTER_SLOTS = {
    1: (2,), 2: (3,), 3: (4, 2), 4: (4, 3), 5: (4, 3, 2), 6: (4, 3, 3),
    7: (4, 3, 3, 1), 8: (4, 3, 3, 2), 9: (4, 3, 3, 3, 1), 10: (4, 3, 3, 3, 2),
    11: (4, 3, 3, 3, 2, 1), 12: (4, 3, 3, 3, 2, 1), 13: (4, 3, 3, 3, 2, 1, 1),
    14: (4, 3, 3, 3, 2, 1, 1), 15: (4, 3, 3, 3, 2, 1, 1, 1), 16: (4, 3, 3, 3, 2, 1, 1, 1),
    17: (4, 3, 3, 3, 2, 1, 1, 1, 1), 18: (4, 3, 3, 3, 3, 1, 1, 1, 1),
    19: (4, 3, 3, 3, 3, 2, 1, 1, 1), 20: (4, 3, 3, 3, 3, 2, 2, 1, 1),
}
HALF_CASTER_SLOTS = {
    1: (), 2: (2,), 3: (3,), 4: (3,), 5: (4, 2), 6: (4, 2), 7: (4, 3), 8: (4, 3),
    9: (4, 3, 2), 10: (4, 3, 2), 11: (4, 3, 3), 12: (4, 3, 3), 13: (4, 3, 3, 1),
    14: (4, 3, 3, 1), 15: (4, 3, 3, 2), 16: (4, 3, 3, 2), 17: (4, 3, 3, 3, 1),
    18: (4, 3, 3, 3, 1), 19: (4, 3, 3, 3, 2), 20: (4, 3, 3, 3, 2),
}
WARLOCK_PACT = {
    1: (1, 1), 2: (2, 1), 3: (2, 2), 4: (2, 2), 5: (2, 3), 6: (2, 3), 7: (2, 4),
    8: (2, 4), 9: (2, 5), 10: (2, 5), 11: (3, 5), 12: (3, 5), 13: (3, 5), 14: (3, 5),
    15: (3, 5), 16: (3, 5), 17: (4, 5), 18: (4, 5), 19: (4, 5), 20: (4, 5),
}


def caster_type(spellcasting) -> str | None:
    if not spellcasting:
        return None
    kind = spellcasting[0]
    if kind in ("full", "prepared"):
        return "full"
    return kind


def spell_slots(ctype: str | None, level: int):
    if ctype == "full":
        return {f"level_{i+1}": n for i, n in enumerate(FULL_CASTER_SLOTS[level])}
    if ctype == "half":
        return {f"level_{i+1}": n for i, n in enumerate(HALF_CASTER_SLOTS[level])}
    if ctype == "pact":
        num, lvl = WARLOCK_PACT[level]
        return {"pact_slots": num, "pact_slot_level": lvl}
    return {}


ASI_LEVELS = {
    "fighter": (4, 6, 8, 12, 14, 16, 19),
    "rogue": (4, 8, 10, 12, 16, 19),
}
_DEFAULT_ASI = (4, 8, 12, 16, 19)


def asi_levels(class_key: str) -> tuple:
    return ASI_LEVELS.get(class_key, _DEFAULT_ASI)


def asi_count(class_key: str, level: int) -> int:
    return sum(1 for l in asi_levels(class_key) if level >= l)


A = ("Ability Score Improvement", "Raise one ability by 2 or two by 1 (or take a feat).")
SUB = lambda n="": ("Subclass feature", f"Your subclass grants a feature{(' at this level' if not n else '')}.")

CLASS_FEATURES = {
    "barbarian": {
        1: [("Rage", "Bonus-action fury: bonus damage, resistance to bludgeoning/piercing/slashing."),
            ("Unarmored Defense", "AC = 10 + DEX + CON unarmored.")],
        2: [("Reckless Attack", "Advantage on STR melee, but attacks against you have advantage."),
            ("Danger Sense", "Advantage on DEX saves vs effects you can see.")],
        3: [("Primal Path", "Choose a path (Berserker, Totem, ...)."), SUB()],
        4: [A], 5: [("Extra Attack", "Attack twice per Attack action."),
                    ("Fast Movement", "+10 ft speed unarmored.")],
        6: [SUB()], 7: [("Feral Instinct", "Advantage on initiative; act while surprised if you rage.")],
        8: [A], 9: [("Brutal Critical", "Roll one extra weapon die on a crit.")],
        10: [SUB()], 11: [("Relentless Rage", "Drop to 1 HP instead of 0 (DC rises each time).")],
        12: [A], 13: [("Brutal Critical", "Two extra weapon dice on a crit.")],
        14: [SUB()], 15: [("Persistent Rage", "Your rage ends early only if you choose.")],
        16: [A], 17: [("Brutal Critical", "Three extra weapon dice on a crit.")],
        18: [("Indomitable Might", "Minimum STR check result equals your STR score.")],
        19: [A], 20: [("Primal Champion", "STR and CON +4 (max 24).")],
    },
    "bard": {
        1: [("Bardic Inspiration", "Bonus action: give an ally a die to add to a roll (d6)."),
            ("Spellcasting", "Full CHA caster.")],
        2: [("Jack of All Trades", "Half proficiency on non-proficient checks."),
            ("Song of Rest", "Allies heal extra on a short rest (d6).")],
        3: [("Bard College", "Choose a College (Lore, Valor, ...)."), ("Expertise", "Double proficiency on two skills.")],
        4: [A], 5: [("Bardic Inspiration (d8)", "Inspiration die improves; Font of Inspiration (regain on short rest).")],
        6: [("Countercharm", "Allies get advantage vs charm/fright while you perform."), SUB()],
        7: [], 8: [A], 9: [("Song of Rest (d8)", "Short-rest healing improves.")],
        10: [("Bardic Inspiration (d10)", "Die improves."), ("Expertise", "Two more skills."),
             ("Magical Secrets", "Learn two spells from any class.")],
        11: [], 12: [A], 13: [("Song of Rest (d10)", "Improves.")],
        14: [("Magical Secrets", "Two more any-class spells."), SUB()],
        15: [("Bardic Inspiration (d12)", "Die improves.")],
        16: [A], 17: [("Song of Rest (d12)", "Improves.")],
        18: [("Magical Secrets", "Two more any-class spells.")],
        19: [A], 20: [("Superior Inspiration", "Regain an Inspiration use when you roll initiative with none.")],
    },
    "cleric": {
        1: [("Spellcasting", "Prepared WIS divine caster."), ("Divine Domain", "Choose a domain; bonus spells/powers."), SUB()],
        2: [("Channel Divinity", "Turn Undead and a domain effect (1/rest)."), ("Turn Undead", "Frighten/drive off undead.")],
        3: [], 4: [A], 5: [("Destroy Undead (CR 1/2)", "Turned weak undead are destroyed.")],
        6: [("Channel Divinity (2/rest)", "Extra use."), SUB()],
        7: [], 8: [A, ("Destroy Undead (CR 1)", "Threshold rises."), SUB()],
        9: [], 10: [("Divine Intervention", "Call on your deity for direct aid.")],
        11: [("Destroy Undead (CR 2)", "Threshold rises.")], 12: [A],
        13: [], 14: [("Destroy Undead (CR 3)", "Threshold rises.")],
        15: [], 16: [A], 17: [("Destroy Undead (CR 4)", "Threshold rises."), SUB()],
        18: [("Channel Divinity (3/rest)", "Extra use.")],
        19: [A], 20: [("Divine Intervention Improvement", "Your deity's aid succeeds automatically.")],
    },
    "druid": {
        1: [("Druidic", "The secret druid tongue."), ("Spellcasting", "Prepared WIS nature caster.")],
        2: [("Wild Shape", "Transform into beasts you've seen."), ("Druid Circle", "Choose a circle."), SUB()],
        3: [], 4: [A, ("Wild Shape (CR 1/2)", "Better beast forms; can swim.")],
        5: [], 6: [SUB()], 7: [], 8: [A, ("Wild Shape (CR 1)", "Better forms; can fly.")],
        9: [], 10: [SUB()], 11: [], 12: [A], 13: [], 14: [SUB()], 15: [], 16: [A],
        17: [], 18: [("Timeless Body", "Age slowly."), ("Beast Spells", "Cast in Wild Shape.")],
        19: [A], 20: [("Archdruid", "Unlimited Wild Shape; ignore some spell components.")],
    },
    "fighter": {
        1: [("Fighting Style", "A combat specialty (Defense, Dueling, Archery, ...)."),
            ("Second Wind", "Bonus action: heal 1d10 + level (1/rest).")],
        2: [("Action Surge", "Take one extra action (1/rest).")],
        3: [("Martial Archetype", "Choose an archetype (Champion, Battle Master, ...)."), SUB()],
        4: [A], 5: [("Extra Attack", "Attack twice per Attack action.")],
        6: [A], 7: [SUB()], 8: [A], 9: [("Indomitable", "Reroll a failed save (1/rest).")],
        10: [SUB()], 11: [("Extra Attack (2)", "Attack three times.")], 12: [A],
        13: [("Indomitable (2)", "Two uses.")], 14: [A], 15: [SUB()], 16: [A],
        17: [("Action Surge (2)", "Two uses."), ("Indomitable (3)", "Three uses.")],
        18: [SUB()], 19: [A], 20: [("Extra Attack (3)", "Attack four times.")],
    },
    "monk": {
        1: [("Unarmored Defense", "AC = 10 + DEX + WIS."), ("Martial Arts", "DEX unarmed strikes; a bonus strike (d4).")],
        2: [("Ki", "A pool of focus (= level): Flurry, Patient Defense, Step of the Wind."),
            ("Unarmored Movement", "+10 ft speed unarmored.")],
        3: [("Monastic Tradition", "Choose a tradition."), ("Deflect Missiles", "Reduce/redirect ranged weapon damage.")],
        4: [A, ("Slow Fall", "Reduce falling damage as a reaction.")],
        5: [("Extra Attack", "Attack twice."), ("Stunning Strike", "Spend ki to stun on a hit.")],
        6: [("Ki-Empowered Strikes", "Unarmed strikes count as magical."), SUB()],
        7: [("Evasion", "Take no damage on a successful DEX save."), ("Stillness of Mind", "End charm/fright on yourself.")],
        8: [A], 9: [("Unarmored Movement Improvement", "Run on walls/water.")],
        10: [("Purity of Body", "Immune to disease and poison.")],
        11: [SUB()], 12: [A], 13: [("Tongue of the Sun and Moon", "Understand and be understood by all.")],
        14: [("Diamond Soul", "Proficiency in all saves; reroll fails with ki.")],
        15: [("Timeless Body", "No aging effects; need no food/water.")],
        16: [A], 17: [SUB()], 18: [("Empty Body", "Spend ki for invisibility; cast Astral Projection.")],
        19: [A], 20: [("Perfect Self", "Regain 4 ki when you have none and roll initiative.")],
    },
    "paladin": {
        1: [("Divine Sense", "Detect celestials, fiends, and undead nearby."),
            ("Lay on Hands", "A pool of healing equal to 5 x level.")],
        2: [("Fighting Style", "A combat specialty."), ("Spellcasting", "Half CHA caster."),
            ("Divine Smite", "Spend a slot to add radiant damage on a hit.")],
        3: [("Divine Health", "Immune to disease."), ("Sacred Oath", "Choose an oath; Channel Divinity."), SUB()],
        4: [A], 5: [("Extra Attack", "Attack twice.")],
        6: [("Aura of Protection", "You and nearby allies add your CHA to saves.")],
        7: [SUB()], 8: [A], 9: [],
        10: [("Aura of Courage", "You and nearby allies can't be frightened.")],
        11: [("Improved Divine Smite", "All melee hits deal +1d8 radiant.")], 12: [A],
        13: [], 14: [("Cleansing Touch", "End spells on yourself or others.")],
        15: [SUB()], 16: [A], 17: [], 18: [("Aura Improvements", "Auras reach 30 ft.")],
        19: [A], 20: [("Sacred Oath capstone", "Your oath's ultimate power.")],
    },
    "ranger": {
        1: [("Favored Enemy", "Advantage to track and recall lore about a chosen foe."),
            ("Natural Explorer", "Mastery of a favored terrain.")],
        2: [("Fighting Style", "A combat specialty."), ("Spellcasting", "Half WIS caster.")],
        3: [("Ranger Archetype", "Choose an archetype (Hunter, Beast Master, ...)."), ("Primeval Awareness", "Sense creature types nearby."), SUB()],
        4: [A], 5: [("Extra Attack", "Attack twice.")],
        6: [("Favored Enemy/Terrain +", "Additional foe and terrain.")], 7: [SUB()],
        8: [A, ("Land's Stride", "Ignore difficult natural terrain.")], 9: [],
        10: [("Natural Explorer +", "Another terrain."), ("Hide in Plain Sight", "Camouflage yourself.")],
        11: [SUB()], 12: [A], 13: [], 14: [("Favored Enemy +", "Another foe."), ("Vanish", "Hide as a bonus action; can't be tracked.")],
        15: [SUB()], 16: [A], 17: [], 18: [("Feral Senses", "Fight unseen attackers; sense invisibles.")],
        19: [A], 20: [("Foe Slayer", "Add WIS to an attack or damage roll vs a favored enemy.")],
    },
    "rogue": {
        1: [("Expertise", "Double proficiency on two skills."),
            ("Sneak Attack", "Extra d6 damage with advantage or a flanking ally (1d6)."),
            ("Thieves' Cant", "A secret code of signs and slang.")],
        2: [("Cunning Action", "Dash, Disengage, or Hide as a bonus action.")],
        3: [("Roguish Archetype", "Choose an archetype (Thief, Assassin, Arcane Trickster, ...)."), SUB()],
        4: [A], 5: [("Uncanny Dodge", "Halve damage from one attacker as a reaction.")],
        6: [("Expertise", "Two more skills.")], 7: [("Evasion", "Take no damage on a successful DEX save.")],
        8: [A], 9: [SUB()], 10: [A], 11: [("Reliable Talent", "Treat a d20 of 9 or lower as 10 on proficient checks.")],
        12: [A], 13: [SUB()], 14: [("Blindsense", "Sense hidden/invisible creatures within 10 ft.")],
        15: [("Slippery Mind", "Proficiency in Wisdom saves.")],
        16: [A], 17: [SUB()], 18: [("Elusive", "No attack roll has advantage against you.")],
        19: [A], 20: [("Stroke of Luck", "Turn a miss into a hit or a failed check into a 20 (1/rest).")],
    },
    "sorcerer": {
        1: [("Spellcasting", "Full CHA caster -- innate."), ("Sorcerous Origin", "The source of your power."), SUB()],
        2: [("Font of Magic", "Sorcery Points (= level).")],
        3: [("Metamagic", "Bend spells with two Metamagic options.")],
        4: [A], 5: [], 6: [SUB()], 7: [], 8: [A], 9: [],
        10: [("Metamagic", "A third option.")], 11: [], 12: [A], 13: [], 14: [SUB()],
        15: [], 16: [A], 17: [("Metamagic", "A fourth option.")], 18: [SUB()],
        19: [A], 20: [("Sorcerous Restoration", "Regain 4 sorcery points on a short rest.")],
    },
    "warlock": {
        1: [("Otherworldly Patron", "A pact with a Fiend, Fey, or Great Old One."),
            ("Pact Magic", "Few but always-max-level slots, refreshed on a short rest.")],
        2: [("Eldritch Invocations", "Permanent magical enhancements (2 known).")],
        3: [("Pact Boon", "Blade, Chain, or Tome.")],
        4: [A], 5: [], 6: [SUB()], 7: [], 8: [A], 9: [],
        10: [SUB()], 11: [("Mystic Arcanum (6th)", "Cast one 6th-level spell per long rest.")],
        12: [A], 13: [("Mystic Arcanum (7th)", "One 7th-level spell per long rest.")],
        14: [SUB()], 15: [("Mystic Arcanum (8th)", "One 8th-level spell per long rest.")],
        16: [A], 17: [("Mystic Arcanum (9th)", "One 9th-level spell per long rest.")],
        18: [], 19: [A], 20: [("Eldritch Master", "Regain all Pact slots once per long rest by entreating your patron.")],
    },
    "wizard": {
        1: [("Spellcasting", "Prepared INT caster from a spellbook."), ("Arcane Recovery", "Recover some slots on a short rest.")],
        2: [("Arcane Tradition", "A school of magic (Evocation, Abjuration, ...)."), SUB()],
        3: [], 4: [A], 5: [], 6: [SUB()], 7: [], 8: [A], 9: [], 10: [SUB()],
        11: [], 12: [A], 13: [], 14: [SUB()], 15: [], 16: [A], 17: [],
        18: [("Spell Mastery", "Cast one 1st- and one 2nd-level spell at will.")],
        19: [A], 20: [("Signature Spells", "Always have two 3rd-level spells prepared, free once per rest.")],
    },
}


def cumulative_features(class_key: str, level: int) -> list:
    table = CLASS_FEATURES.get(class_key, {})
    out = []
    for lvl in range(1, level + 1):
        out.extend(table.get(lvl, []))
    return out


def class_resources(class_key: str, level: int, abilities: dict) -> dict:
    r: dict = {}
    if class_key == "barbarian":
        r["rages"] = _step({1: 2, 3: 3, 6: 4, 12: 5, 17: 6, 20: "unlimited"}, level)
        r["rage_damage"] = 2 if level < 9 else (3 if level < 16 else 4)
        if level >= 5:
            r["attacks_per_action"] = 2
    elif class_key == "monk":
        if level >= 2:
            r["ki_points"] = level
        r["martial_arts_die"] = _step({1: "1d4", 5: "1d6", 11: "1d8", 17: "1d10"}, level)
        r["unarmored_movement"] = _step({2: 10, 6: 15, 10: 20, 14: 25, 18: 30}, level)
        if level >= 5:
            r["attacks_per_action"] = 2
    elif class_key == "rogue":
        r["sneak_attack"] = f"{(level + 1) // 2}d6"
    elif class_key == "fighter":
        r["attacks_per_action"] = 4 if level >= 20 else (3 if level >= 11 else (2 if level >= 5 else 1))
        r["action_surge_uses"] = 2 if level >= 17 else (1 if level >= 2 else 0)
        r["indomitable_uses"] = 3 if level >= 17 else (2 if level >= 13 else (1 if level >= 9 else 0))
    elif class_key == "paladin":
        r["lay_on_hands_pool"] = 5 * level
        if level >= 5:
            r["attacks_per_action"] = 2
        r["aura_range"] = 30 if level >= 18 else (10 if level >= 6 else 0)
    elif class_key == "ranger":
        if level >= 5:
            r["attacks_per_action"] = 2
    elif class_key == "bard":
        r["bardic_inspiration_die"] = _step({1: "1d6", 5: "1d8", 10: "1d10", 15: "1d12"}, level)
        r["inspiration_uses"] = max(1, _mod(abilities.get("cha", 10)))
    elif class_key == "cleric":
        r["channel_divinity_uses"] = 3 if level >= 18 else (2 if level >= 6 else (1 if level >= 2 else 0))
        if level >= 5:
            r["destroy_undead_cr"] = _step({5: "1/2", 8: "1", 11: "2", 14: "3", 17: "4"}, level)
    elif class_key == "druid":
        if level >= 2:
            r["wild_shape_uses"] = 2
            r["wild_shape_cr"] = _step({2: "1/4", 4: "1/2", 8: "1"}, level)
    elif class_key == "sorcerer":
        if level >= 2:
            r["sorcery_points"] = level
        r["metamagic_known"] = 4 if level >= 17 else (3 if level >= 10 else (2 if level >= 3 else 0))
    elif class_key == "warlock":
        r["invocations_known"] = _step({2: 2, 5: 3, 7: 4, 9: 5, 12: 6, 15: 7, 18: 8}, level) or 0
        r["eldritch_blast_beams"] = 4 if level >= 17 else (3 if level >= 11 else (2 if level >= 5 else 1))
        r["mystic_arcanum"] = [lvl for lvl, need in ((6, 11), (7, 13), (8, 15), (9, 17)) if level >= need]
    elif class_key == "wizard":
        r["arcane_recovery_slots"] = max(1, (level + 1) // 2)
    return r


def max_hp(hit_die: int, level: int, con_mod: int) -> int:
    return max(1, hit_die + con_mod + (level - 1) * (HP_PER_LEVEL[hit_die] + con_mod))


SPENDABLE_RESOURCES = {
    "rages", "ki_points", "action_surge_uses", "indomitable_uses", "lay_on_hands_pool",
    "inspiration_uses", "channel_divinity_uses", "wild_shape_uses", "sorcery_points",
    "arcane_recovery_slots",
}
SHORT_REST_RESOURCES = {
    "ki_points", "action_surge_uses", "channel_divinity_uses", "wild_shape_uses",
    "inspiration_uses", "arcane_recovery_slots",
}


def spendable_pools(class_resources: dict) -> dict:
    return {k: v for k, v in (class_resources or {}).items()
            if k in SPENDABLE_RESOURCES and isinstance(v, int)}


def derive_level(class_key: str, level: int, hit_die: int, spellcasting, abilities: dict) -> dict:
    level = max(1, min(20, level))
    ctype = caster_type(spellcasting)
    out = {
        "level": level,
        "proficiency_bonus": proficiency_bonus(level),
        "max_hp": max_hp(hit_die, level, _mod(abilities.get("con", 10))),
        "class_features": [n for n, _ in cumulative_features(class_key, level)],
        "feature_detail": cumulative_features(class_key, level),
        "spell_slots": spell_slots(ctype, level),
        "class_resources": class_resources(class_key, level, abilities),
        "asi_pending": asi_count(class_key, level),
    }
    return out


def progression(class_key: str, hit_die: int, spellcasting, abilities: dict | None = None) -> list:
    abilities = abilities or {"con": 14, "cha": 14, "wis": 14}
    rows = []
    for lvl in range(1, 21):
        d = derive_level(class_key, lvl, hit_die, spellcasting, abilities)
        rows.append({"level": lvl, "proficiency_bonus": d["proficiency_bonus"],
                     "features": [n for n, _ in CLASS_FEATURES.get(class_key, {}).get(lvl, [])],
                     "spell_slots": d["spell_slots"], "resources": d["class_resources"]})
    return rows


FULL_CASTERS = frozenset({"bard", "cleric", "druid", "sorcerer", "wizard"})
HALF_CASTERS = frozenset({"paladin", "ranger"})


def caster_fraction(class_key: str, subclass: str | None = None) -> float:
    if class_key in FULL_CASTERS:
        return 1.0
    if class_key in HALF_CASTERS:
        return 0.5
    return 0.0


def _slotted_casters(classes: list) -> list:
    return [c for c in classes
            if c.get("class_key") in FULL_CASTERS or c.get("class_key") in HALF_CASTERS]


def multiclass_caster_level(classes: list) -> int:
    full = half = 0
    for c in classes:
        ck = c.get("class_key", "")
        lv = int(c.get("level", 0))
        if ck in FULL_CASTERS:
            full += lv
        elif ck in HALF_CASTERS:
            half += lv
    return full + half // 2


def multiclass_spell_slots(classes: list) -> dict:
    casters = _slotted_casters(classes)
    if not casters:
        return {}
    if len(casters) == 1:
        c = casters[0]
        ctype = "full" if c.get("class_key") in FULL_CASTERS else "half"
        return spell_slots(ctype, max(1, min(20, int(c.get("level", 1)))))
    cl = multiclass_caster_level(classes)
    return spell_slots("full", min(20, cl)) if cl >= 1 else {}


def pact_slots_for(classes: list) -> dict:
    for c in classes:
        if c.get("class_key") == "warlock":
            return spell_slots("pact", max(1, min(20, int(c.get("level", 1)))))
    return {}


def multiclass_max_hp(classes: list, con_mod: int) -> int:
    total, first = 0, True
    for c in classes:
        die = int(c.get("hit_die", 8))
        for _ in range(int(c.get("level", 0))):
            if first:
                total += die + con_mod
                first = False
            else:
                total += HP_PER_LEVEL.get(die, die // 2) + con_mod
    return max(1, total)


def feature_union(classes: list) -> list:
    out, seen = [], set()
    for c in classes:
        for name, _ in cumulative_features(c.get("class_key", ""), int(c.get("level", 0))):
            if name not in seen:
                seen.add(name)
                out.append(name)
    return out


def merge_class_resources(classes: list, abilities: dict) -> dict:
    merged: dict = {}
    for c in classes:
        r = class_resources(c.get("class_key", ""), int(c.get("level", 0)), abilities)
        for k, v in r.items():
            if k == "attacks_per_action":
                merged[k] = max(merged.get(k, 1), v if isinstance(v, int) else 1)
            else:
                merged[k] = v
    merged.setdefault("attacks_per_action", 1)
    return merged


def total_level(classes: list) -> int:
    return min(20, sum(int(c.get("level", 0)) for c in classes))
