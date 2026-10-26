from __future__ import annotations

SUBCLASS_LEVEL = {
    "cleric": 1, "sorcerer": 1, "warlock": 1,
    "druid": 2, "wizard": 2,
    "barbarian": 3, "bard": 3, "fighter": 3, "monk": 3,
    "paladin": 3, "ranger": 3, "rogue": 3,
}

SUBCLASS_NOUN = {
    "barbarian": "Primal Path", "bard": "Bard College", "cleric": "Divine Domain",
    "druid": "Druid Circle", "fighter": "Martial Archetype", "monk": "Monastic Tradition",
    "paladin": "Sacred Oath", "ranger": "Ranger Archetype", "rogue": "Roguish Archetype",
    "sorcerer": "Sorcerous Origin", "warlock": "Otherworldly Patron", "wizard": "Arcane Tradition",
}

SUBCLASSES = {
    "barbarian": {
        "berserker": ("Path of the Berserker", "Unbridled fury that overwhelms.", {
            3: [("Frenzy", "Rage with a bonus-action attack each turn (then exhaustion).")],
            6: [("Mindless Rage", "Can't be charmed or frightened while raging.")],
            10: [("Intimidating Presence", "Frighten a creature as an action.")],
            14: [("Retaliation", "Reaction strike against someone who damages you.")],
        }),
        "totem_warrior": ("Path of the Totem Warrior", "Spirit animals lend their power.", {
            3: [("Spirit Seeker", "Beast Sense and Speak with Animals rituals."),
                ("Totem Spirit", "Bear/Eagle/Wolf boon while raging.")],
            6: [("Aspect of the Beast", "A lasting animal gift (e.g. bear's carry, eagle's sight).")],
            10: [("Spirit Walker", "Cast Commune with Nature as a ritual.")],
            14: [("Totemic Attunement", "A combat boon by totem (bear taunt, wolf knockdown...).")],
        }),
    },
    "bard": {
        "lore": ("College of Lore", "Knowledge, cutting words, borrowed magic.", {
            3: [("Bonus Proficiencies", "Three more skill proficiencies."),
                ("Cutting Words", "Reaction: subtract a Bardic die from a foe's roll.")],
            6: [("Additional Magical Secrets", "Learn two spells from any class.")],
            14: [("Peerless Skill", "Add a Bardic die to your own ability check.")],
        }),
        "valor": ("College of Valor", "A skald who fights beside the heroes.", {
            3: [("Bonus Proficiencies", "Medium armor, shields, martial weapons."),
                ("Combat Inspiration", "Inspiration die adds to damage or AC.")],
            6: [("Extra Attack", "Attack twice per Attack action.")],
            14: [("Battle Magic", "Bonus-action weapon attack after casting a spell.")],
        }),
    },
    "cleric": {
        "life": ("Life Domain", "The pinnacle of healing magic.", {
            1: [("Bonus Proficiency", "Heavy armor."),
                ("Disciple of Life", "Healing spells restore extra HP.")],
            2: [("Channel Divinity: Preserve Life", "Distribute healing to nearby wounded.")],
            6: [("Blessed Healer", "Your healing spells also heal you.")],
            8: [("Divine Strike", "Once a turn, weapon hits deal extra radiant damage.")],
            17: [("Supreme Healing", "Healing dice roll their maximum.")],
        }),
        "war": ("War Domain", "A holy warrior at the front.", {
            1: [("Bonus Proficiencies", "Martial weapons, heavy armor."),
                ("War Priest", "Bonus-action weapon attack a few times per rest.")],
            2: [("Channel Divinity: Guided Strike", "+10 to one attack roll.")],
            6: [("Channel Divinity: War God's Blessing", "Grant +10 to an ally's attack.")],
            8: [("Divine Strike", "Once a turn, extra damage on a weapon hit.")],
            17: [("Avatar of Battle", "Resistance to nonmagical weapon damage.")],
        }),
        "light": ("Light Domain", "Radiant fire and warding flame.", {
            1: [("Bonus Cantrip & Warding Flame", "Light cantrip; reaction to impose disadvantage.")],
            2: [("Channel Divinity: Radiance of the Dawn", "Burst of radiant damage, clears magical darkness.")],
            6: [("Improved Flare", "Warding Flame can protect allies.")],
            8: [("Potent Spellcasting", "Add WIS to cantrip damage.")],
            17: [("Corona of Light", "Aura of light that hampers foes' resistance.")],
        }),
    },
    "druid": {
        "land": ("Circle of the Land", "The classic spell-rich druid.", {
            2: [("Bonus Cantrip", "An extra druid cantrip."),
                ("Natural Recovery", "Recover spell slots on a short rest."),
                ("Circle Spells", "Bonus spells keyed to a terrain.")],
            6: [("Land's Stride", "Move through difficult terrain and plants freely.")],
            10: [("Nature's Ward", "Immunity to charm/fright by elementals and fey; poison.")],
            14: [("Nature's Sanctuary", "Beasts and plants hesitate to attack you.")],
        }),
        "moon": ("Circle of the Moon", "A shapeshifting frontline brawler.", {
            2: [("Combat Wild Shape", "Wild Shape as a bonus action; spend slots to heal in form."),
                ("Circle Forms", "Transform into much tougher beasts (CR 1+).")],
            6: [("Primal Strike", "Beast attacks count as magical.")],
            10: [("Elemental Wild Shape", "Become an air/earth/fire/water elemental.")],
            14: [("Thousand Forms", "Cast Alter Self at will.")],
        }),
    },
    "fighter": {
        "champion": ("Champion", "Raw, reliable martial excellence.", {
            3: [("Improved Critical", "Your weapon attacks crit on a 19-20.")],
            7: [("Remarkable Athlete", "Half proficiency to many checks; better running jump.")],
            10: [("Additional Fighting Style", "Adopt a second Fighting Style.")],
            15: [("Superior Critical", "Your weapon attacks crit on an 18-20.")],
            18: [("Survivor", "Regain HP at the start of each turn while bloodied.")],
        }),
        "battle_master": ("Battle Master", "Tactical maneuvers and superiority dice.", {
            3: [("Combat Superiority", "Learn maneuvers; a pool of superiority dice (d8)."),
                ("Student of War", "One artisan's tool proficiency.")],
            7: [("Know Your Enemy", "Study a creature to learn its relative strengths.")],
            10: [("Improved Combat Superiority", "Superiority dice become d10.")],
            15: [("Relentless", "Regain a superiority die when you have none in initiative.")],
            18: [("Improved Combat Superiority", "Superiority dice become d12.")],
        }),
        "eldritch_knight": ("Eldritch Knight", "A fighter woven with wizard magic.", {
            3: [("Spellcasting", "Cast wizard spells (abjuration/evocation focus)."),
                ("Weapon Bond", "Summon a bonded weapon to your hand.")],
            7: [("War Magic", "Bonus-action weapon attack after a cantrip.")],
            10: [("Eldritch Strike", "Your hits give foes disadvantage on your next spell save.")],
            15: [("Arcane Charge", "Teleport when you Action Surge.")],
            18: [("Improved War Magic", "Bonus-action weapon attack after any spell.")],
        }),
    },
    "monk": {
        "open_hand": ("Way of the Open Hand", "The peerless unarmed master.", {
            3: [("Open Hand Technique", "Flurry strikes can knock down, push, or deny reactions.")],
            6: [("Wholeness of Body", "Heal yourself as an action once per rest.")],
            11: [("Tranquility", "Sanctuary-like calm at the end of a long rest.")],
            17: [("Quivering Palm", "Set lethal vibrations you can trigger later.")],
        }),
        "shadow": ("Way of Shadow", "A ninja of darkness and stealth.", {
            3: [("Shadow Arts", "Spend ki for darkness, silence, and shadow magic.")],
            6: [("Shadow Step", "Teleport between shadows with advantage on the next strike.")],
            11: [("Cloak of Shadows", "Become invisible in dim light or darkness.")],
            17: [("Opportunist", "Reaction strike when a creature near you is hit.")],
        }),
    },
    "paladin": {
        "devotion": ("Oath of Devotion", "The paragon of holy virtue.", {
            3: [("Channel Divinity: Sacred Weapon / Turn the Unholy", "Bless your weapon or rebuke fiends/undead.")],
            7: [("Aura of Devotion", "You and nearby allies can't be charmed.")],
            15: [("Purity of Spirit", "Always under Protection from Evil and Good.")],
            20: [("Holy Nimbus", "Become an aura of searing sunlight.")],
        }),
        "vengeance": ("Oath of Vengeance", "A relentless hunter of the wicked.", {
            3: [("Channel Divinity: Abjure Enemy / Vow of Enmity", "Frighten a foe, or hunt one with advantage.")],
            7: [("Relentless Avenger", "Move when you hit with an opportunity attack.")],
            15: [("Soul of Vengeance", "Reaction strike against your Vow of Enmity target.")],
            20: [("Avenging Angel", "Sprout wings and radiate a frightening aura.")],
        }),
    },
    "ranger": {
        "hunter": ("Hunter", "A specialist slayer of threats.", {
            3: [("Hunter's Prey", "Pick a boon: Colossus Slayer, Giant Killer, or Horde Breaker.")],
            7: [("Defensive Tactics", "Escape multiattack, evasive footwork, or steel will.")],
            11: [("Multiattack", "Volley or Whirlwind Attack against many foes.")],
            15: [("Superior Hunter's Defense", "A standout defensive reaction.")],
        }),
        "beast_master": ("Beast Master", "Bonded to a loyal animal companion.", {
            3: [("Ranger's Companion", "A beast that fights at your command.")],
            7: [("Exceptional Training", "Your beast can Dash/Disengage/Help and strike as a bonus.")],
            11: [("Bestial Fury", "Your companion attacks twice.")],
            15: [("Share Spells", "Target your companion with your self-spells.")],
        }),
    },
    "rogue": {
        "thief": ("Thief", "Nimble hands and second-story work.", {
            3: [("Fast Hands", "Use objects, tools, or Sleight of Hand as a bonus action."),
                ("Second-Story Work", "Climb at full speed; longer running jumps.")],
            9: [("Supreme Sneak", "Advantage on Stealth when you move at half speed.")],
            13: [("Use Magic Device", "Ignore class/level/race requirements on items.")],
            17: [("Thief's Reflexes", "Take two turns in the first round of combat.")],
        }),
        "assassin": ("Assassin", "Lethal to the unready.", {
            3: [("Bonus Proficiencies", "Disguise kit and poisoner's kit."),
                ("Assassinate", "Advantage on surprised foes; auto-crit against them.")],
            9: [("Infiltration Expertise", "Build a reliable false identity.")],
            13: [("Impostor", "Mimic another person's speech, writing, and behavior.")],
            17: [("Death Strike", "Double damage against a surprised target who fails a save.")],
        }),
        "arcane_trickster": ("Arcane Trickster", "A spell-thief of illusion and enchantment.", {
            3: [("Spellcasting", "Wizard spells (illusion/enchantment focus)."),
                ("Mage Hand Legerdemain", "An invisible, thieving Mage Hand.")],
            9: [("Magical Ambush", "Foes have disadvantage to save vs your spells if you're hidden.")],
            13: [("Versatile Trickster", "Use Mage Hand to gain advantage on attacks.")],
            17: [("Spell Thief", "Steal a spell cast at you for a time.")],
        }),
    },
    "sorcerer": {
        "draconic": ("Draconic Bloodline", "Dragon-blooded resilience and power.", {
            1: [("Dragon Ancestor", "A draconic heritage and damage type."),
                ("Draconic Resilience", "+1 HP per level; natural AC 13 + DEX.")],
            6: [("Elemental Affinity", "Add CHA to your ancestry's damage; spend a point to resist it.")],
            14: [("Dragon Wings", "Sprout wings and fly.")],
            18: [("Draconic Presence", "Aura of awe or fear.")],
        }),
        "wild_magic": ("Wild Magic", "Chaotic surges of raw magic.", {
            1: [("Wild Magic Surge", "Spells can spark a random magical effect."),
                ("Tides of Chaos", "Advantage once, then risk a surge.")],
            6: [("Bend Luck", "Spend a point to nudge any creature's roll.")],
            14: [("Controlled Chaos", "Roll twice on surges and pick.")],
            18: [("Spell Bombardment", "A maxed damage die explodes into another.")],
        }),
    },
    "warlock": {
        "fiend": ("The Fiend", "A pact with a lord of the Lower Planes.", {
            1: [("Dark One's Blessing", "Gain temp HP when you drop a foe."),
                ("Expanded Spells", "Fiendish bonus spells.")],
            6: [("Dark One's Own Luck", "Add a d10 to a check or save once per rest.")],
            10: [("Fiendish Resilience", "Choose a damage resistance after a rest.")],
            14: [("Hurl Through Hell", "Banish a struck foe through the hells for searing damage.")],
        }),
        "archfey": ("The Archfey", "A bargain with a fey lord or lady.", {
            1: [("Fey Presence", "Charm or frighten nearby creatures as an action."),
                ("Expanded Spells", "Fey bonus spells.")],
            6: [("Misty Escape", "Turn invisible and teleport when you take damage.")],
            10: [("Beguiling Defenses", "Immune to charm; reflect it back.")],
            14: [("Dark Delirium", "Trap a creature in a charming or frightening illusion.")],
        }),
    },
    "wizard": {
        "evocation": ("School of Evocation", "Master of raw elemental destruction.", {
            2: [("Evocation Savant", "Copy/learn evocation spells cheaply."),
                ("Sculpt Spells", "Protect allies from your own area spells.")],
            6: [("Potent Cantrip", "Cantrips deal half damage even on a miss/save.")],
            10: [("Empowered Evocation", "Add INT to one damage roll of an evocation.")],
            14: [("Overchannel", "Maximize a spell's damage, at a rising cost.")],
        }),
        "abjuration": ("School of Abjuration", "A warden of protective magic.", {
            2: [("Abjuration Savant", "Copy/learn abjuration spells cheaply."),
                ("Arcane Ward", "A rechargeable shield of force around you.")],
            6: [("Projected Ward", "Spend your ward to protect a nearby ally.")],
            10: [("Improved Abjuration", "Add PB to counterspell/dispel checks.")],
            14: [("Spell Resistance", "Advantage on saves vs spells; resistance to their damage.")],
        }),
    },
}


