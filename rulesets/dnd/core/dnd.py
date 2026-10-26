from __future__ import annotations

from engine import addons as _addons
from engine.creation import Option, Step
from engine.dice import Dice, RandomDice
from engine.difficulty import DifficultyBand
from engine.outcome import (Band, Difficulty, OpposedDifficulty, Outcome,
                       StaticDifficulty)
from engine.ruleset import Ruleset
from engine.state import Combatant
from engine.turnmodel import TurnModel
from rulesets.dnd.core.dnd_combat import DnDTurnModel

SKILLS = {
    "athletics": "str",
    "acrobatics": "dex", "stealth": "dex", "sleight_of_hand": "dex",
    "arcana": "int", "history": "int", "investigation": "int",
    "nature": "int", "religion": "int",
    "animal_handling": "wis", "insight": "wis", "medicine": "wis",
    "perception": "wis", "survival": "wis",
    "deception": "cha", "intimidation": "cha",
    "performance": "cha", "persuasion": "cha",
}
ABILITIES = ("str", "dex", "con", "int", "wis", "cha")

SKILL_TAGS = {
    "athletics": {"physical"},
    "acrobatics": {"physical"},
    "stealth": {"physical", "opposed"},
    "sleight_of_hand": {"physical", "tool"},
    "perception": {"sight"},
    "investigation": {"sight"},
    "insight": {"social"},
    "deception": {"social", "opposed"},
    "intimidation": {"social", "opposed"},
    "persuasion": {"social", "opposed"},
    "performance": {"social"},
    "survival": {"sight"},
    "str": {"physical"}, "dex": {"physical"}, "cha": {"social"},
}

DC_BY_BAND = {
    DifficultyBand.TRIVIAL: 5,
    DifficultyBand.EASY: 10,
    DifficultyBand.MEDIUM: 15,
    DifficultyBand.HARD: 20,
    DifficultyBand.VERY_HARD: 25,
    DifficultyBand.NEARLY_IMPOSSIBLE: 30,
}

ABILITY_LABELS = {"str": "Strength", "dex": "Dexterity", "con": "Constitution",
                  "int": "Intelligence", "wis": "Wisdom", "cha": "Charisma"}
STANDARD_ARRAY = (15, 14, 13, 12, 10, 8)

ANCESTRIES = {
    "human": {"label": "Human", "bonus": {"str": 1, "dex": 1, "con": 1,
                                          "int": 1, "wis": 1, "cha": 1},
              "detail": "+1 to every ability."},
    "elf": {"label": "Elf", "bonus": {"dex": 2, "int": 1},
            "detail": "+2 Dexterity, +1 Intelligence; keen-eyed."},
    "dwarf": {"label": "Dwarf", "bonus": {"con": 2, "str": 1},
              "detail": "+2 Constitution, +1 Strength; hardy."},
    "halfling": {"label": "Halfling", "bonus": {"dex": 2, "cha": 1},
                 "detail": "+2 Dexterity, +1 Charisma; nimble and lucky."},
}
CLASSES = {
    "fighter": {"label": "Fighter", "hit_die": 10, "attack_ability": "str",
                "ac_base": 16, "ac_adds_dex": False, "weapon": ("longsword", "1d8"),
                "skills": ["athletics", "perception"],
                "detail": "d10 HP, heavy armor; Strength and steel."},
    "rogue": {"label": "Rogue", "hit_die": 8, "attack_ability": "dex",
              "ac_base": 12, "ac_adds_dex": True, "weapon": ("shortsword", "1d6"),
              "skills": ["stealth", "acrobatics", "perception"],
              "detail": "d8 HP, light armor; Dexterity and guile."},
    "cleric": {"label": "Cleric", "hit_die": 8, "attack_ability": "wis",
               "ac_base": 16, "ac_adds_dex": False, "weapon": ("mace", "1d6"),
               "skills": ["insight", "medicine"],
               "detail": "d8 HP, heavy armor; Wisdom and faith."},
    "wizard": {"label": "Wizard", "hit_die": 6, "attack_ability": "int",
               "ac_base": 12, "ac_adds_dex": True, "weapon": ("arcane bolt", "1d8"),
               "skills": ["arcana", "investigation"],
               "detail": "d6 HP, no armor; Intelligence and arcana."},
}


def _attr(obj, key, default=None):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _skill_label(key: str) -> str:
    return key.replace("_", " ").title()


def _first(items):
    return items[0] if items else ""


_STARTING_GOLD = {"barbarian": 50, "bard": 125, "cleric": 125, "druid": 50, "fighter": 150,
                  "monk": 15, "paladin": 150, "ranger": 150, "rogue": 100, "sorcerer": 75,
                  "warlock": 100, "wizard": 80}


