from __future__ import annotations

from engine.creation import Option, Step
from engine.dice import Dice, RandomDice
from engine.difficulty import DifficultyBand
from engine.events import PowerUsed, RiteCast
from engine.invoke import POWER_SHORTHANDS, match_invocation
from engine.morality import Morality, Sin
from engine.outcome import Band, Difficulty, Outcome, PoolDifficulty
from engine.ruleset import Ruleset, SpecialAction
from engine.state import Combatant
from engine.turnmodel import TurnModel
from rulesets.storyteller.additional.disciplines import POWER_LIST, combat_powers_for, resolve_power
from rulesets.storyteller.additional.rituals import RITUAL_LIST, RITUALS, perform_ritual
from rulesets.storyteller.core.storyteller_combat import StorytellerTurnModel, band_for_net, roll_pool

ST_SKILLS = {
    "brawl": ("dexterity", "brawl"), "melee": ("dexterity", "melee"),
    "dodge": ("dexterity", "dodge"), "athletics": ("dexterity", "athletics"),
    "stealth": ("dexterity", "stealth"),
    "intimidation": ("manipulation", "intimidation"),
    "subterfuge": ("manipulation", "subterfuge"),
    "deception": ("manipulation", "subterfuge"),
    "persuasion": ("charisma", "subterfuge"),
    "awareness": ("perception", "awareness"),
    "investigation": ("perception", "investigation"),
    "occult": ("intelligence", "occult"), "academics": ("intelligence", "academics"),
}
ST_SKILL_TAGS = {
    "brawl": {"physical"}, "melee": {"physical"}, "dodge": {"physical"},
    "athletics": {"physical"}, "stealth": {"physical", "opposed"},
    "intimidation": {"social", "opposed"}, "subterfuge": {"social", "opposed"},
    "deception": {"social", "opposed"}, "persuasion": {"social", "opposed"},
    "awareness": {"sight"}, "investigation": {"sight"},
}
PERCEPTION_SKILLS = {"awareness", "investigation"}

TARGET_BY_BAND = {
    DifficultyBand.TRIVIAL: 4, DifficultyBand.EASY: 5, DifficultyBand.MEDIUM: 6,
    DifficultyBand.HARD: 7, DifficultyBand.VERY_HARD: 8, DifficultyBand.NEARLY_IMPOSSIBLE: 9,
}

HEALTH_LABELS = ["unhurt", "bruised", "hurt", "injured", "wounded", "mauled",
                 "crippled", "incapacitated"]
WOUND_DIFFICULTY_STEPS = [0, 0, 1, 1, 2, 2, 3]
WOUND_DICE_PENALTY = [0, 0, 1, 1, 2, 2, 5]

GENERATION = {
    13: (10, 1, 5), 12: (11, 1, 5), 11: (12, 1, 5), 10: (13, 1, 5),
    9: (14, 2, 5), 8: (15, 3, 5), 7: (20, 4, 6), 6: (30, 6, 7),
}

HUMANITY_NOTES = {
    10: "Saintly. The Beast is a distant whisper; cruelty is almost unthinkable.",
    9: "Conscientious. Guilt bites hard; you hold yourself to a high line.",
    8: "Decent. An ordinary moral person who recoils from real harm.",
    7: "Ordinary. Small selfishness comes without much guilt.",
    6: "Hardening. You can hurt when pressed and rationalize it after.",
    5: "Callous. Violence is a tool you reach for easily.",
    4: "Cruel. Empathy is thin; others are mostly means to ends.",
    3: "Monstrous. You kill without much thought; the mask slips.",
    2: "Predatory. The Beast rides close behind every want.",
    1: "A monster wearing a face. Almost nothing of the person remains.",
    0: "Wassail. The Beast has won -- the character is lost to the Storyteller.",
}
SIN_THRESHOLD = {5: 1, 4: 3, 3: 5, 2: 7, 1: 9}
SINS = (
    Sin(1, "a petty selfish, cowardly, or dishonest act"),
    Sin(2, "deliberate theft, vandalism, or betrayal of trust"),
    Sin(3, "intentional and serious injury to another being"),
    Sin(4, "killing in the heat of the moment, or through callous neglect"),
    Sin(5, "premeditated murder, torture, or wanton atrocity"),
)