def subclass_level(class_key: str) -> int:
    return SUBCLASS_LEVEL.get(class_key, 3)


def subclass_noun(class_key: str) -> str:
    return SUBCLASS_NOUN.get(class_key, "Subclass")


def subclasses_for(class_key: str) -> dict:
    return {k: {"key": k, "label": v[0], "blurb": v[1]}
            for k, v in SUBCLASSES.get(class_key, {}).items()}


def has_subclasses(class_key: str) -> bool:
    return bool(SUBCLASSES.get(class_key))


def subclass_label(class_key: str, sub_key: str) -> str:
    d = SUBCLASSES.get(class_key, {}).get(sub_key)
    return d[0] if d else ""


def subclass_feature_table(class_key: str, sub_key: str) -> dict:
    d = SUBCLASSES.get(class_key, {}).get(sub_key)
    return d[2] if d else {}


def cumulative_subclass_features(class_key: str, sub_key: str, level: int) -> list:
    out = []
    for lvl in sorted(subclass_feature_table(class_key, sub_key)):
        if level >= lvl:
            out.extend(subclass_feature_table(class_key, sub_key)[lvl])
    return out


def subclass_features_at(class_key: str, sub_key: str, level: int) -> list:
    return list(subclass_feature_table(class_key, sub_key).get(level, []))