class DnDRuleset(Ruleset):
    name = "dnd5e-lite"

    def __init__(self, dice: Dice | None = None):
        _addons.load_all()
        self.dice = dice or RandomDice()
        self._turn_model: TurnModel | None = None
        try:
            from rulesets.dnd.additional import (alignment as _align, backgrounds as _bg,
                                                 classes as _classes, equipment as _equipment_mod,
                                                 gender as _gender_mod, items as _items_mod,
                                                 leveling as _leveling,
                                                 proficiencies as _prof,
                                                 races as _races, spells as _spells,
                                                 subclasses as _subclasses_mod,
                                                 trade as _trade_mod)
            self.races = dict(_races.RACES)
            self.classes = dict(_classes.CLASSES)
            self.alignments = dict(_align.ALIGNMENTS)
            self.backgrounds = dict(_bg.BACKGROUNDS)
            self._race_order = _races.ORDER
            self._class_order = _classes.ORDER
            self._align_order = _align.ORDER
            self._bg_order = _bg.ORDER
            self._align = _align
            self._bg = _bg
            self._prof = _prof
            self._leveling = _leveling
            self._spells = _spells
            self._subclasses = _subclasses_mod
            self._items = _items_mod
            self._trade = _trade_mod
            self._gender = _gender_mod
            self._equipment = _equipment_mod
            self._has_additional = True
        except Exception:
            self.races = dict(ANCESTRIES)
            self.classes = dict(CLASSES)
            self.alignments = {}
            self.backgrounds = {}
            self._race_order = tuple(ANCESTRIES)
            self._class_order = tuple(CLASSES)
            self._align_order = ()
            self._bg_order = ()
            self._align = None
            self._bg = None
            self._prof = None
            self._leveling = None
            self._spells = None
            self._subclasses = None
            self._items = None
            self._trade = None
            self._gender = None
            self._equipment = None
            self._has_additional = False

        self.extensions = [factory(self) for factory in _addons.ruleset_extensions("dnd")
                           if self._has_additional]

        try:
            from rulesets.dnd import settings as _settings
            self.settings = dict(_settings.SETTINGS)
            self._setting_order = _settings.ORDER
            self.setting = self.settings.get(_settings.DEFAULT)
        except Exception:
            self.settings = {}
            self._setting_order = ()
            self.setting = None

        import random as _random
        self.shops: dict = {}
        self._shop_rng = _random.Random()
        self._rest_count = 0

    @staticmethod
    def _ability_mod(score: int) -> int:
        return (score - 10) // 2

    def modifier_for(self, actor: Combatant, skill: str) -> int:
        sheet = actor.sheet
        abilities = sheet.get("abilities", {})
        prof = sheet.get("proficiencies", [])
        pb = sheet.get("proficiency_bonus", 2)
        skill = skill.lower()
        if skill in ABILITIES:
            return self._ability_mod(abilities.get(skill, 10))
        for ext in self.extensions:
            mod = ext.skill_modifier(actor, skill)
            if mod is not None:
                return mod
        ability = SKILLS.get(skill, "int")
        mod = self._ability_mod(abilities.get(ability, 10))
        if skill in prof:
            mod += pb
        return mod

    def skill_names(self) -> list[str]:
        names = list(SKILLS.keys()) + list(ABILITIES)
        for ext in self.extensions:
            names += [n for n in ext.skill_names() if n not in names]
        return names

    def _skill_ability(self, skill: str) -> str:
        s = skill.lower()
        if s in SKILLS:
            return SKILLS[s]
        for ext in self.extensions:
            ab = ext.skill_ability(s)
            if ab:
                return ab
        return s

    def _mental_abilities(self) -> set:
        out = set(self._gender.MENTAL) if self._gender is not None else {"int", "wis", "cha"}
        for ext in self.extensions:
            out |= set(ext.mental_abilities())
        return out

    def situational_difficulty_delta(self, actor: Combatant, skill: str) -> int:
        steps = 0
        if (self._gender is not None and self._gender.dissonant(actor.sheet)
                and self._skill_ability(skill) in self._mental_abilities()):
            steps += 1
        for ext in self.extensions:
            steps += ext.difficulty_delta(actor, skill)
        return steps

    def skill_tags(self, skill: str) -> set[str]:
        return set(SKILL_TAGS.get(skill.lower(), set()))

    def difficulty_for_band(self, band: DifficultyBand) -> Difficulty:
        return StaticDifficulty(dc=DC_BY_BAND.get(band, 15), label=band.value)

    def resolve_check(self, actor, skill, difficulty, ctx=None) -> Outcome:
        ctx = ctx or {}
        roll = self.dice.roll(20)
        mod = self.modifier_for(actor, skill) + int(ctx.get("situational", 0))
        total = roll + mod
        dc = self._dc_against(difficulty)
        return self._band(roll, total, dc, mod)

    def _dc_against(self, difficulty: Difficulty) -> int:
        if isinstance(difficulty, StaticDifficulty):
            return difficulty.dc
        if isinstance(difficulty, OpposedDifficulty):
            return self.dice.roll(20) + self.modifier_for(
                difficulty.target, difficulty.skill)
        raise TypeError(f"unknown difficulty: {difficulty!r}")

    def _band(self, roll: int, total: int, dc: int, mod: int) -> Outcome:
        raw = {"roll": roll, "total": total, "dc": dc, "mod": mod}
        if roll == 20:
            return Outcome(True, Band.CRITICAL, total - dc, is_crit=True, raw=raw)
        if roll == 1:
            return Outcome(False, Band.BOTCH, total - dc, is_botch=True, raw=raw)
        margin = total - dc
        if total >= dc:
            band = Band.EXCEPTIONAL if margin >= 10 else Band.SUCCESS
            return Outcome(True, band, margin, raw=raw)
        return Outcome(False, Band.FAILURE, margin, raw=raw)

    def health_descriptor(self, actor: Combatant) -> str:
        hp = actor.sheet.get("hp", 1)
        mx = actor.sheet.get("max_hp", 1)
        if hp <= 0:
            return "down and out"
        frac = hp / mx if mx else 1.0
        if frac >= 0.99:
            return "unhurt"
        if frac >= 0.6:
            return "lightly hurt"
        if frac >= 0.3:
            return "badly wounded"
        return "barely standing"

    def apply_damage(self, actor: Combatant, amount: int, dtype: str | None = None) -> None:
        actor.sheet["hp"] = max(0, actor.sheet.get("hp", 0) - max(0, amount))

    def apply_healing(self, actor: Combatant, amount: int) -> int:
        mx = actor.sheet.get("max_hp", actor.sheet.get("hp", 0))
        before = actor.sheet.get("hp", 0)
        actor.sheet["hp"] = min(mx, before + max(0, amount))
        return actor.sheet["hp"] - before

    _CONSUMABLE_HEAL = {"potion_of_healing": "2d4+2"}

    def use_item(self, actor: Combatant, item_key: str, *, presenter=None) -> dict:
        inv = actor.sheet.setdefault("inventory", [])
        if item_key not in inv:
            return {"ok": False, "kind": "none", "message": "You aren't carrying that."}
        info = self._items.get(item_key) if self._items is not None else None
        for ext in self.extensions:
            res = ext.use_item(actor, item_key, info, presenter=presenter)
            if res is not None:
                return res
        formula = self._CONSUMABLE_HEAL.get(item_key)
        if formula is None:
            return {"ok": False, "kind": "non_consumable",
                    "message": "That isn't something you can use up right now."}
        from engine.dice import roll_notation
        healed = self.apply_healing(actor, roll_notation(self.dice, formula))
        inv.remove(item_key)
        name = getattr(info, "name", None) or item_key
        return {"ok": True, "kind": "heal", "healed": healed, "item_key": item_key, "item_name": name,
                "message": f"You drink the {name} and recover ({healed} HP)."}

    def is_defeated(self, actor: Combatant) -> bool:
        return actor.sheet.get("hp", 0) <= 0

    def health_fraction(self, actor: Combatant) -> float:
        mx = actor.sheet.get("max_hp", 1) or 1
        return max(0.0, actor.sheet.get("hp", 0) / mx)

    def turn_model(self) -> TurnModel:
        if self._turn_model is None:
            self._turn_model = DnDTurnModel(self)
        return self._turn_model

    def make_pc(self, name: str) -> Combatant:
        sheet = self.default_sheet()
        self._init_profile(sheet, None)
        return Combatant(name=name, is_pc=True, sheet=sheet)

    def creation_spec(self) -> list[Step]:
        ability_slots = tuple(Option(a, ABILITY_LABELS[a]) for a in ABILITIES)
        race_opts = tuple(Option(k, _attr(self.races[k], "label", k),
                                 _attr(self.races[k], "detail", ""))
                          for k in self._race_order if k in self.races)
        class_opts = tuple(Option(k, _attr(self.classes[k], "label", k),
                                  _attr(self.classes[k], "detail", ""))
                           for k in self._class_order if k in self.classes)
        steps = [
            Step("name", "What is your character's name?", "text"),
            Step("race", "Choose a race", "choose_one", options=race_opts),
            Step("class", "Choose a class", "choose_one", options=class_opts),
        ]
        if self._has_additional:
            bg_opts = tuple(Option(k, self.backgrounds[k].label, self.backgrounds[k].detail)
                            for k in self._bg_order if k in self.backgrounds)
            steps.append(Step("background", "Choose a background", "choose_one", options=bg_opts))
            align_opts = tuple(Option(k, self.alignments[k].label, self.alignments[k].tendency)
                               for k in self._align_order)
            steps.append(Step("alignment", "Choose an alignment", "choose_one", options=align_opts))
        steps.append(Step("abilities", "Assign the standard array (15,14,13,12,10,8)", "assign",
                          pool=STANDARD_ARRAY, slots=ability_slots))
        if self._has_additional:
            steps.append(Step("skills", "Choose skill proficiencies", "choose_many", dynamic=True))
            steps.append(Step("trait", "Choose a personality trait", "choose_one", dynamic=True))
            steps.append(Step("ideal", "Choose an ideal", "choose_one", dynamic=True))
            steps.append(Step("bond", "Choose a bond", "choose_one", dynamic=True))
            steps.append(Step("flaw", "Choose a flaw", "choose_one", dynamic=True))
        return steps

    _RP_ATTR = {"trait": "traits", "ideal": "ideals", "bond": "bonds", "flaw": "flaws"}

    def options_for(self, step_key: str, selections: dict) -> tuple:
        if step_key == "skills":
            cls = self.classes.get(selections.get("class"))
            skills = _attr(cls, "skill_list", None) or _attr(cls, "skills", ()) if cls else ()
            return tuple(Option(s, _skill_label(s)) for s in skills)
        if step_key in self._RP_ATTR:
            bg = self.backgrounds.get(selections.get("background"))
            items = _attr(bg, self._RP_ATTR[step_key], ()) if bg else ()
            return tuple(Option(s, s) for s in items)
        return ()

    def count_for(self, step_key: str, selections: dict) -> int:
        if step_key == "skills":
            cls = self.classes.get(selections.get("class"))
            return int(_attr(cls, "skill_choices", 2)) if cls else 2
        return 0

    def build_pc(self, selections: dict) -> Combatant:
        name = str(selections.get("name", "Adventurer"))
        race = (self.races.get(selections.get("race"))
                or self.races.get(selections.get("ancestry"))
                or next(iter(self.races.values())))
        cls = (self.classes.get(selections.get("class"))
               or self.classes.get("fighter") or next(iter(self.classes.values())))
        assigned = dict(selections.get("abilities") or {})

        bonuses = _attr(race, "ability_bonuses", None) or _attr(race, "bonus", {}) or {}
        abilities = {a: assigned.get(a, 10) + bonuses.get(a, 0) for a in ABILITIES}
        pb = 2
        con_mod = self._ability_mod(abilities["con"])
        dex_mod = self._ability_mod(abilities["dex"])

        hit_die = _attr(cls, "hit_die", 8)
        max_hp = max(1, hit_die + con_mod)
        ac = _attr(cls, "ac_base", 12) + (dex_mod if _attr(cls, "ac_adds_dex", True) else 0)

        atk_ability = _attr(cls, "attack_ability", "str")
        atk_mod = self._ability_mod(abilities[atk_ability])
        wname, wdie = _attr(cls, "weapon", ("club", "1d4"))
        reach = _attr(cls, "reach", "melee")
        damage = wdie if atk_mod == 0 else f"{wdie}{atk_mod:+d}"
        attacks = [{"name": wname, "bonus": atk_mod + pb, "damage": damage, "reach": reach}]

        race_skills = tuple(_attr(race, "skills", ()) or ())
        skill_list = _attr(cls, "skill_list", None) or _attr(cls, "skills", ())
        skill_choices = int(_attr(cls, "skill_choices", len(skill_list) if skill_list else 0))
        chosen = selections.get("skills") or list(_attr(cls, "skills", ()) or ())
        if self._prof is not None:
            profs = self._prof.resolve_skill_proficiencies(skill_list, skill_choices, chosen, race_skills)
        else:
            profs, seen = [], set()
            for s in list(chosen)[:skill_choices] + list(race_skills):
                if s not in seen:
                    seen.add(s)
                    profs.append(s)

        bg = self.backgrounds.get(selections.get("background")) if self._bg else None
        for s in (tuple(_attr(bg, "skills", ()) or ()) if bg else ()):
            if s not in profs:
                profs.append(s)

        sheet = {
            "abilities": abilities,
            "proficiencies": profs,
            "proficiency_bonus": pb,
            "save_proficiencies": list(_attr(cls, "saving_throws", ())),
            "hp": max_hp, "max_hp": max_hp, "ac": ac,
            "attacks": attacks,
            "intelligence": 3,
            "comprehends_language": True, "mindless": False,
            "race": _attr(race, "label", selections.get("race", "")),
            "ancestry": _attr(race, "label", selections.get("race", "")),
            "class": _attr(cls, "label", selections.get("class", "")),
            "level": 1,
            "size": _attr(race, "size", "Medium"),
            "speed": _attr(race, "speed", 30),
            "darkvision": _attr(race, "darkvision", 0),
            "resistances": list(_attr(race, "resistances", ()) or ()),
            "languages": list(_attr(race, "languages", ("Common",)) or ("Common",)),
            "race_traits": [n for n, _ in _attr(race, "traits", ()) or ()],
            "class_features": [n for n, _ in _attr(cls, "features", ()) or ()],
        }

        sheet["class_key"] = selections.get("class") or ""
        sheet["race_key"] = selections.get("race") or selections.get("ancestry") or ""
        sheet["creature_type"] = "humanoid"
        sheet["hit_die"] = hit_die
        sheet["classes"] = [{"class_key": sheet["class_key"], "level": 1, "subclass": "",
                             "subclass_label": "", "hit_die": hit_die}]

        if bg is not None:
            feat = _attr(bg, "feature", ("", ""))
            sheet["background"] = _attr(bg, "label", "")
            sheet["background_key"] = selections.get("background") or ""
            sheet["tool_proficiencies"] = list(_attr(bg, "tools", ()) or ())
            sheet["background_languages"] = int(_attr(bg, "languages", 0) or 0)
            sheet["background_feature"] = {"name": feat[0], "text": feat[1]}
            seed = self._bg.roleplay_seed(bg)
            seed["chosen"] = {
                "trait": selections.get("trait") or _first(seed["suggested_traits"]),
                "ideal": selections.get("ideal") or _first(seed["suggested_ideals"]),
                "bond": selections.get("bond") or _first(seed["suggested_bonds"]),
                "flaw": selections.get("flaw") or _first(seed["suggested_flaws"]),
            }
            sheet["roleplay"] = seed

        al = selections.get("alignment")
        if al and self._align is not None:
            prof = self._align.profile(al, selections.get("presented_alignment"))
            if prof is not None:
                sheet["alignment"] = prof.true.label
                sheet["alignment_key"] = prof.true.key
                sheet["presented_alignment"] = prof.presented.label
                sheet["alignment_note"] = prof.narration_note()

        sc = _attr(cls, "spellcasting", None)
        if sc:
            sheet["spellcasting"] = self._spellcasting_block(sheet["class_key"] or "", sc, abilities, 1)

        if self._leveling is not None:
            lv = self._leveling.derive_level(sheet["class_key"] or "fighter", 1, hit_die, sc, abilities)
            sheet["spell_slots"] = lv["spell_slots"]
            sheet["class_resources"] = lv["class_resources"]
            sheet["asi_pending"] = lv["asi_pending"]
            sheet["spell_slots_remaining"] = dict(lv["spell_slots"])
            sheet["resources_remaining"] = self._leveling.spendable_pools(lv["class_resources"])
        else:
            sheet["spell_slots_remaining"] = {}
            sheet["resources_remaining"] = {}

        sheet["gold"] = _STARTING_GOLD.get(sheet["class_key"], 75)
        sheet["inventory"] = []
        sheet["equipped"] = {}
        sheet["hit_dice_total"] = sheet.get("level", 1)
        sheet["hit_dice_remaining"] = sheet.get("level", 1)

        self._init_profile(sheet, selections)

        return Combatant(name=name, is_pc=True, sheet=sheet)

    def _init_profile(self, sheet: dict, selections: dict | None = None) -> None:
        sel = selections or {}
        if self._gender is not None:
            self._gender.init(sheet, sel.get("gender", "androgynous"))
        for ext in self.extensions:
            ext.init_profile(sheet, sel)

    def _ensure_profile(self, actor: Combatant) -> None:
        if self._gender is not None and not self._gender.has(actor.sheet):
            self._gender.init(actor.sheet)
        for ext in self.extensions:
            ext.ensure_profile(actor)

    def save_modifier(self, actor: Combatant, ability: str) -> int:
        score = actor.sheet.get("abilities", {}).get(ability, 10)
        proficient = ability in actor.sheet.get("save_proficiencies", [])
        pb = actor.sheet.get("proficiency_bonus", 2)
        return self._ability_mod(score) + (pb if proficient else 0)

    def list_races(self) -> list[str]:
        return [k for k in self._race_order if k in self.races]

    def list_classes(self) -> list[str]:
        return [k for k in self._class_order if k in self.classes]

    def list_alignments(self) -> list[str]:
        return list(self._align_order)

    def class_info(self, key: str):
        return self.classes.get(key)

    def race_info(self, key: str):
        return self.races.get(key)

    def list_backgrounds(self) -> list[str]:
        return [k for k in self._bg_order if k in self.backgrounds]

    def background_info(self, key: str):
        return self.backgrounds.get(key)

    def _normalize_classes(self, sheet: dict) -> list:
        classes = sheet.get("classes")
        if not classes:
            ck = sheet.get("class_key", "") or ""
            cls = self.classes.get(ck)
            classes = [{
                "class_key": ck,
                "level": int(sheet.get("level", 1)),
                "subclass": sheet.get("subclass", "") or "",
                "subclass_label": sheet.get("subclass_label", "") or "",
                "hit_die": int(sheet.get("hit_die") or _attr(cls, "hit_die", 8)),
            }]
            sheet["classes"] = classes
        return classes

    def _sync_primary_mirror(self, sheet: dict) -> None:
        classes = sheet.get("classes") or []
        if not classes:
            return
        primary = classes[0]
        ck = primary.get("class_key", "")
        cls = self.classes.get(ck)
        sheet["class_key"] = ck
        if cls is not None:
            sheet["class"] = _attr(cls, "label", sheet.get("class", ""))
        sheet["subclass"] = primary.get("subclass", "")
        sheet["subclass_label"] = primary.get("subclass_label", "")
        sheet["hit_die"] = int(primary.get("hit_die") or _attr(cls, "hit_die", 8))
        tot = (self._leveling.total_level(classes) if self._leveling is not None
               else min(20, sum(int(c.get("level", 0)) for c in classes)))
        sheet["level"] = tot
        sheet["hit_dice_total"] = tot

    def _recompute_sheet(self, actor: Combatant) -> Combatant:
        if self._leveling is None:
            return actor
        sheet = actor.sheet
        classes = self._normalize_classes(sheet)
        lev = self._leveling
        abilities = sheet.get("abilities", {})
        con_mod = self._ability_mod(abilities.get("con", 10))
        tot = lev.total_level(classes)
        pb = lev.proficiency_bonus(tot)

        old_max = sheet.get("max_hp")
        new_max = lev.multiclass_max_hp(classes, con_mod)
        if old_max is None:
            old_max = new_max
        sheet["max_hp"] = new_max
        sheet["hp"] = max(1, sheet.get("hp", new_max) + max(0, new_max - old_max))
        sheet["level"] = tot
        sheet["proficiency_bonus"] = pb

        features = lev.feature_union(classes)
        if self._subclasses is not None:
            seen = set(features)
            for c in classes:
                sub = c.get("subclass")
                if not sub:
                    continue
                for name, _ in self._subclasses.cumulative_subclass_features(
                        c.get("class_key", ""), sub, int(c.get("level", 0))):
                    if name not in seen:
                        seen.add(name)
                        features.append(name)
        sheet["class_features"] = features

        resources = lev.merge_class_resources(classes, abilities)
        sheet["class_resources"] = resources
        slots = dict(lev.multiclass_spell_slots(classes))
        slots.update(lev.pact_slots_for(classes))
        sheet["spell_slots"] = slots
        sheet["asi_pending"] = sum(lev.asi_count(c.get("class_key", ""), int(c.get("level", 0)))
                                   for c in classes)
        sheet["spell_slots_remaining"] = dict(slots)
        sheet["resources_remaining"] = lev.spendable_pools(resources)

        primary_cls = self.classes.get(classes[0].get("class_key", ""))
        atk_ability = _attr(primary_cls, "attack_ability", "str")
        atk_mod = self._ability_mod(abilities.get(atk_ability, 10))
        wname, wdie = _attr(primary_cls, "weapon", ("club", "1d4"))
        reach = _attr(primary_cls, "reach", "melee")
        damage = wdie if atk_mod == 0 else f"{wdie}{atk_mod:+d}"
        sheet["attacks"] = [{"name": wname, "bonus": atk_mod + pb, "damage": damage, "reach": reach}]
        sheet["attacks_per_action"] = resources.get("attacks_per_action", 1)

        caster = next((c for c in classes
                       if _attr(self.classes.get(c.get("class_key", "")), "spellcasting", None)), None)
        if caster is not None and self._prof is not None:
            sc = _attr(self.classes.get(caster.get("class_key", "")), "spellcasting", None)
            sheet["spellcasting"] = self._spellcasting_block(
                caster.get("class_key", ""), sc, abilities, int(caster.get("level", 1)),
                total_level=tot)
        self._sync_primary_mirror(sheet)
        return actor

    def advance_to_level(self, actor: Combatant, level: int) -> Combatant:
        if self._leveling is None:
            return actor
        classes = self._normalize_classes(actor.sheet)
        if self.classes.get(classes[0].get("class_key")) is None and len(classes) == 1:
            return actor
        level = max(1, min(20, int(level)))
        if len(classes) == 1:
            classes[0]["level"] = level
        return self._recompute_sheet(actor)

    def level_up(self, actor: Combatant) -> Combatant:
        return self.advance_to_level(actor, int(actor.sheet.get("level", 1)) + 1)

    def class_progression(self, class_key: str) -> list:
        cls = self.classes.get(class_key)
        if cls is None or self._leveling is None:
            return []
        return self._leveling.progression(class_key, _attr(cls, "hit_die", 8),
                                          _attr(cls, "spellcasting", None))

    EXPERTISE_LEVELS = {"rogue": (1, 6), "bard": (3, 10)}

    def list_subclasses(self, class_key: str) -> dict:
        return self._subclasses.subclasses_for(class_key) if self._subclasses is not None else {}

    def subclass_choice_level(self, class_key: str) -> int:
        return self._subclasses.subclass_level(class_key) if self._subclasses is not None else 3

    def _known_spell_delta(self, class_key: str, target_level: int) -> int:
        if self._spells is None:
            return 0
        cls = self.classes.get(class_key)
        sc = _attr(cls, "spellcasting", None) if cls else None
        if not sc:
            return 0
        here = self._spells.spells_known_or_prepared(class_key, target_level)
        if here.get("method") != "known":
            return 0
        before = self._spells.spells_known_or_prepared(class_key, max(1, target_level - 1))
        return max(0, int(here.get("spells", 0)) - int(before.get("spells", 0)))

    def _compute_level_slots(self, class_key: str, target_level: int, sheet: dict,
                             class_entry: dict | None = None) -> list:
        slots = []
        subs = self._subclasses
        has_subclass = bool(class_entry.get("subclass")) if class_entry is not None else bool(sheet.get("subclass"))
        if subs is not None and subs.has_subclasses(class_key) \
                and target_level == subs.subclass_level(class_key) and not has_subclass:
            slots.append({"key": "subclass", "kind": "subclass",
                          "label": f"Choose your {subs.subclass_noun(class_key)}", "choose": 1,
                          "options": [{"id": s["key"], "label": s["label"], "desc": s["blurb"]}
                                      for s in subs.subclasses_for(class_key).values()]})
        if self._leveling is not None and target_level in self._leveling.asi_levels(class_key):
            labels = ABILITY_LABELS if "ABILITY_LABELS" in globals() else {}
            slots.append({"key": "asi", "kind": "asi",
                          "label": "Ability Score Improvement (+2 to one ability)", "choose": 1,
                          "options": [{"id": a, "label": labels.get(a, a.upper()),
                                       "desc": f"Raise {labels.get(a, a.upper())} by 2 (max 20)."}
                                      for a in ("str", "dex", "con", "int", "wis", "cha")]})
        if target_level in self.EXPERTISE_LEVELS.get(class_key, ()):
            prof = [p for p in sheet.get("proficiencies", []) if p in SKILLS]
            already = set(sheet.get("expertise", []))
            opts = [p for p in prof if p not in already]
            slots.append({"key": "expertise", "kind": "expertise",
                          "label": "Expertise (double proficiency on two skills)", "choose": 2,
                          "options": [{"id": s, "label": SKILLS.get(s, s).title() if isinstance(SKILLS.get(s), str)
                                       else s.replace("_", " ").title(), "desc": ""} for s in opts]})
        delta = self._known_spell_delta(class_key, target_level)
        if delta and self._spells is not None:
            known = set((sheet.get("spellcasting", {}) or {}).get("known", []))
            opts = [k for k in self._spells.spell_keys_for_class(class_key, min_level=1)
                    if k not in known]
            slots.append({"key": "spells", "kind": "spells",
                          "label": f"Learn {delta} new spell{'s' if delta != 1 else ''}", "choose": delta,
                          "options": [{"id": k, "label": k.replace("_", " ").title(), "desc": ""}
                                      for k in opts]})
        return slots

    def _class_choice_slot(self, sheet: dict) -> dict:
        classes = self._normalize_classes(sheet)
        tot = self._leveling.total_level(classes) if self._leveling is not None else 0
        options, taken = [], {c.get("class_key") for c in classes}
        for c in classes:
            ck = c.get("class_key", "")
            if int(c.get("level", 0)) >= 20:
                continue
            cls = self.classes.get(ck)
            options.append({"id": f"advance:{ck}",
                            "label": f"{_attr(cls, 'label', ck.title())} {int(c.get('level', 0)) + 1}",
                            "desc": "Continue in this class."})
        if tot < 20:
            for ck in self.list_classes():
                if ck in taken:
                    continue
                cls = self.classes.get(ck)
                options.append({"id": f"new:{ck}", "label": f"{_attr(cls, 'label', ck.title())} (new)",
                                "desc": "Take your first level in a new class."})
        return {"key": "class", "kind": "class", "label": "Which class advances?", "choose": 1,
                "options": options}

    def _populate_pending_for_class(self, sheet: dict, pending: dict) -> None:
        classes = self._normalize_classes(sheet)
        ck = pending["class_key"]
        entry = None if pending.get("is_new_class") else next(
            (c for c in classes if c.get("class_key") == ck), None)
        class_target = 1 if pending.get("is_new_class") else int((entry or {}).get("level", 0)) + 1
        pending["class_target_level"] = class_target
        pending["slots"] = [self._class_choice_slot(sheet)] + \
            self._compute_level_slots(ck, class_target, sheet, class_entry=entry)
        pending["choices"] = {"class": (f"new:{ck}" if pending.get("is_new_class") else f"advance:{ck}")}

    def award_level_up(self, actor: Combatant):
        sheet = actor.sheet
        if self._leveling is None:
            return None
        classes = self._normalize_classes(sheet)
        tot = self._leveling.total_level(classes)
        if tot >= 20:
            return None
        if sheet.get("pending_level_up"):
            return sheet["pending_level_up"]
        pending = {"target_total_level": tot + 1, "class_key": classes[0].get("class_key", ""),
                   "is_new_class": False}
        self._populate_pending_for_class(sheet, pending)
        sheet["pending_level_up"] = pending
        return pending

    def cancel_level_up(self, actor: Combatant) -> bool:
        return actor.sheet.pop("pending_level_up", None) is not None

    def _slots_ready(self, pending: dict) -> bool:
        for s in pending.get("slots", []):
            chosen = pending.get("choices", {}).get(s["key"])
            need = s.get("choose", 1)
            if need <= 1:
                if not chosen:
                    return False
            elif not isinstance(chosen, list) or len(chosen) < need:
                return False
        return True

    def set_level_choice(self, actor: Combatant, slot_key: str, value):
        pending = actor.sheet.get("pending_level_up")
        if not pending:
            return None
        sheet = actor.sheet
        if slot_key == "class":
            slot = next((s for s in pending["slots"] if s["key"] == "class"), None)
            valid = {o["id"] for o in slot["options"]} if slot else set()
            if value not in valid:
                return self.level_up_state(actor)
            prev = {k: v for k, v in pending.get("choices", {}).items() if k != "class"}
            mode, _, ck = value.partition(":")
            pending["class_key"] = ck
            pending["is_new_class"] = (mode == "new")
            self._populate_pending_for_class(sheet, pending)
            for s in pending["slots"]:
                if s["key"] not in prev:
                    continue
                ids = {o["id"] for o in s["options"]}
                pv = prev[s["key"]]
                if isinstance(pv, list):
                    keep = [x for x in pv if x in ids]
                    if keep:
                        pending["choices"][s["key"]] = keep
                elif pv in ids:
                    pending["choices"][s["key"]] = pv
            return self.level_up_state(actor)
        slot = next((s for s in pending["slots"] if s["key"] == slot_key), None)
        if slot is None:
            return self.level_up_state(actor)
        valid = {o["id"] for o in slot["options"]}
        if slot.get("choose", 1) > 1:
            picked = [v for v in (value or []) if v in valid][: slot["choose"]]
            pending["choices"][slot_key] = picked
        else:
            pending["choices"][slot_key] = value if value in valid else None
        return self.level_up_state(actor)

    def level_up_state(self, actor: Combatant) -> dict:
        sheet = actor.sheet
        classes = self._normalize_classes(sheet)
        pending = sheet.get("pending_level_up")
        primary = classes[0]
        pck = primary.get("class_key", "")
        tot = (self._leveling.total_level(classes) if self._leveling is not None
               else int(sheet.get("level", 1)))
        class_views = [{
            "class_key": c.get("class_key", ""),
            "label": _attr(self.classes.get(c.get("class_key", "")), "label",
                           c.get("class_key", "").title()),
            "level": int(c.get("level", 0)),
            "subclass": c.get("subclass", ""),
            "subclass_label": c.get("subclass_label", ""),
        } for c in classes]
        return {
            "name": actor.name,
            "class_key": pck,
            "class_label": _attr(self.classes.get(pck), "label", sheet.get("class", "")),
            "level": tot,
            "total_level": tot,
            "subclass": primary.get("subclass", ""),
            "subclass_label": primary.get("subclass_label", ""),
            "classes": class_views,
            "available": bool(pending),
            "target_level": pending["target_total_level"] if pending else None,
            "chosen_class": pending["class_key"] if pending else None,
            "class_target_level": pending.get("class_target_level") if pending else None,
            "is_new_class": bool(pending.get("is_new_class")) if pending else False,
            "slots": pending["slots"] if pending else [],
            "choices": pending["choices"] if pending else {},
            "ready": self._slots_ready(pending) if pending else False,
        }

    def apply_pending_level_up(self, actor: Combatant) -> dict | None:
        sheet = actor.sheet
        pending = sheet.get("pending_level_up")
        if not pending or self._leveling is None:
            return None
        classes = self._normalize_classes(sheet)
        ck = pending["class_key"]
        ch = dict(pending.get("choices", {}))
        from_level = self._leveling.total_level(classes)

        if pending.get("is_new_class"):
            entry = {"class_key": ck, "level": 1, "subclass": "", "subclass_label": "",
                     "hit_die": _attr(self.classes.get(ck), "hit_die", 8)}
            classes.append(entry)
        else:
            entry = next((c for c in classes if c.get("class_key") == ck), None)
            if entry is None:
                entry = {"class_key": ck, "level": 1, "subclass": "", "subclass_label": "",
                         "hit_die": _attr(self.classes.get(ck), "hit_die", 8)}
                classes.append(entry)
            else:
                entry["level"] = int(entry.get("level", 0)) + 1
        applied = {"name": actor.name, "from": from_level,
                   "to": self._leveling.total_level(classes), "gained": []}
        if pending.get("is_new_class"):
            applied["gained"].append(_attr(self.classes.get(ck), "label", ck.title()) + " level 1")

        asi_slot = next((s for s in pending["slots"] if s["key"] == "asi"), None)
        if asi_slot is not None:
            a = ch.get("asi") or asi_slot["options"][0]["id"]
            ab = sheet.setdefault("abilities", {})
            ab[a] = min(20, int(ab.get(a, 10)) + 2)
            applied["gained"].append(f"+2 {a.upper()}")

        sub_slot = next((s for s in pending["slots"] if s["key"] == "subclass"), None)
        if sub_slot is not None and self._subclasses is not None:
            sk = ch.get("subclass") or sub_slot["options"][0]["id"]
            entry["subclass"] = sk
            entry["subclass_label"] = self._subclasses.subclass_label(ck, sk)
            applied["gained"].append(entry["subclass_label"])

        self._recompute_sheet(actor)

        exp_slot = next((s for s in pending["slots"] if s["key"] == "expertise"), None)
        if exp_slot is not None:
            picks = ch.get("expertise") or [o["id"] for o in exp_slot["options"][:exp_slot["choose"]]]
            ex = sheet.setdefault("expertise", [])
            for p in picks:
                if p not in ex:
                    ex.append(p)
            if picks:
                applied["gained"].append("Expertise: " + ", ".join(picks))

        sp_slot = next((s for s in pending["slots"] if s["key"] == "spells"), None)
        if sp_slot is not None:
            sc = sheet.get("spellcasting", {}) or {}
            picks = ch.get("spells") or [o["id"] for o in sp_slot["options"][:sp_slot["choose"]]]
            sc["known"] = list(dict.fromkeys(list(sc.get("known", [])) + list(picks)))
            sheet["spellcasting"] = sc
            if picks:
                applied["gained"].append(f"Learned {len(picks)} spell(s)")

        sheet.pop("pending_level_up", None)
        return applied

    def creature_type(self, actor: Combatant) -> str:
        return actor.sheet.get("creature_type", "humanoid")

    def detect_evil_and_good(self, target: Combatant):
        return self._align.detect_evil_and_good(self.creature_type(target)) if self._align else None

    def protection_from_evil_and_good(self, attacker: Combatant) -> bool:
        return self._align.protection_disadvantage(self.creature_type(attacker)) if self._align else False

    def magic_circle_blocks(self, configured_type: str, target: Combatant) -> bool:
        return (self._align.magic_circle_blocks(configured_type, self.creature_type(target))
                if self._align else False)

    def attune_item(self, actor: Combatant, item_key: str):
        return (self._align.item_attunement(actor.sheet.get("alignment_key"), item_key)
                if self._align else None)

    def sentient_item_conflict(self, actor: Combatant, item_alignment_key: str):
        return (self._align.sentient_item_conflict(actor.sheet.get("alignment_key"), item_alignment_key)
                if self._align else None)

    def _spellcasting_block(self, class_key: str, sc, abilities: dict, level: int,
                            total_level: int | None = None) -> dict:
        sc_type, sc_ability = sc
        score = abilities.get(sc_ability, 10)
        block = {"type": sc_type, "ability": sc_ability}
        if self._prof is not None:
            block.update(self._prof.spell_stats(score, total_level if total_level is not None else level))
        if self._spells is not None and class_key:
            rep = self._spells.spells_known_or_prepared(class_key, level, self._ability_mod(score))
            block.update(cantrips_known=rep["cantrips"], spells_method=rep["method"],
                         spells_count=rep["spells"])
        return block

    def class_spell_list(self, class_key: str) -> dict:
        if self._spells is None:
            return {}
        return {lvl: [(s.name, s.school, s.desc) for s in row]
                for lvl, row in self._spells.by_level(class_key).items()}

    def available_spells(self, actor: Combatant) -> dict:
        return self.class_spell_list(actor.sheet.get("class_key", ""))

    def spell_info(self, key: str):
        return self._spells.get(key) if self._spells is not None else None

    def prepare_spells(self, actor: Combatant, spell_keys) -> list | None:
        sc = actor.sheet.get("spellcasting")
        if not sc or sc.get("spells_method") != "prepared" or self._spells is None:
            return None
        ck = actor.sheet.get("class_key", "")
        allowed = self._spells.spell_keys_for_class(ck, min_level=1)
        sc["prepared"] = self._spells.validate_selection(spell_keys, allowed, sc.get("spells_count", 0))
        return sc["prepared"]

    def set_known_spells(self, actor: Combatant, spell_keys) -> list | None:
        sc = actor.sheet.get("spellcasting")
        if not sc or sc.get("spells_method") != "known" or self._spells is None:
            return None
        ck = actor.sheet.get("class_key", "")
        allowed = self._spells.spell_keys_for_class(ck, min_level=1)
        sc["known"] = self._spells.validate_selection(spell_keys, allowed, sc.get("spells_count", 0))
        return sc["known"]

    def set_cantrips(self, actor: Combatant, cantrip_keys) -> list | None:
        sc = actor.sheet.get("spellcasting")
        if not sc or self._spells is None:
            return None
        ck = actor.sheet.get("class_key", "")
        allowed = self._spells.cantrip_keys_for_class(ck)
        sc["cantrips"] = self._spells.validate_selection(cantrip_keys, allowed, sc.get("cantrips_known", 0))
        return sc["cantrips"]

    def _spell_level_of(self, spell_key: str) -> int:
        sp = self.spell_info(spell_key)
        return sp.level if sp is not None else 1

    def cast_spell(self, actor: Combatant, spell_key: str | None = None, *, level: int | None = None) -> dict:
        sheet = actor.sheet
        need = level if level is not None else (self._spell_level_of(spell_key) if spell_key else 1)
        if need <= 0:
            return {"cast": True, "slot_used": 0, "remaining": sheet.get("spell_slots_remaining", {})}
        rem = sheet.setdefault("spell_slots_remaining", dict(sheet.get("spell_slots", {})))
        if "pact_slots" in rem:
            if rem.get("pact_slots", 0) > 0 and need <= rem.get("pact_slot_level", 9):
                rem["pact_slots"] -= 1
                return {"cast": True, "slot_used": rem.get("pact_slot_level"), "remaining": rem}
            return {"cast": False, "slot_used": None, "remaining": rem}
        for lvl in range(need, 10):
            key = f"level_{lvl}"
            if rem.get(key, 0) > 0:
                rem[key] -= 1
                return {"cast": True, "slot_used": lvl, "remaining": rem}
        return {"cast": False, "slot_used": None, "remaining": rem}

    def spend_slot(self, actor: Combatant, level: int) -> bool:
        return self.cast_spell(actor, level=level)["cast"]

    def spend_resource(self, actor: Combatant, name: str, amount: int = 1) -> bool:
        rem = actor.sheet.setdefault("resources_remaining", {})
        have = rem.get(name)
        if not isinstance(have, int) or have < amount:
            return False
        rem[name] = have - amount
        return True

    def resource_remaining(self, actor: Combatant, name: str):
        return actor.sheet.get("resources_remaining", {}).get(name)

    def short_rest(self, actor: Combatant, *, spend_hit_dice: int = 0) -> dict:
        sheet = actor.sheet
        cr = sheet.get("class_resources", {})
        rem = sheet.setdefault("resources_remaining", {})
        refreshed = []
        if self._leveling is not None:
            for k in self._leveling.SHORT_REST_RESOURCES:
                if k in cr and isinstance(cr[k], int):
                    rem[k] = cr[k]
                    refreshed.append(k)
        slots = sheet.get("spell_slots_remaining", {})
        if "pact_slots" in slots:
            slots["pact_slots"] = sheet.get("spell_slots", {}).get("pact_slots", slots["pact_slots"])
            refreshed.append("pact_slots")
        healed = dice_spent = 0
        if spend_hit_dice > 0:
            sheet.setdefault("hit_dice_total", sheet.get("level", 1))
            avail = int(sheet.get("hit_dice_remaining", sheet.get("hit_dice_total", sheet.get("level", 1))))
            hd = sheet.get("hit_die", 8)
            con = self._ability_mod(sheet.get("abilities", {}).get("con", 10))
            mx = sheet.get("max_hp", sheet.get("hp", 1))
            to_spend = max(0, min(spend_hit_dice, avail))
            for _ in range(to_spend):
                if sheet.get("hp", 0) >= mx:
                    break
                healed += max(1, self.dice.roll(hd) + con)
                dice_spent += 1
            sheet["hp"] = min(mx, sheet.get("hp", 0) + healed)
            sheet["hit_dice_remaining"] = avail - dice_spent
        msg = f"{actor.name} takes a short rest"
        if dice_spent:
            msg += f", spending {dice_spent} hit di{'e' if dice_spent==1 else 'ce'} to recover {healed} HP"
        elif refreshed:
            msg += " and recovers their breath"
        return {"name": actor.name, "refreshed": refreshed, "healed": healed,
                "hit_dice_spent": dice_spent,
                "hit_dice_remaining": sheet.get("hit_dice_remaining", sheet.get("level", 1)),
                "message": msg + "."}

    def long_rest(self, actor: Combatant, prepared=None, *, allowed: bool = True) -> dict:
        sheet = actor.sheet
        if not allowed:
            return {"name": actor.name, "rested": False, "healed": 0,
                    "message": f"{actor.name} can't bed down here without drawing attention."}
        before = sheet.get("hp", 0)
        healed = max(0, sheet.get("max_hp", before) - before)
        sheet["hp"] = sheet.get("max_hp", before)
        sheet["spell_slots_remaining"] = dict(sheet.get("spell_slots", {}) or {})
        sheet["resources_remaining"] = (self._leveling.spendable_pools(sheet.get("class_resources", {}))
                                        if self._leveling is not None else {})
        reprepared = False
        sc = sheet.get("spellcasting")
        if sc and prepared is not None and sc.get("spells_method") == "prepared":
            self.prepare_spells(actor, prepared)
            reprepared = True
        self._advance_world_clock()
        if self._gender is not None:
            self._gender.settle(sheet)
        for ext in self.extensions:
            ext.on_long_rest(actor)
        leveled = self.apply_pending_level_up(actor)
        result = {"name": actor.name, "rested": True, "healed": healed,
                  "slots_restored": bool(sheet["spell_slots_remaining"]),
                  "reprepared": reprepared,
                  "message": f"{actor.name} takes a long rest"
                             + (f", recovering {healed} HP" if healed else ", already at full health")
                           + (" and re-preparing spells" if reprepared else "") + "."}
        if leveled:
            result["leveled_up"] = leveled
            gained = (" \u2014 gained " + ", ".join(leveled["gained"])) if leveled.get("gained") else ""
            result["message"] = (result["message"].rstrip(".")
                                 + f". {actor.name} reaches level {leveled['to']}{gained}.")
        return result

    def list_settings(self) -> list[str]:
        return list(self._setting_order)

    def setting_info(self, key: str):
        return self.settings.get(key)

    def use_setting(self, key: str) -> bool:
        s = self.settings.get(key)
        if s is None:
            return False
        self.setting = s
        return True

    def current_setting(self):
        return self.setting

    def world_brief(self) -> str:
        return self.setting.narration_brief() if self.setting is not None else ""

    def location(self, key: str):
        return self.setting.location(key) if self.setting is not None else None

    def npc(self, key: str):
        return self.setting.npc(key) if self.setting is not None else None

    def _setting_mod(self, name: str):
        if self.setting is None:
            return None
        return self.setting.submodule(name)

    def npc_sheet(self, key: str):
        mod = self._setting_mod("npcs")
        return mod.npc_sheet(key) if mod is not None else None

    def build_npc(self, key: str):
        mod = self._setting_mod("npcs")
        if mod is None:
            return None
        c = mod.build_npc(key)
        if c is not None:
            self._ensure_profile(c)
        return c

    def list_locations(self) -> list[str]:
        return self.setting.list_locations() if self.setting is not None else []

    def list_npcs(self) -> list[str]:
        return self.setting.list_npcs() if self.setting is not None else []

    def item_info(self, key: str):
        return self._items.get(key) if self._items is not None else None

    def inventory_names(self, actor: Combatant) -> list:
        sheet = getattr(actor, "sheet", {}) or {}
        keys = list(sheet.get("inventory", []) or []) + list((sheet.get("equipped") or {}).values())
        names = []
        for k in keys:
            info = self.item_info(k)
            nm = getattr(info, "name", None) or (info.get("name") if isinstance(info, dict) else None)
            names.append(nm or str(k).replace("_", " "))
        return names

    def grant_item(self, actor: Combatant, item_key: str) -> bool:
        if self._items is not None and self._items.get(item_key) is None:
            return False
        actor.sheet.setdefault("inventory", []).append(item_key)
        return True

    def build_scene(self, key: str):
        mod = self._setting_mod("scenes")
        if mod is None:
            return None
        scene = mod.build(key, lambda name, **kw: self.make_enemy(name, **kw))
        if scene is not None:
            for ext in self.extensions:
                ext.on_scene_built(key, scene)
        return scene

    def list_scenes(self) -> list:
        mod = self._setting_mod("scenes")
        return mod.list_scenes() if mod is not None else []

    def build_adventure(self, key: str):
        mod = self._setting_mod("stories")
        return mod.build(key) if mod is not None else None

    def list_adventures(self) -> list:
        mod = self._setting_mod("stories")
        return mod.list_adventures() if mod is not None else []

    def list_tradesmen(self) -> list[str]:
        return self.setting.list_tradesmen() if self.setting is not None else []

    def tradesman_info(self, key: str):
        return self.setting.tradesman(key) if self.setting is not None else None

    def build_trader(self, key: str):
        mod = self._setting_mod("tradesmen")
        if mod is None:
            return None
        c = mod.build_trader(key)
        if c is not None:
            self._ensure_profile(c)
        return c

    def open_shops(self, seed: int | None = None) -> None:
        import random as _random
        if seed is not None:
            self._shop_rng = _random.Random(seed)
        self.shops = {}
        for tk in self.list_tradesmen():
            self.shops[tk] = self._trade.generate_stock(self.tradesman_info(tk), rng=self._shop_rng)

    def shop_stock(self, tradesman_key: str) -> list:
        if self._trade is None or self.tradesman_info(tradesman_key) is None:
            return []
        if tradesman_key not in self.shops:
            self.shops[tradesman_key] = self._trade.generate_stock(
                self.tradesman_info(tradesman_key), rng=self._shop_rng)
        return self.shops[tradesman_key]

    def shop_listing(self, tradesman_key: str) -> list:
        t = self.tradesman_info(tradesman_key)
        if t is None:
            return []
        out = []
        for key in self.shop_stock(tradesman_key):
            it = self._items.get(key)
            if it is not None:
                out.append((it, self._trade.price_to_buy(it, t.markup)))
        return out

    def price_quote(self, item_key: str, tradesman_key: str, *, selling: bool = False) -> int | None:
        it = self._items.get(item_key) if self._items is not None else None
        t = self.tradesman_info(tradesman_key)
        if it is None or t is None:
            return None
        return (self._trade.price_to_sell(it, t.sell_rate) if selling
                else self._trade.price_to_buy(it, t.markup))

    def buy(self, actor: Combatant, item_key: str, tradesman_key: str) -> dict:
        t = self.tradesman_info(tradesman_key)
        it = self._items.get(item_key) if self._items is not None else None
        if t is None or it is None:
            return {"ok": False, "message": "No such item or merchant."}
        stock = self.shop_stock(tradesman_key)
        if item_key not in stock:
            return {"ok": False, "message": f"{t.name} doesn't have that in stock."}
        price = self._trade.price_to_buy(it, t.markup)
        gold = actor.sheet.get("gold", 0)
        if gold < price:
            return {"ok": False, "message": f"You can't afford {it.name} ({price} gp; you have {gold})."}
        actor.sheet["gold"] = gold - price
        actor.sheet.setdefault("inventory", []).append(item_key)
        stock.remove(item_key)
        return {"ok": True, "item": it.name, "price": price, "gold_left": actor.sheet["gold"],
                "message": f"You buy {it.name} from {t.name} for {price} gp."}

    def sell(self, actor: Combatant, item_key: str, tradesman_key: str) -> dict:
        t = self.tradesman_info(tradesman_key)
        it = self._items.get(item_key) if self._items is not None else None
        if t is None or it is None:
            return {"ok": False, "message": "No such item or merchant."}
        inv = actor.sheet.setdefault("inventory", [])
        if item_key not in inv:
            return {"ok": False, "message": f"You don't have {it.name} to sell."}
        if it.plot:
            return {"ok": False, "message": f"{t.name} won't touch that -- it's not something to be sold."}
        price = self._trade.price_to_sell(it, t.sell_rate)
        inv.remove(item_key)
        actor.sheet["gold"] = actor.sheet.get("gold", 0) + price
        stock = self.shop_stock(tradesman_key)
        if item_key not in stock:
            stock.append(item_key)
        return {"ok": True, "item": it.name, "price": price, "gold_left": actor.sheet["gold"],
                "message": f"You sell {it.name} to {t.name} for {price} gp."}

    def haggle_approaches(self) -> list[str]:
        base = ["persuasion", "intimidation"]
        for ext in self.extensions:
            base += [a for a in ext.haggle_approaches() if a not in base]
        return base

    def haggle_cues(self) -> list:
        return [cue for ext in self.extensions for cue in ext.haggle_cues()]

    def haggle(self, actor: Combatant, item_key: str, tradesman_key: str, *,
               selling: bool = False, approach: str = "persuasion") -> dict:
        it = self._items.get(item_key) if self._items is not None else None
        t = self.tradesman_info(tradesman_key)
        if it is None or t is None:
            return {"ok": False, "message": "No such item or merchant."}
        approach = approach.lower()
        if approach not in self.haggle_approaches():
            approach = "persuasion"
        base = (self._trade.price_to_sell(it, t.sell_rate) if selling
                else self._trade.price_to_buy(it, t.markup))
        terms = next((t for t in (ext.haggle_terms(actor, approach) for ext in self.extensions)
                      if t is not None), None)
        mod = terms["modifier"] if terms is not None else self.modifier_for(actor, approach)
        roll = self.dice.roll(20)
        dc = 12 + int(round((t.markup - 1.0) * 10))
        margin = (roll + mod) - dc
        waived = False
        if roll == 1:
            tier = -0.10
        elif margin < 0:
            tier = 0.0
        elif margin < 5:
            tier = 0.10
        elif margin < 10:
            tier = 0.20
        else:
            tier = 0.30
        if terms is not None:
            tier = min(0.5, tier + float(terms.get("swing", 0.0)))
            wm = terms.get("waive_margin")
            if wm is not None and (roll == 20 or margin >= wm):
                waived = True
        if selling:
            price = int(round(base * (1 + tier)))
        else:
            price = 0 if waived else int(round(base * (1 - tier)))
        return {"ok": True, "approach": approach, "selling": selling, "roll": roll, "modifier": mod,
                "dc": dc, "margin": margin, "base_price": base, "price": max(0, price),
                "discount_pct": int(round(tier * 100)), "waived": waived,
                "style": (terms or {}).get("style", "check"),
                "message": (f"{t.name} agrees to {price} gp" if not waived
                            else f"{t.name} waives the price")}

    def restock_shops(self, force: bool = False) -> list:
        restocked = []
        for tk in self.list_tradesmen():
            t = self.tradesman_info(tk)
            interval = max(1, int(getattr(t, "restock_interval", 3) or 3))
            if force or (self._rest_count > 0 and self._rest_count % interval == 0):
                self.shops[tk] = self._trade.restock(self.shop_stock(tk), t, rng=self._shop_rng)
                restocked.append(tk)
        return restocked

    def _advance_world_clock(self) -> None:
        self._rest_count += 1
        if self._trade is not None and self.setting is not None:
            self.restock_shops()

    _URBAN_KINDS = {"street", "harbor", "market", "temple", "ward", "plaza"}
    _INN_KINDS = {"tavern", "inn"}
    _WILD_KINDS = {"forest", "ruin", "tower", "road", "camp", "wild", "cave", "dungeon"}

    def rest_context(self, location: str) -> dict:
        loc = (location or "").lower()
        if self.setting is not None:
            for lkey, lobj in self.setting.locations.items():
                if lkey in loc or lobj.name.lower() in loc:
                    kind = (lobj.kind or "").lower()
                    if kind in self._INN_KINDS:
                        return {"in_settlement": True, "at_inn": True}
                    if kind in self._URBAN_KINDS:
                        return {"in_settlement": True, "at_inn": False}
                    if kind in self._WILD_KINDS:
                        return {"in_settlement": False, "at_inn": False}
        at_inn = any(w in loc for w in ("inn", "tavern", "room", "common room"))
        wild = any(w in loc for w in ("forest", "wood", "camp", "road", "wilds", "wilderness",
                                      "ruin", "cave", "dungeon", "mountain", "field", "moor"))
        in_settlement = (not wild) and any(
            w in loc for w in ("city", "town", "village", "street", "ward", "market", "square",
                               "waterdeep", "baldur", "neverwinter", "gate", "alley", "harbor",
                               "dock", "tavern", "inn"))
        if at_inn:
            return {"in_settlement": True, "at_inn": True}
        return {"in_settlement": bool(in_settlement), "at_inn": False}

    _REST_WARNINGS = 2
    _REST_FINE = 5

    def rest_attempt(self, actor: Combatant, *, in_settlement: bool = False,
                     at_inn: bool = False, attempts: int = 0) -> dict:
        if not in_settlement or at_inn:
            rest = self.long_rest(actor, allowed=True)
            return {"outcome": "rested", "rest": rest, "message": rest["message"]}

        if attempts < self._REST_WARNINGS:
            self.long_rest(actor, allowed=False)
            if attempts == 0:
                msg = ("As you bed down, a City Watch patrol appears and moves you on -- no sleeping "
                       "rough within the walls. Rent a room at an inn if you want a proper rest.")
            else:
                msg = ("The Watch is back, and out of patience -- hands on cudgels. Try to bed down "
                       "here again and you'll be arrested for disturbing the peace. (Leave, talk "
                       "your way out, or fight them off.)")
            stage = "warned" if attempts == 0 else "guards"
            return {"outcome": stage, "rest": None, "message": msg}

        fine = min(self._REST_FINE, actor.sheet.get("gold", 0))
        actor.sheet["gold"] = actor.sheet.get("gold", 0) - fine
        rest = self.long_rest(actor, allowed=True)
        return {"outcome": "arrested", "rest": rest, "fine": fine,
                "message": ("The Watch hauls you off for disturbing the public order. You spend the "
                            f"night in a cell and are released at dawn{f', lighter by {fine} gp' if fine else ''}. "
                            "You're rested, but you've lost the night and made no friends.")}

    def narration_tone(self) -> str:
        return self.setting.tone if self.setting is not None else ""

    def narration_register(self, skill: str, actor: Combatant, approach: str = "") -> str:
        for ext in self.extensions:
            reg = ext.narration_register(skill, actor, approach)
            if reg:
                return reg
        return ""

    def register_for_text(self, text: str, actor: Combatant | None = None) -> str:
        for ext in self.extensions:
            reg = ext.register_for_text(text, actor)
            if reg:
                return reg
        return ""

    def narrator_briefing(self, pc: Combatant) -> str:
        s = pc.sheet
        lines: list[str] = []
        ident = " ".join(x for x in (s.get("race", ""), s.get("class", "")) if x)
        bg = s.get("background", "")
        who = f"You are {pc.name}"
        if ident:
            who += f", a {ident}"
        if bg:
            who += f" with the {bg} background"
        lines.append(who + ".")
        if s.get("alignment"):
            ak = s.get("alignment_key")
            al = self.alignments.get(ak) if ak else None
            tend = (al.tendency if al else "") or ""
            lead = f"Your moral leaning is {s['alignment']}"
            lines.append(f"{lead} -- {tend}" if tend else f"{lead}.")
        for ext in self.extensions:
            lines += ext.briefing_lines(pc)
        rp = s.get("roleplay") or {}
        chosen = rp.get("chosen") or {}
        feat = rp.get("feature") or {}
        if feat.get("name"):
            lines.append(f"Background feature, {feat['name']}: {feat.get('text', '')}")

        def _pick(field_key, suggestions_key):
            return chosen.get(field_key) or _first(rp.get(suggestions_key, []))
        trait = _pick("trait", "suggested_traits")
        ideal = _pick("ideal", "suggested_ideals")
        bond = _pick("bond", "suggested_bonds")
        flaw = _pick("flaw", "suggested_flaws")
        if trait:
            lines.append(f"Personality: {trait}")
        if ideal:
            lines.append(f"Ideal: {ideal}")
        if bond:
            lines.append(f"Bond: {bond}")
        if flaw:
            lines.append(f"Flaw: {flaw}")
        if len(lines) <= 1:
            char_brief = ""
        else:
            char_brief = ("Character briefing (let this color the character's voice, manner, and "
                          "choices; weave it in naturally and never contradict the player's stated "
                          "actions, and do not narrate mechanical outcomes from it):\n- "
                          + "\n- ".join(lines))
        world_brief = self.setting.narration_brief() if self.setting is not None else ""
        return "\n\n".join(b for b in (world_brief, char_brief) if b)

    @staticmethod
    def default_sheet() -> dict:
        return {
            "abilities": {"str": 12, "dex": 14, "con": 13,
                          "int": 10, "wis": 12, "cha": 11},
            "proficiencies": ["perception", "stealth", "persuasion", "athletics"],
            "proficiency_bonus": 2,
            "hp": 12, "max_hp": 12, "ac": 14,
            "attacks": [{"name": "shortsword", "bonus": 4, "damage": "1d6+2",
                         "reach": "melee"}],
            "intelligence": 3,
            "comprehends_language": True, "mindless": False,
        }

    def make_enemy(self, name: str, *, hp: int = 7, ac: int = 12,
                   attack=("claw", 4, "1d6+1"), reach: str = "melee",
                   intelligence: int = 2, morale: int = 100,
                   creature_type: str = "humanoid", alignment: str | None = None,
                   comprehends_language: bool = True, mindless: bool = False,
                   gender: str = "non_applicable") -> Combatant:
        an, ab, ad = attack
        sheet = {
            "abilities": {"str": 12, "dex": 12, "con": 12, "int": 7, "wis": 10, "cha": 8},
            "proficiencies": [], "proficiency_bonus": 2,
            "hp": hp, "max_hp": hp, "ac": ac,
            "attacks": [{"name": an, "bonus": ab, "damage": ad, "reach": reach}],
            "intelligence": intelligence,
            "morale": morale, "morale_threshold": 30, "resolve_dc": 12,
            "creature_type": creature_type,
            "comprehends_language": comprehends_language, "mindless": mindless,
        }
        if alignment and self._align is not None:
            al = self._align.get(alignment)
            if al is not None:
                sheet["alignment"] = al.label
                sheet["alignment_key"] = al.key
        if self._gender is not None:
            self._gender.init(sheet, gender)
        for ext in self.extensions:
            ext.init_creature(sheet, name=name, creature_type=creature_type, mindless=mindless)
        return Combatant(name=name, is_pc=False, sheet=sheet)

    def make_companion(self, name: str, *, hp: int = 11, ac: int = 14,
                       attack=("spear", 4, "1d6+2"), reach: str = "melee",
                       intelligence: int = 3, gender: str = "androgynous") -> Combatant:
        an, ab, ad = attack
        sheet = {
            "abilities": {"str": 13, "dex": 13, "con": 13, "int": 10, "wis": 11, "cha": 10},
            "proficiencies": ["athletics"], "proficiency_bonus": 2,
            "hp": hp, "max_hp": hp, "ac": ac,
            "attacks": [{"name": an, "bonus": ab, "damage": ad, "reach": reach}],
            "intelligence": intelligence,
            "comprehends_language": True, "mindless": False,
        }
        self._init_profile(sheet, {"gender": gender})
        return Combatant(name=name, is_pc=False, sheet=sheet)

    def optional_rules(self) -> list:
        return [dict(ext.rule, on=ext.enabled) for ext in self.extensions if ext.rule]

    def set_rule(self, key: str, on: bool) -> bool:
        for ext in self.extensions:
            if ext.rule and ext.rule.get("key") == key:
                return ext.set_enabled(on)
        return False

    def rule_enabled(self, key: str) -> bool:
        return key in self.enabled_rules()

    def enabled_rules(self) -> set:
        return {ext.rule["key"] for ext in self.extensions if ext.rule and ext.enabled}

    def extension(self, key: str):
        return next((ext for ext in self.extensions if ext.key == key), None)

    def set_gender(self, actor: Combatant, new_gender: str, *, presenter=None) -> dict:
        if self._gender is None:
            return {"ok": False, "message": "gender system unavailable"}
        self._ensure_profile(actor)
        res = self._gender.set_gender(actor, new_gender, presenter=presenter)
        if res.get("changed"):
            for ext in self.extensions:
                ext.on_gender_change(actor, res["before"], res["after"])
        return res

    def save_disadvantage(self, actor: Combatant, ability: str) -> bool:
        ability = ability.lower()
        if (self._gender is not None and ability in self._mental_abilities()
                and self._gender.dissonant(actor.sheet)):
            return True
        return any(ext.save_disadvantage(actor, ability) for ext in self.extensions)

    def effective_speed(self, actor: Combatant) -> int:
        base = actor.sheet.get("speed", 30)
        for ext in self.extensions:
            base += ext.speed_modifier(actor)
        if self._equipment is not None:
            base += self.encumbrance_status(actor)["speed_penalty"]
        return max(0, base)

    def equip_item(self, actor: Combatant, item_key: str, slot: str, *, in_combat: bool = False) -> dict:
        if self._equipment is None:
            return {"ok": False, "message": "Equipment rules unavailable."}
        return self._equipment.equip(self, actor, item_key, slot, in_combat=in_combat)

    def unequip_item(self, actor: Combatant, slot: str) -> dict:
        if self._equipment is None:
            return {"ok": False, "message": "Equipment rules unavailable."}
        return self._equipment.unequip(self, actor, slot)

    def can_equip(self, actor: Combatant, item_key: str, slot: str, *, in_combat: bool = False) -> dict:
        if self._equipment is None:
            return {"ok": False, "reason": "Equipment rules unavailable."}
        return self._equipment.can_equip(actor, self.item_info(item_key), slot,
                                         in_combat=in_combat, lookup=lambda k: self.item_info(k))

    def equipment_view(self, actor: Combatant) -> dict:
        if self._equipment is None:
            return {"slots": [], "encumbrance": {}, "ac": actor.sheet.get("ac", 10), "bonuses": {}}
        return self._equipment.equipment_view(self, actor)

    def encumbrance_status(self, actor: Combatant) -> dict:
        if self._equipment is None:
            return {"weight": 0, "capacity": 0, "status": "unencumbered", "speed_penalty": 0, "over": False}
        return self._equipment.encumbrance(actor.sheet, lambda k: self.item_info(k))

    def recompute_equipment(self, actor: Combatant) -> None:
        if self._equipment is not None:
            self._equipment.recompute(self, actor)