ABILITY_LABELS = {"strength": "Strength", "dexterity": "Dexterity",
                  "stamina": "Stamina", "wits": "Wits", "charisma": "Charisma",
                  "intelligence": "Intelligence"}
CLANS = {
    "brujah": {"label": "Brujah", "detail": "Rebels and brawlers (Celerity, Potence, Presence)."},
    "gangrel": {"label": "Gangrel", "detail": "Feral survivors (Animalism, Fortitude, Protean)."},
    "ventrue": {"label": "Ventrue", "detail": "Aristocratic leaders (Dominate, Fortitude, Presence)."},
    "nosferatu": {"label": "Nosferatu", "detail": "Hidden lurkers (Animalism, Obfuscate, Potence)."},
    "toreador": {"label": "Toreador", "detail": "Artists and seducers (Auspex, Celerity, Presence)."},
    "malkavian": {"label": "Malkavian", "detail": "Mad oracles (Auspex, Dominate, Dementation)."},
    "tremere": {"label": "Tremere", "detail": "Blood sorcerers (Auspex, Dominate, Thaumaturgy)."},
    "lasombra": {"label": "Lasombra", "detail": "Shadow-wielding lords (Dominate, Obtenebration, Potence)."},
    "tzimisce": {"label": "Tzimisce", "detail": "Flesh-shaping fiends (Animalism, Auspex, Vicissitude)."},
    "assamite": {"label": "Assamite", "detail": "Silent assassins (Celerity, Obfuscate, Quietus)."},
    "setite": {"label": "Followers of Set", "detail": "Serpent-priests (Obfuscate, Presence, Serpentis)."},
    "ravnos": {"label": "Ravnos", "detail": "Tricksters and illusionists (Animalism, Chimerstry, Fortitude)."},
    "giovanni": {"label": "Giovanni", "detail": "Necromancer-merchants (Dominate, Necromancy, Potence)."},
}
CLAN_DISCIPLINES = {
    "brujah": ["Celerity", "Potence", "Presence"],
    "gangrel": ["Animalism", "Fortitude", "Protean"],
    "ventrue": ["Dominate", "Fortitude", "Presence"],
    "nosferatu": ["Animalism", "Obfuscate", "Potence"],
    "toreador": ["Auspex", "Celerity", "Presence"],
    "malkavian": ["Auspex", "Dominate", "Dementation"],
    "tremere": ["Auspex", "Dominate", "Path of Blood"],
    "lasombra": ["Dominate", "Obtenebration", "Potence"],
    "tzimisce": ["Animalism", "Auspex", "Vicissitude"],
    "assamite": ["Celerity", "Obfuscate", "Quietus"],
    "setite": ["Obfuscate", "Presence", "Serpentis"],
    "ravnos": ["Animalism", "Chimerstry", "Fortitude"],
    "giovanni": ["Dominate", "Path of the Sepulchre", "Potence"],
}
DISCIPLINES = {
    "potence": {"label": "Potence", "detail": "Supernatural strength: auto successes to damage."},
    "fortitude": {"label": "Fortitude", "detail": "Unholy toughness: extra soak, soaks aggravated."},
    "celerity": {"label": "Celerity", "detail": "Blinding speed: spend blood for extra actions."},
    "auspex": {"label": "Auspex", "detail": "Preternatural senses: extra perception dice."},
    "dominate": {"label": "Dominate", "detail": "Command another's mind (eye to eye)."},
    "obfuscate": {"label": "Obfuscate", "detail": "Slip from sight and memory."},
    "presence": {"label": "Presence", "detail": "Sway crowds with awe or dread."},
    "animalism": {"label": "Animalism", "detail": "Speak to and command beasts."},
    "protean": {"label": "Protean", "detail": "Claws, shadow-melding, and shape."},
    "obtenebration": {"label": "Obtenebration", "detail": "Wield the living shadow of the Abyss."},
    "quietus": {"label": "Quietus", "detail": "Silent death; turn vitae to poison."},
    "serpentis": {"label": "Serpentis", "detail": "The serpent's stare, scales, and shape."},
    "vicissitude": {"label": "Vicissitude", "detail": "Reshape flesh and bone like clay."},
    "chimerstry": {"label": "Chimerstry", "detail": "Illusions the senses swear are real."},
    "dementation": {"label": "Dementation", "detail": "Pour madness into another's mind."},
    "path_of_blood": {"label": "Path of Blood", "detail": "Thaumaturgy: master vitae itself."},
    "lure_of_flames": {"label": "Lure of Flames", "detail": "Thaumaturgy: conjure and hurl fire."},
    "movement_of_the_mind": {"label": "Movement of the Mind", "detail": "Thaumaturgy: telekinesis."},
    "path_of_the_sepulchre": {"label": "Path of the Sepulchre", "detail": "Necromancy: command the dead."},
}


