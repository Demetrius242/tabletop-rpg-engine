from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .outcome import Band
from .state import Combatant


@dataclass
class Budget:
    actions: int = 1
    bonus: int = 1
    reactions: int = 1
    movement: int = 1

    def can(self, kind: str) -> bool:
        return getattr(self, kind, 0) > 0

    def spend(self, kind: str) -> None:
        setattr(self, kind, getattr(self, kind) - 1)


@dataclass(frozen=True)
class Attack:
    target: Combatant


@dataclass(frozen=True)
class Defend:
    pass


@dataclass(frozen=True)
class Pass:
    pass


@dataclass(frozen=True)
class AttackResult:
    attacker: str
    defender: str
    hit: bool
    band: Band
    damage: int
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AttackEstimate:
    hit_chance: float
    expected_damage: float
    could_drop: bool


@runtime_checkable
class TurnContext(Protocol):
    def is_active(self, c: Combatant) -> bool: ...
    def combat_over(self) -> bool: ...
    def begin_turn(self, c: Combatant) -> None: ...
    def take_turn(self, c: Combatant) -> None: ...
    def begin_round(self) -> None: ...
    def declare(self, c: Combatant) -> None: ...
    def announce_turn(self, c: Combatant) -> None: ...
    def resolve(self, c: Combatant) -> None: ...


class TurnModel(ABC):
    @abstractmethod
    def initiative_order(self, combatants: list[Combatant]) -> list[tuple[Combatant, int]]:
        pass

    @abstractmethod
    def new_turn_budget(self, combatant: Combatant) -> Budget: ...

    @abstractmethod
    def resolve_attack(self, attacker: Combatant, defender: Combatant, *,
                       defending: bool = False, situational_ac: int = 0,
                       situational_hit: int = 0) -> AttackResult: ...

    @abstractmethod
    def estimate_attack(self, attacker: Combatant, defender: Combatant, *,
                        situational_ac: int = 0, situational_hit: int = 0) -> AttackEstimate: ...

    @abstractmethod
    def run_round(self, order: list[Combatant], ctx: TurnContext) -> None:
        pass
