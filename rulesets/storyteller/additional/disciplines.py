from __future__ import annotations

from dataclasses import dataclass, field

from engine.outcome import Band
from rulesets.storyteller.core.storyteller_combat import band_for_net, roll_pool


@dataclass(frozen=True)
class Power:
    discipline: str
    dots: int
    key: str
    name: str
    summary: str
    cost: int = 0
    gate: str = "self"
    target: str = "self"
    roll: tuple | None = None
    contested: bool = False
    base_difficulty: int = 6
    combat: bool = False
    effect: str = ""
    damage: int = 0


@dataclass
class PowerResult:
    ok: bool
    reason: str = ""
    success: bool = False
    band: Band | None = None
    discipline: str = ""
    power: str = ""
    blood_spent: int = 0
    cue: str = ""
    contested: bool = False
    net: int = 0
    damage_dealt: int = 0


_POWERS = [
    Power("Dominate", 1, "command", "Command the Wearied Mind",
          "A one-word command the victim must obey.", gate="eye_contact", target="other",
          roll=("manipulation", "intimidation"), contested=True, combat=True, effect="command"),
    Power("Dominate", 2, "mesmerize", "Mesmerize",
          "Plant a complex suggestion to surface later.", gate="eye_contact", target="other",
          roll=("manipulation", "subterfuge"), contested=True, effect="mesmerize"),
    Power("Dominate", 3, "forgetful_mind", "The Forgetful Mind",
          "Rewrite or erase the subject's memories.", gate="eye_contact", target="other",
          roll=("wits", "subterfuge"), contested=True, effect="forget"),
    Power("Dominate", 4, "conditioning", "Conditioning",
          "Break a subject to your will over time; ever more pliable.", gate="eye_contact",
          target="other", roll=("charisma", "intimidation"), contested=True, effect="condition"),
    Power("Dominate", 5, "possession", "Possession",
          "Drive your psyche into the subject and wear them.", gate="eye_contact",
          target="other", roll=("manipulation", "intimidation"), contested=True,
          base_difficulty=7, effect="possession"),

    Power("Obfuscate", 1, "cloak_of_shadows", "Cloak of Shadows",
          "Vanish while still, in shadow or cover.", roll=("wits", "stealth"), effect="hide"),
    Power("Obfuscate", 2, "unseen_presence", "Unseen Presence",
          "Move about wholly unnoticed.", roll=("wits", "stealth"), combat=True, effect="hide"),
    Power("Obfuscate", 3, "mask_of_a_thousand_faces", "Mask of a Thousand Faces",
          "Wear the seeming of an ordinary stranger.", roll=("manipulation", "subterfuge"),
          effect="mask"),
    Power("Obfuscate", 4, "vanish", "Vanish from the Mind's Eye",
          "Disappear even as someone stares at you.", roll=("wits", "stealth"),
          base_difficulty=7, combat=True, effect="hide"),
    Power("Obfuscate", 5, "cloak_the_gathering", "Cloak the Gathering",
          "Extend your concealment to those beside you.", roll=("wits", "stealth"),
          base_difficulty=7, combat=True, effect="hide_allies"),

    Power("Presence", 1, "awe", "Awe",
          "Draw every eye and warm every heart toward you.", gate="line_of_sight",
          roll=("charisma", "subterfuge"), base_difficulty=7, combat=True, effect="awe"),
    Power("Presence", 2, "dread_gaze", "Dread Gaze",
          "Fill one soul with paralyzing terror.", gate="line_of_sight", target="other",
          roll=("charisma", "intimidation"), contested=True, combat=True, effect="terrify"),
    Power("Presence", 3, "entrancement", "Entrancement",
          "Bind a subject as your adoring thrall.", gate="line_of_sight", target="other",
          roll=("charisma", "subterfuge"), contested=True, combat=True, effect="entrance"),
    Power("Presence", 4, "summon", "Summon",
          "Call a known subject to you from any distance.", gate="none", target="other",
          roll=("charisma", "subterfuge"), base_difficulty=7, effect="summon"),
    Power("Presence", 5, "majesty", "Majesty",
          "Become so awe-ful none dare move against you.", gate="line_of_sight",
          roll=("charisma", "intimidation"), base_difficulty=7, combat=True, effect="majesty"),

    Power("Animalism", 1, "feral_whispers", "Feral Whispers",
          "Speak with animals and call them near.", gate="none", target="animal",
          roll=("manipulation", "awareness"), effect=""),
    Power("Animalism", 2, "beckoning", "The Beckoning",
          "Summon animals of a kind from afar.", gate="none", target="animal",
          roll=("charisma", "awareness"), base_difficulty=7, effect=""),
    Power("Animalism", 3, "quell_the_beast", "Quell the Beast",
          "Smother a subject's Beast and passions.", gate="line_of_sight", target="other",
          roll=("manipulation", "intimidation"), contested=True, combat=True, effect="quell"),
    Power("Animalism", 4, "subsume_the_spirit", "Subsume the Spirit",
          "Ride an animal's body and senses.", gate="line_of_sight", target="animal",
          roll=("manipulation", "awareness"), base_difficulty=8, effect=""),
    Power("Animalism", 5, "drawing_out_the_beast", "Drawing Out the Beast",
          "Cast your frenzy into another and go calm.", gate="line_of_sight", target="other",
          roll=("manipulation", "intimidation"), contested=True, combat=True, effect="draw_out_beast"),

    Power("Protean", 1, "eyes_of_the_beast", "Eyes of the Beast",
          "See in perfect darkness with a red gaze.", combat=True, effect="darksight"),
    Power("Protean", 2, "feral_claws", "Feral Claws",
          "Grow talons that rend with aggravated fury.", cost=1, combat=True, effect="claws"),
    Power("Protean", 3, "earth_meld", "Earth Meld",
          "Sink into raw earth to rest unreachable.", cost=1, effect=""),
    Power("Protean", 4, "shape_of_the_beast", "Shape of the Beast",
          "Take the form of wolf or bat.", cost=1, combat=True, effect="beast_form"),
    Power("Protean", 5, "mist_form", "Mist Form",
          "Dissolve into mist, untouchable by blade or fist.", cost=1, combat=True, effect="mist"),

    Power("Obtenebration", 1, "shadow_play", "Shadow Play",
          "Bend ambient shadow to clutch and unnerve.", gate="line_of_sight", target="other",
          roll=("manipulation", "intimidation"), contested=True, combat=True, effect="terrify"),
    Power("Obtenebration", 2, "shroud_of_night", "Shroud of Night",
          "Vomit forth a cloud of utter darkness.", target="other", gate="line_of_sight",
          roll=("manipulation", "occult"), combat=True, effect="blind"),
    Power("Obtenebration", 3, "arms_of_the_abyss", "Arms of the Abyss",
          "Raise tentacles of living shadow to seize.", gate="line_of_sight", target="other",
          roll=("manipulation", "occult"), combat=True, effect="entangle"),
    Power("Obtenebration", 4, "black_metamorphosis", "Black Metamorphosis",
          "Sheathe yourself in razor shadow-limbs.", cost=1, combat=True, effect="shadow"),
    Power("Obtenebration", 5, "tenebrous_form", "Tenebrous Form",
          "Become a living, untouchable shadow.", cost=1, combat=True, effect="mist"),

    Power("Quietus", 1, "silence_of_death", "Silence of Death",
          "Smother all sound in a still pool of quiet.", target="other", gate="line_of_sight",
          roll=("manipulation", "stealth"), combat=True, effect="silence"),
    Power("Quietus", 2, "scorpions_touch", "Scorpion's Touch",
          "Turn your vitae to venom at a touch.", gate="line_of_sight", target="other",
          roll=("dexterity", "brawl"), contested=True, combat=True, effect="poison"),
    Power("Quietus", 3, "dagons_call", "Dagon's Call",
          "Burst a victim's blood within them, unseen.", gate="line_of_sight", target="other",
          roll=("willpower", "occult"), contested=True, combat=True, effect="damage", damage=1),
    Power("Quietus", 4, "baals_caress", "Baal's Caress",
          "Sheathe a blade in flesh-eating vitae.", cost=1, combat=True, effect="claws"),
    Power("Quietus", 5, "taste_of_death", "Taste of Death",
          "Exhale a searing cloud of caustic blood.", gate="line_of_sight", target="other",
          roll=("stamina", "occult"), combat=True, effect="damage", damage=2),

    Power("Serpentis", 1, "eyes_of_the_serpent", "The Eyes of the Serpent",
          "Hold a victim immobile with a golden stare.", gate="eye_contact", target="other",
          roll=("appearance", "intimidation"), contested=True, combat=True, effect="paralyze"),
    Power("Serpentis", 2, "tongue_of_the_asp", "The Tongue of the Asp",
          "Grow a forked tongue that flays flesh.", cost=1, combat=True, effect="claws"),
    Power("Serpentis", 3, "skin_of_the_adder", "The Skin of the Adder",
          "Take on scaled, supple serpent-hide.", cost=1, combat=True, effect="armor"),
    Power("Serpentis", 4, "form_of_the_cobra", "The Form of the Cobra",
          "Become a great black serpent.", cost=1, combat=True, effect="serpent_form"),
    Power("Serpentis", 5, "heart_of_darkness", "The Heart of Darkness",
          "Draw out and hide your own heart.", cost=1, effect="heartless"),

    Power("Vicissitude", 1, "malleable_visage", "Malleable Visage",
          "Knead your own flesh into another seeming.", roll=("intelligence", "medicine"),
          effect="disguise"),
    Power("Vicissitude", 2, "fleshcraft", "Fleshcraft",
          "Reshape another's flesh like wet clay.", gate="line_of_sight", target="other",
          roll=("intelligence", "medicine"), contested=True, combat=True, effect="poison"),
    Power("Vicissitude", 3, "bonecraft", "Bonecraft",
          "Draw bone into spurs, blades, and plate.", cost=1, combat=True, effect="bonecraft"),
    Power("Vicissitude", 4, "horrid_form", "Horrid Form",
          "Swell into a fanged, taloned war-beast.", cost=1, combat=True, effect="warform"),
    Power("Vicissitude", 5, "bloodform", "Bloodform",
          "Dissolve into a crawling sheet of blood.", cost=1, combat=True, effect="mist"),

    Power("Chimerstry", 1, "ignis_fatuus", "Ignis Fatuus",
          "Conjure a single fixed phantom sensation.", roll=("manipulation", "subterfuge"),
          effect=""),
    Power("Chimerstry", 2, "fata_morgana", "Fata Morgana",
          "Weave a rich, lasting waking dream.", roll=("manipulation", "subterfuge"),
          effect=""),
    Power("Chimerstry", 3, "apparition", "Apparition",
          "Set your illusions moving and acting.", gate="line_of_sight", target="other",
          roll=("manipulation", "subterfuge"), contested=True, combat=True, effect="confuse"),
    Power("Chimerstry", 4, "permanency", "Permanency",
          "Anchor an illusion so it lingers untended.", roll=("manipulation", "subterfuge"),
          effect=""),
    Power("Chimerstry", 5, "horrid_reality", "Horrid Reality",
          "Make a phantom so true its wounds bite.", gate="line_of_sight", target="other",
          roll=("manipulation", "subterfuge"), contested=True, combat=True, effect="damage", damage=1),

    Power("Dementation", 1, "passion", "Passion",
          "Stoke or smother a subject's emotions.", gate="line_of_sight", target="other",
          roll=("charisma", "empathy"), contested=True, effect="terrify"),
    Power("Dementation", 2, "the_haunting", "The Haunting",
          "Plague a victim with phantom torments.", gate="line_of_sight", target="other",
          roll=("manipulation", "subterfuge"), contested=True, combat=True, effect="confuse"),
    Power("Dementation", 3, "eyes_of_chaos", "Eyes of Chaos",
          "Read the mad pattern under all things.", roll=("perception", "occult"), effect=""),
    Power("Dementation", 4, "voice_of_madness", "Voice of Madness",
          "Speak words that crack the listening mind.", gate="line_of_sight", target="other",
          roll=("manipulation", "empathy"), contested=True, combat=True, effect="madden"),
    Power("Dementation", 5, "total_insanity", "Total Insanity",
          "Drown a victim in every madness at once.", gate="line_of_sight", target="other",
          roll=("manipulation", "intimidation"), contested=True, combat=True, effect="insane"),

    Power("Path of Blood", 1, "a_taste_for_blood", "A Taste for Blood",
          "Read a being's age and state from their vitae.", roll=("intelligence", "occult"),
          effect=""),
    Power("Path of Blood", 2, "blood_rage", "Blood Rage",
          "Force a vampire to spend their own vitae.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), contested=True, effect=""),
    Power("Path of Blood", 3, "blood_of_potency", "Blood of Potency",
          "Thicken your own blood toward the elders'.", roll=("intelligence", "occult"),
          effect="potent"),
    Power("Path of Blood", 4, "theft_of_vitae", "Theft of Vitae",
          "Tear blood from a victim across the room.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), contested=True, combat=True, effect="blood_drain", damage=1),
    Power("Path of Blood", 5, "cauldron_of_blood", "Cauldron of Blood",
          "Boil the blood within a victim's body.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), contested=True, combat=True, effect="damage", damage=2),

    Power("Lure of Flames", 1, "candle", "Lure of Flames (Candle)",
          "Conjure a flame the size of a candle's.", cost=1, gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="fire", damage=0),
    Power("Lure of Flames", 2, "palm_of_flame", "Lure of Flames (Palm)",
          "Call fire enough to fill a cupped hand.", cost=1, gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="fire", damage=1),
    Power("Lure of Flames", 3, "campfire", "Lure of Flames (Campfire)",
          "Raise a roaring campfire's worth of flame.", cost=1, gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="fire", damage=2),
    Power("Lure of Flames", 4, "bonfire", "Lure of Flames (Bonfire)",
          "Loose a towering bonfire.", cost=1, gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="fire", damage=3),
    Power("Lure of Flames", 5, "inferno", "Lure of Flames (Inferno)",
          "Unleash an engulfing inferno.", cost=1, gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="fire", damage=4),

    Power("Movement of the Mind", 1, "tk_grams", "Movement of the Mind (light)",
          "Nudge small objects with a thought.", roll=("intelligence", "occult"), effect=""),
    Power("Movement of the Mind", 2, "tk_kilo", "Movement of the Mind (handheld)",
          "Lift and hurl what a hand could hold.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="telekinesis", damage=0),
    Power("Movement of the Mind", 3, "tk_heavy", "Movement of the Mind (heavy)",
          "Fling furniture and worse across a room.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="telekinesis", damage=1),
    Power("Movement of the Mind", 4, "tk_person", "Movement of the Mind (a person)",
          "Throw a grown body through the air.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="telekinesis", damage=2),
    Power("Movement of the Mind", 5, "tk_crushing", "Movement of the Mind (crushing)",
          "Pin or crush with unseen force.", gate="line_of_sight", target="other",
          roll=("intelligence", "occult"), combat=True, effect="telekinesis", damage=3),

    Power("Path of the Sepulchre", 1, "witness_of_death", "Witness of Death",
          "Open your senses to the restless dead.", roll=("perception", "occult"), effect="deathsight"),
    Power("Path of the Sepulchre", 2, "summon_soul", "Summon Soul",
          "Call a known ghost to speak with you.", gate="none", target="other",
          roll=("manipulation", "occult"), effect=""),
    Power("Path of the Sepulchre", 3, "compel_soul", "Compel Soul",
          "Bind a wraith to your command.", gate="line_of_sight", target="other",
          roll=("manipulation", "occult"), contested=True, effect=""),
    Power("Path of the Sepulchre", 4, "haunting", "Haunting",
          "Tether a tormenting ghost to a victim.", gate="line_of_sight", target="other",
          roll=("manipulation", "occult"), contested=True, combat=True, effect="confuse"),
    Power("Path of the Sepulchre", 5, "torment", "Torment",
          "Drive a bound wraith to savage the living.", gate="line_of_sight", target="other",
          roll=("manipulation", "occult"), contested=True, combat=True, effect="damage", damage=1),
]

REGISTRY = {(p.discipline.lower(), p.key): p for p in _POWERS}
POWER_LIST = tuple(_POWERS)

_LABELS = {p.discipline.lower(): p.discipline for p in _POWERS}

_COMMAND_WORDS = {
    "flee": "flee", "run": "flee", "away": "flee", "leave": "flee", "go": "flee",
    "stop": "pass", "halt": "pass", "freeze": "pass", "wait": "pass", "still": "pass",
    "sleep": "pass", "drop": "pass", "kneel": "pass", "surrender": "pass",
}


def label_for(discipline: str) -> str:
    return _LABELS.get(discipline.lower(), discipline.title())


def combat_powers_for(rs, actor) -> list:
    out = []
    for p in _POWERS:
        if p.combat and rs.discipline_rating(actor, p.discipline) >= p.dots:
            out.append(p)
    return out


def _check_gate(rs, actor, target, power: Power) -> str:
    if power.target in ("self", "animal") or power.gate in ("self", "none"):
        return ""
    if target is None:
        return "no_target"
    if rs.is_defeated(target):
        return "target_down"
    if power.gate == "eye_contact":
        if "blinded" in actor.statuses or "blinded" in target.statuses:
            return "no_eye_contact"
        if target.sheet.get("_frenzied") or "asleep" in target.statuses:
            return "target_unreachable"
        if not rs.can_receive_communication(target, "mental"):
            return "target_unreachable"
    elif power.gate == "line_of_sight":
        if "hidden" in target.statuses or "blinded" in actor.statuses:
            return "no_line_of_sight"
    elif power.gate == "verbal":
        if not rs.can_receive_communication(target, "verbal"):
            return "cannot_hear"
    return ""


def resolve_power(rs, actor, discipline, power_key, target=None, *, param="", allies=()) -> PowerResult:
    power = REGISTRY.get((discipline.lower(), power_key.lower()))
    if power is None:
        return PowerResult(False, reason="unknown_power")
    disc = power.discipline
    if rs.discipline_rating(actor, disc) < power.dots:
        return PowerResult(False, reason="insufficient_dots", discipline=disc, power=power.name)

    if disc == "Dominate" and target is not None:
        if target.sheet.get("generation", 13) < actor.sheet.get("generation", 13):
            return PowerResult(False, reason="blood_too_strong", discipline=disc, power=power.name)

    gate = _check_gate(rs, actor, target, power)
    if gate:
        return PowerResult(False, reason=gate, discipline=disc, power=power.name)

    spent = 0
    if power.cost:
        if not rs.spend_blood(actor, power.cost):
            return PowerResult(False, reason="not_enough_blood", discipline=disc, power=power.name)
        spent = power.cost

    success, band = True, None
    net = 0
    if power.roll is not None:
        attr_k, abil_k = power.roll
        pool = max(1, actor.sheet.get("attributes", {}).get(attr_k, 2)
                   + actor.sheet.get("abilities", {}).get(abil_k, 0))
        difficulty = power.base_difficulty
        if power.contested and target is not None:
            difficulty = min(9, max(3, target.sheet.get("willpower", 5)))
        s, o, net, _ = roll_pool(rs.dice, pool, difficulty)
        band = band_for_net(s, o, net)
        success = net > 0 if power.contested else band not in (Band.BOTCH, Band.FAILURE)

    result = PowerResult(True, success=success, band=band, discipline=disc,
                         power=power.name, blood_spent=spent, contested=power.contested,
                         net=max(0, net))
    _apply_effect(rs, power, actor, target, result, param, allies)
    return result


def _apply_effect(rs, power: Power, actor, target, result: PowerResult, param: str, allies) -> None:
    a, t = actor.name, (target.name if target is not None else "the target")
    eff = power.effect

    self_tokens = {"claws": "claws", "mist": "mist", "darksight": "darksight",
                   "mask": "masked", "awe": "awe", "majesty": "majesty",
                   "beast_form": "beast_form", "hide": "hidden",
                   "shadow": "shadow", "armor": "armored", "bonecraft": "bonecraft",
                   "warform": "warform", "serpent_form": "serpent_form",
                   "heartless": "heartless", "disguise": "disguised",
                   "potent": "potent", "deathsight": "deathsight"}
    if eff in self_tokens:
        if result.success:
            actor.statuses.add(self_tokens[eff])
        result.cue = _self_cue(eff, a, result.success)
        return

    if eff == "hide_allies":
        if result.success:
            actor.statuses.add("hidden")
            for ally in allies:
                ally.statuses.add("hidden")
        result.cue = (f"RESULT: {a} and those nearby fade from notice."
                      if result.success else f"RESULT: the concealment fails to take.")
        return

    if eff == "command":
        if result.success and target is not None:
            forced = _COMMAND_WORDS.get((param or "flee").strip().lower(), "pass")
            target.statuses.add("dominated")
            target.sheet["_dominated_command"] = forced
            verb = "turns to flee" if forced == "flee" else "freezes, unable to act"
            result.cue = f"RESULT: {t} obeys against their will and {verb}."
        else:
            result.cue = f"RESULT: {t} shrugs off the command."
        return

    if eff == "terrify":
        if result.success and target is not None:
            target.statuses.add("terrified")
            result.cue = f"RESULT: {t} is seized by supernatural dread and recoils from {a}."
        else:
            result.cue = f"RESULT: {t} steels themselves against the fear."
        return

    if eff == "entrance":
        if result.success and target is not None:
            target.statuses.add("entranced")
            result.cue = f"RESULT: {t} is enraptured and will not raise a hand against {a}."
        else:
            result.cue = f"RESULT: {t} remains unmoved by {a}'s presence."
        return

    if eff == "quell":
        if result.success and target is not None:
            was = bool(target.sheet.pop("_frenzied", False))
            target.statuses.discard("terrified")
            target.statuses.add("cowed")
            result.cue = (f"RESULT: the Beast in {t} is smothered; the frenzy drains away."
                          if was else f"RESULT: {t}'s passions go cold and still.")
        else:
            result.cue = f"RESULT: the Beast in {t} will not be quieted."
        return

    if eff == "draw_out_beast":
        if result.success and target is not None and actor.sheet.get("_frenzied"):
            actor.sheet.pop("_frenzied", None)
            target.sheet["_frenzied"] = True
            result.cue = f"RESULT: {a} casts the frenzy out and into {t}, going suddenly calm."
        elif result.success:
            result.cue = f"RESULT: {a} reaches for a frenzy that isn't there; nothing passes."
        else:
            result.cue = f"RESULT: the Beast refuses to leave {a}."
        return

    debuffs = {"entangle": ("entangled", "shadow-limbs drag {t} fast and helpless"),
               "blind": ("blinded", "a swallowing darkness blinds {t}"),
               "silence": ("silenced", "every sound around {t} is smothered to nothing"),
               "paralyze": ("paralyzed", "{t} freezes, locked rigid and unable to move"),
               "confuse": ("confused", "{t} reels, senses swimming with phantoms"),
               "poison": ("poisoned", "{t}'s blood curdles to venom, sapping their strength")}
    if eff in debuffs:
        token, line = debuffs[eff]
        if result.success and target is not None:
            target.statuses.add(token)
            result.cue = "RESULT: " + line.format(t=t) + "."
        else:
            result.cue = f"RESULT: {t} shakes it off."
        return

    if eff == "madden":
        if result.success and target is not None:
            target.sheet["_frenzied"] = True
            target.statuses.add("maddened")
            result.cue = f"RESULT: madness floods {t}; the Beast slips its leash and rages."
        else:
            result.cue = f"RESULT: {t}'s mind holds against the madness."
        return

    if eff == "insane":
        if result.success and target is not None:
            target.statuses.add("insane")
            target.sheet.setdefault("derangements", []).append("induced insanity")
            result.cue = f"RESULT: every madness at once breaks over {t}; they are lost to it."
        else:
            result.cue = f"RESULT: {t} reels but does not break."
        return

    if eff in ("damage", "fire", "blood_drain", "telekinesis"):
        if not result.success:
            result.cue = {"fire": f"RESULT: the flames gutter out short of {t}.",
                          "telekinesis": f"RESULT: the force slips off {t}."}.get(
                eff, f"RESULT: {t} resists the worst of it.")
            return
        net = max(1, result.net)
        levels = max(1, net + power.damage)
        if target is not None:
            rs.apply_damage(target, levels)
            if eff == "blood_drain":
                stolen = min(levels, target.sheet.get("blood", 0))
                target.sheet["blood"] = target.sheet.get("blood", 0) - stolen
                actor.sheet["blood"] = min(actor.sheet.get("blood_max", 10),
                                           actor.sheet.get("blood", 0) + stolen)
        result.damage_dealt = levels
        phrasing = {"fire": f"fire engulfs {t}, searing {levels} wound level(s)",
                    "blood_drain": f"{a} rips {levels} of vitae from {t} across the air",
                    "telekinesis": f"unseen force hurls {t} for {levels} wound level(s)"}.get(
            eff, f"{t} convulses as their blood turns against them ({levels} level(s))")
        result.cue = "RESULT: " + phrasing + "."
        return

    cues = {
        "mesmerize": (f"RESULT: a hidden suggestion settles into {t}'s mind, waiting.",
                      f"RESULT: the suggestion fails to take in {t}."),
        "forget": (f"RESULT: a span of {t}'s memory dissolves as {a} wills it.",
                   f"RESULT: {t}'s memory resists {a}'s reshaping."),
        "condition": (f"RESULT: {t} bends further to {a}'s will, more pliable than before.",
                      f"RESULT: {t} resists being broken to {a}'s will."),
        "possession": (f"RESULT: {a}'s psyche floods into {t}, seizing the body.",
                       f"RESULT: {a} batters at {t}'s mind but cannot take hold."),
        "summon": (f"RESULT: {t} feels the pull and will come to {a}.",
                   f"RESULT: the call does not reach {t}."),
        "": (f"RESULT: {a}'s {power.name.lower()} takes hold.",
             f"RESULT: {a}'s {power.name.lower()} fails to take."),
    }
    yes, no = cues.get(eff, cues[""])
    result.cue = yes if result.success else no


def _self_cue(eff: str, a: str, ok: bool) -> str:
    if not ok:
        return f"RESULT: {a}'s power flickers and fails."
    return {
        "claws": f"RESULT: talons of bone erupt from {a}'s fingers.",
        "mist": f"RESULT: {a} dissolves into a roiling bank of mist, untouchable.",
        "darksight": f"RESULT: {a}'s eyes catch fire with red light; the dark is no barrier.",
        "masked": f"RESULT: {a}'s features blur into those of an unremarkable stranger.",
        "awe": f"RESULT: every eye is drawn helplessly to {a}.",
        "majesty": f"RESULT: {a} radiates a terrible majesty; none dare move against them.",
        "beast_form": f"RESULT: {a}'s body twists into the shape of the Beast.",
        "hidden": f"RESULT: {a} slips from sight and notice.",
        "shadow": f"RESULT: writhing shadow-limbs erupt from {a}'s back, edged like knives.",
        "armored": f"RESULT: {a}'s skin hardens into scaled, blade-turning armor.",
        "bonecraft": f"RESULT: {a} draws their own bone into jagged spurs and plate.",
        "warform": f"RESULT: {a} swells into a hulking, fanged war-beast.",
        "serpent_form": f"RESULT: {a} pours down into the coils of a great black serpent.",
        "heartless": f"RESULT: {a} draws out their own heart and hides it away.",
        "disguised": f"RESULT: {a} kneads their flesh into an unfamiliar face.",
        "potent": f"RESULT: {a}'s blood thickens, surging closer to the elders' power.",
        "deathsight": f"RESULT: the veil thins; {a} sees and hears the restless dead.",
    }.get(eff, f"RESULT: {a} invokes the power.")
