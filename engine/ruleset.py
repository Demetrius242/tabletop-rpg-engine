from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .creation import Step
from .difficulty import DifficultyBand
from .outcome import Difficulty, Outcome, StaticDifficulty
from .state import Combatant
from .turnmodel import TurnModel


@dataclass
class SpecialAction:
    kind: str
    event: object = None
    cue: str = ""
    message: str = ""
    moral_text: str = ""


class Ruleset(ABC):
    name: str = "ruleset"

    @abstractmethod
    def resolve_check(
        self, actor: Combatant, skill: str,
        difficulty: Difficulty, ctx: dict | None = None,
    ) -> Outcome:
        ...

    @abstractmethod
    def modifier_for(self, actor: Combatant, skill: str) -> int: ...

    @abstractmethod
    def skill_names(self) -> list[str]: ...

    @abstractmethod
    def difficulty_for_band(self, band: DifficultyBand) -> Difficulty: ...

    @abstractmethod
    def health_descriptor(self, actor: Combatant) -> str: ...

    @abstractmethod
    def apply_damage(
        self, actor: Combatant, amount: int, dtype: str | None = None
    ) -> None: ...

    @abstractmethod
    def is_defeated(self, actor: Combatant) -> bool: ...

    @abstractmethod
    def health_fraction(self, actor: Combatant) -> float: ...

    @abstractmethod
    def turn_model(self) -> TurnModel: ...

    @abstractmethod
    def make_pc(self, name: str) -> Combatant: ...

    def creation_spec(self) -> list[Step]:
        return [Step("name", "What is your character's name?", "text")]

    def build_pc(self, selections: dict) -> Combatant:
        return self.make_pc(selections.get("name", "Adventurer"))

    def options_for(self, step_key: str, selections: dict) -> tuple:
        return ()

    def count_for(self, step_key: str, selections: dict) -> int:
        return 0

    def narrator_briefing(self, pc: Combatant) -> str:
        return ""

    def narration_tone(self) -> str:
        return ""

    def narration_register(self, skill: str, actor: Combatant, approach: str = "") -> str:
        return ""

    def register_for_text(self, text: str, actor: Combatant | None = None) -> str:
        return ""

    def optional_rules(self) -> list:
        return []

    def set_rule(self, key: str, on: bool) -> bool:
        return False

    def inventory_names(self, actor: Combatant) -> list:
        return []

    def long_rest(self, pc: Combatant) -> dict | None:
        return None

    def rest_context(self, location: str) -> dict:
        return {"in_settlement": False, "at_inn": False}

    def rest_attempt(self, pc: Combatant, *, in_settlement: bool = False,
                     at_inn: bool = False, attempts: int = 0) -> dict:
        rest = self.long_rest(pc)
        msg = (rest or {}).get("message") if isinstance(rest, dict) else None
        return {"outcome": "rested", "rest": rest, "message": msg or "You take a long rest."}

    def grant_item(self, pc: Combatant, item_key: str) -> bool:
        return False

    def skill_tags(self, skill: str) -> set[str]:
        return set()

    def situational_difficulty_delta(self, actor: Combatant, skill: str) -> int:
        return 0

    def can_receive_communication(self, target: Combatant, mode: str = "verbal") -> bool:
        if self.is_defeated(target):
            return False
        sheet = target.sheet
        if mode == "mental":
            return not sheet.get("mindless", False)
        if sheet.get("mindless", False) or not sheet.get("comprehends_language", True):
            return False
        if "deafened" in target.statuses:
            return False
        return True

    def social_difficulty(self, target: Combatant, mode: str = "intimidate") -> Difficulty:
        return StaticDifficulty(target.sheet.get("resolve_dc", 12))

    def actions_this_turn(self, actor: Combatant) -> int:
        return 1

    def pre_turn_choices(self, actor: Combatant) -> list:
        return []

    def apply_pre_turn(self, actor: Combatant, key: str) -> str:
        return ""

    def ai_pre_turn(self, actor: Combatant) -> None:
        return None

    def check_frenzy(self, actor: Combatant) -> bool:
        return False

    def is_out_of_control(self, actor: Combatant) -> bool:
        return False

    def combat_heal(self, actor: Combatant) -> tuple:
        return (False, 0)

    def end_turn(self, actor: Combatant) -> None:
        return None

    def available_combat_powers(self, actor: Combatant) -> list:
        return []

    def use_discipline(self, actor: Combatant, discipline: str, power_key: str,
                       target: Combatant | None = None, **kw):
        return None

    def forced_action(self, actor: Combatant) -> str | None:
        return None

    def ai_combat_power(self, actor: Combatant) -> str | None:
        return None

    def try_special_action(self, actor: Combatant, text: str) -> "SpecialAction | None":
        return None

    def exploration_powers(self, actor: Combatant) -> list:
        return []

    def known_rituals(self, actor: Combatant) -> list:
        return []

    def morality(self):
        return None

    def build_adventure(self, key: str):
        return None

    def list_adventures(self) -> list:
        return []