def _gen_traits(generation: int):
    return GENERATION.get(generation, GENERATION[13])


class StorytellerRuleset(Ruleset):
    name = "storyteller-vtm"

    def __init__(self, dice: Dice | None = None):
        self.dice = dice or RandomDice()
        self._turn_model: TurnModel | None = None

    def modifier_for(self, actor: Combatant, skill: str) -> int:
        attr_key, abil_key = ST_SKILLS.get(skill.lower(), ("wits", "awareness"))
        attrs = actor.sheet.get("attributes", {})
        abils = actor.sheet.get("abilities", {})
        return attrs.get(attr_key, 2) + abils.get(abil_key, 0)

    def skill_names(self) -> list:
        return sorted(ST_SKILLS.keys())

    def skill_tags(self, skill: str) -> set:
        return set(ST_SKILL_TAGS.get(skill.lower(), set()))

    def difficulty_for_band(self, band: DifficultyBand) -> Difficulty:
        return PoolDifficulty(target=TARGET_BY_BAND.get(band, 6), required=1, label=band.value)

    def situational_difficulty_delta(self, actor: Combatant, skill: str) -> int:
        return WOUND_DIFFICULTY_STEPS[min(actor.sheet.get("health_taken", 0), 6)]

    def resolve_check(self, actor, skill, difficulty, ctx=None) -> Outcome:
        pool = max(1, self.modifier_for(actor, skill))
        target = getattr(difficulty, "target", 6)
        successes, ones, net, rolls = roll_pool(self.dice, pool, target)
        if skill.lower() in PERCEPTION_SKILLS:
            auspex = self.discipline_rating(actor, "Auspex")
            successes += auspex
            net = successes - ones
        band = band_for_net(successes, ones, net)
        success = band not in (Band.BOTCH, Band.FAILURE)
        return Outcome(success, band, magnitude=max(0, net),
                       is_botch=(band is Band.BOTCH),
                       raw={"pool": pool, "target": target, "successes": successes,
                            "ones": ones, "net": net, "rolls": rolls})

    def social_difficulty(self, target: Combatant, mode: str = "intimidate") -> Difficulty:
        return PoolDifficulty(target=target.sheet.get("resolve_target", 6), required=1)

    @staticmethod
    def discipline_rating(actor: Combatant, name: str) -> int:
        return actor.sheet.get("disciplines", {}).get(name, 0)

    def health_descriptor(self, actor: Combatant) -> str:
        return HEALTH_LABELS[min(actor.sheet.get("health_taken", 0), 7)]

    def apply_damage(self, actor: Combatant, amount: int, dtype: str | None = None) -> None:
        actor.sheet["health_taken"] = min(7, actor.sheet.get("health_taken", 0) + max(0, amount))

    def is_defeated(self, actor: Combatant) -> bool:
        return actor.sheet.get("health_taken", 0) >= 7

    def health_fraction(self, actor: Combatant) -> float:
        mx = actor.sheet.get("health_max", 7) or 7
        return max(0.0, (mx - actor.sheet.get("health_taken", 0)) / mx)

    def wound_dice_penalty(self, actor: Combatant) -> int:
        return WOUND_DICE_PENALTY[min(actor.sheet.get("health_taken", 0), 6)]

    def spend_blood(self, actor: Combatant, n: int = 1) -> bool:
        blood = actor.sheet.get("blood", 0)
        per = actor.sheet.get("blood_per_turn", 1)
        used = actor.sheet.get("_blood_turn", 0)
        if n <= 0 or n > blood or used + n > per:
            return False
        actor.sheet["blood"] = blood - n
        actor.sheet["_blood_turn"] = used + n
        return True

    def blood_augment(self, actor: Combatant, attribute: str = "strength", dots: int = 1) -> bool:
        if not self.spend_blood(actor, dots):
            return False
        attrs = actor.sheet.setdefault("attributes", {})
        attrs[attribute] = attrs.get(attribute, 2) + dots
        return True

    def combat_heal(self, actor: Combatant) -> tuple:
        if self.is_defeated(actor) or not self.spend_blood(actor, 1):
            return (False, 0)
        before = actor.sheet.get("health_taken", 0)
        actor.sheet["health_taken"] = max(0, before - 1)
        return (True, before - actor.sheet["health_taken"])

    def check_frenzy(self, actor: Combatant) -> bool:
        if actor.sheet.get("blood", 0) > 0 or self.is_defeated(actor):
            return False
        self_control = actor.sheet.get("virtues", {}).get("self_control", 2)
        humanity = actor.sheet.get("humanity", 7)
        difficulty = min(9, 6 + max(0, 5 - humanity))
        successes, ones, net, _ = roll_pool(self.dice, max(1, self_control), difficulty)
        if band_for_net(successes, ones, net) in (Band.BOTCH, Band.FAILURE):
            actor.sheet["_frenzied"] = True
            return True
        return False

    def is_out_of_control(self, actor: Combatant) -> bool:
        return bool(actor.sheet.get("_frenzied"))

    def morality(self) -> Morality:
        return Morality(name="Humanity", trait="humanity", virtue="conscience", sins=SINS)

    def degeneration_check(self, actor: Combatant, severity: int) -> dict:
        humanity = actor.sheet.get("humanity", 7)
        if severity <= 0 or humanity < SIN_THRESHOLD.get(severity, 99):
            return {"checked": False}
        conscience = actor.sheet.get("virtues", {}).get("conscience", 2)
        successes, ones, net, _ = roll_pool(self.dice, max(1, conscience), 8)
        band = band_for_net(successes, ones, net)
        result = {"checked": True, "before": humanity, "after": humanity,
                  "lost": False, "botch": False, "derangement": False, "trait": "Humanity"}
        if band not in (Band.BOTCH, Band.FAILURE):
            return result
        actor.sheet["humanity"] = max(0, humanity - 1)
        result.update(after=actor.sheet["humanity"], lost=True, botch=(band is Band.BOTCH))
        if band is Band.BOTCH:
            actor.sheet.setdefault("derangements", []).append("a new fracture in the psyche")
            result["derangement"] = True
        return result

    def actions_this_turn(self, actor: Combatant) -> int:
        extra = self.discipline_rating(actor, "Celerity") if actor.sheet.get("_celerity_active") else 0
        return 1 + extra

    def pre_turn_choices(self, actor: Combatant) -> list:
        choices = []
        cel = self.discipline_rating(actor, "Celerity")
        can_spend = actor.sheet.get("blood", 0) > 0 and \
            actor.sheet.get("_blood_turn", 0) < actor.sheet.get("blood_per_turn", 1)
        if cel >= 1 and can_spend and not actor.sheet.get("_celerity_active"):
            plural = "s" if cel != 1 else ""
            choices.append(("celerity", f"Blur (Celerity): 1 blood for {cel} extra action{plural}"))
        if can_spend:
            choices.append(("surge", "Surge: 1 blood for +1 Strength this scene"))
        return choices

    def apply_pre_turn(self, actor: Combatant, key: str) -> str:
        if key == "celerity" and self.spend_blood(actor, 1):
            actor.sheet["_celerity_active"] = True
            return f"{actor.name} blurs into motion."
        if key == "surge" and self.blood_augment(actor, "strength", 1):
            return f"{actor.name} floods muscle with blood."
        return ""

    def ai_pre_turn(self, actor: Combatant) -> None:
        if (self.discipline_rating(actor, "Celerity") >= 1
                and actor.sheet.get("blood", 0) > 2
                and not actor.sheet.get("_celerity_active")
                and self.spend_blood(actor, 1)):
            actor.sheet["_celerity_active"] = True

    def end_turn(self, actor: Combatant) -> None:
        actor.sheet["_blood_turn"] = 0
        actor.sheet.pop("_celerity_active", None)
        actor.sheet.pop("_frenzied", None)
        actor.sheet.pop("_dominated_command", None)

    def use_discipline(self, actor, discipline, power_key, target=None, *, param="", allies=()):
        return resolve_power(self, actor, discipline, power_key, target, param=param, allies=allies)

    def available_combat_powers(self, actor: Combatant) -> list:
        return combat_powers_for(self, actor)

    def discipline_powers(self) -> tuple:
        return POWER_LIST

    def exploration_powers(self, actor: Combatant) -> list:
        return [p for p in POWER_LIST if self.discipline_rating(actor, p.discipline) >= p.dots]

    def known_rituals(self, actor: Combatant) -> list:
        return [RITUALS[k] for k in actor.sheet.get("known_rituals", ()) if k in RITUALS]

    def try_special_action(self, actor, text):
        actor.sheet["_blood_turn"] = 0
        rituals = self.known_rituals(actor)
        powers = self.exploration_powers(actor)
        rite, _, expl_r = match_invocation(text, rituals, (), {})
        if rite is not None:
            return self._do_ritual(actor, rite, text)
        power, ptarget, expl_p = match_invocation(text, powers, (), POWER_SHORTHANDS)
        if power is not None:
            return self._do_power(actor, power, ptarget, text)
        if expl_r or expl_p:
            return SpecialAction("help", message=self._invocation_help(powers, rituals))
        return None

    def _do_power(self, actor, power, target_name, text):
        target = self.make_enemy((target_name or "the target").title()) if power.target == "other" else None
        result = resolve_power(self, actor, power.discipline, power.key, target)
        event = PowerUsed(name=actor.name, power=result.power or power.name,
                          discipline=power.discipline, target=(target_name or ""),
                          success=result.success, ok=result.ok, reason=result.reason)
        return SpecialAction("power", event=event, cue=result.cue, moral_text=text)

    def _do_ritual(self, actor, rite, text):
        target = None
        res = perform_ritual(self, actor, rite.key, target)
        event = RiteCast(name=actor.name, rite=rite.name, tradition=rite.tradition,
                         success=res.success, ok=res.ok, reason=res.reason, missing=res.missing)
        return SpecialAction("ritual", event=event, cue=res.cue, moral_text=text)

    def _invocation_help(self, powers, rituals) -> str:
        bits = []
        if powers:
            bits.append("Disciplines you can invoke (type 'use <power>'): "
                        + ", ".join(sorted(p.key for p in powers)) + ".")
        if rituals:
            bits.append("Rituals you can perform (type 'perform <ritual>'): "
                        + ", ".join(sorted(r.key for r in rituals)) + ".")
        return " ".join(bits) if bits else "You have no Disciplines or rituals to invoke."

    def forced_action(self, actor: Combatant) -> str | None:
        if actor.sheet.get("_frenzied"):
            return "attack"
        st = actor.statuses
        if "maddened" in st or "insane" in st:
            return "attack"
        if "terrified" in st:
            return "flee"
        if {"mist", "entranced", "entangled", "paralyzed"} & st:
            return "pass"
        cmd = actor.sheet.get("_dominated_command")
        if cmd:
            return cmd
        return None

    def ai_combat_power(self, actor: Combatant) -> str | None:
        if {"claws", "beast_form", "mist"} & actor.statuses:
            return None
        if self.discipline_rating(actor, "Protean") >= 2 and actor.sheet.get("blood", 0) >= 2:
            return "feral_claws"
        return None

    def turn_model(self) -> TurnModel:
        if self._turn_model is None:
            self._turn_model = StorytellerTurnModel(self)
        return self._turn_model

    def make_pc(self, name: str) -> Combatant:
        return Combatant(name=name, is_pc=True, sheet=self._default_sheet())

    @staticmethod
    def _vampire_sheet(*, attributes, abilities, disciplines, generation=13,
                       humanity=7, virtues=None, soak_bonus=0, name_clan="Caitiff",
                       is_enemy_mortal=False) -> dict:
        blood_max, per_turn, _ = _gen_traits(generation)
        virtues = virtues or {"conscience": 3, "self_control": 3, "courage": 3}
        soak = attributes.get("stamina", 2) + soak_bonus + disciplines.get("Fortitude", 0)
        return {
            "attributes": attributes, "abilities": abilities, "disciplines": disciplines,
            "attack": {"name": "fangs and fists", "attribute": "dexterity",
                       "skill": "brawl", "damage_rating": 2},
            "soak": soak, "health_taken": 0, "health_max": 7, "initiative_bonus": 0,
            "generation": generation, "blood": blood_max, "blood_max": blood_max,
            "blood_per_turn": per_turn,
            "humanity": humanity, "virtues": virtues, "willpower": 5, "willpower_max": 5,
            "derangements": [],
            "intelligence": 3, "morale": 100, "morale_threshold": 30, "resolve_target": 6,
            "comprehends_language": True, "mindless": False, "clan": name_clan,
            "inventory": [], "known_rituals": [], "scene_effects": [],
        }

    @classmethod
    def _default_sheet(cls) -> dict:
        return cls._vampire_sheet(
            attributes={"strength": 3, "dexterity": 3, "stamina": 3, "charisma": 2,
                        "manipulation": 2, "perception": 3, "intelligence": 2, "wits": 3},
            abilities={"brawl": 2, "dodge": 2, "melee": 1, "intimidation": 2,
                       "stealth": 2, "athletics": 1, "subterfuge": 1, "awareness": 2},
            disciplines={"Potence": 1, "Celerity": 1, "Fortitude": 1},
            generation=13, humanity=7, name_clan="Caitiff")

    def make_enemy(self, name: str, *, attributes=None, abilities=None, attack=None,
                   disciplines=None, generation=13, humanity=7, soak: int | None = None,
                   intelligence: int = 2, morale: int = 100,
                   comprehends_language: bool = True, mindless: bool = False) -> Combatant:
        attrs = {"strength": 2, "dexterity": 3, "stamina": 2, "charisma": 2,
                 "manipulation": 2, "perception": 2, "intelligence": 2, "wits": 3}
        attrs.update(attributes or {})
        abils = {"brawl": 2, "dodge": 1, "melee": 1, "intimidation": 1}
        abils.update(abilities or {})
        disc = dict(disciplines or {})
        sheet = self._vampire_sheet(attributes=attrs, abilities=abils, disciplines=disc,
                                    generation=generation, humanity=humanity)
        if attack:
            sheet["attack"] = attack
        else:
            sheet["attack"] = {"name": "claws", "attribute": "dexterity",
                               "skill": "brawl", "damage_rating": 2}
        if soak is not None:
            sheet["soak"] = soak + disc.get("Fortitude", 0)
        sheet.update(intelligence=intelligence, morale=morale,
                     comprehends_language=comprehends_language, mindless=mindless)
        c = Combatant(name=name, is_pc=False, sheet=sheet)
        return c

    def creation_spec(self) -> list:
        slots = tuple(Option(k, ABILITY_LABELS[k]) for k in
                      ("strength", "dexterity", "stamina", "wits", "charisma", "intelligence"))
        return [
            Step("name", "What is your character's name?", "text"),
            Step("clan", "Choose a clan", "choose_one",
                 options=tuple(Option(k, v["label"], v["detail"]) for k, v in CLANS.items())),
            Step("attributes", "Assign attribute dots (4,3,3,2,2,1)", "assign",
                 pool=(4, 3, 3, 2, 2, 1), slots=slots),
            Step("discipline", "Favor a Discipline (your clan's three start at 1; "
                 "your favored one gets +1)", "choose_one",
                 options=tuple(Option(k, v["label"], v["detail"]) for k, v in DISCIPLINES.items())),
        ]

    def build_pc(self, selections: dict) -> Combatant:
        name = str(selections.get("name", "Fledgling"))
        clan_key = selections.get("clan", "brujah")
        clan = CLANS.get(clan_key, {"label": "Caitiff"})

        assigned = dict(selections.get("attributes") or {})
        attrs = {"strength": 2, "dexterity": 2, "stamina": 2, "charisma": 2,
                 "manipulation": 2, "perception": 2, "intelligence": 2, "wits": 2}
        attrs.update(assigned)

        abils = {"brawl": 1, "dodge": 1, "melee": 0, "intimidation": 1, "stealth": 1,
                 "athletics": 1, "subterfuge": 1, "awareness": 1}

        disciplines = {d: 1 for d in CLAN_DISCIPLINES.get(clan_key, [])}
        favored = DISCIPLINES.get(selections.get("discipline"), {}).get("label", "Potence")
        disciplines[favored] = disciplines.get(favored, 0) + 1

        sheet = self._vampire_sheet(attributes=attrs, abilities=abils,
                                    disciplines=disciplines, generation=13, humanity=7,
                                    name_clan=clan["label"])
        return Combatant(name=name, is_pc=True, sheet=sheet)
