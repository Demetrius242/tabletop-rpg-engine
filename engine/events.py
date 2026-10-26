from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


class Event:
    pass


@dataclass
class Narration(Event):
    text: str


@dataclass
class SystemMessage(Event):
    text: str


@dataclass
class Menu(Event):
    prompt: str
    options: list[str] = field(default_factory=list)


@dataclass
class StateDelta(Event):
    summary: str
    changes: dict = field(default_factory=dict)


@dataclass
class SessionEnd(Event):
    reason: str = "Session ended."


@dataclass
class CheckResolved(Event):
    skill: str
    band: str
    success: bool
    difficulty: str = ""
    raw: dict = field(default_factory=dict)


@dataclass
class CombatStarted(Event):
    order: list[str]
    sides: dict = field(default_factory=dict)


@dataclass
class TurnStarted(Event):
    name: str
    side: str


@dataclass
class AttackResolved(Event):
    attacker: str
    defender: str
    hit: bool
    crit: bool
    band: str
    damage: int
    defender_condition: str
    defeated: bool
    raw: dict = field(default_factory=dict)


@dataclass
class Defended(Event):
    name: str


@dataclass
class Moved(Event):
    name: str
    from_zone: str
    to_zone: str
    provoked: bool = False


@dataclass
class Fled(Event):
    name: str


@dataclass
class OrderIssued(Event):
    by: str
    to: str
    directive: str
    target: str = ""
    delivered: bool = True


@dataclass
class SocialResolved(Event):
    by: str
    target: str
    mode: str
    band: str = ""
    delivered: bool = True
    effect: str = ""


@dataclass
class MoraleBroke(Event):
    name: str
    outcome: str


@dataclass
class CombatEnded(Event):
    victor: str
    survivors: list[str] = field(default_factory=list)


@dataclass
class CharacterCreated(Event):
    name: str
    summary: str = ""


@dataclass
class BloodSpent(Event):
    name: str
    amount: int
    purpose: str = ""
    remaining: int = 0


@dataclass
class CelerityActivated(Event):
    name: str
    extra_actions: int = 0


@dataclass
class Frenzied(Event):
    name: str


@dataclass
class Healed(Event):
    name: str
    levels: int = 0
    amount: int = 0
    source: str = ""


@dataclass
class ItemGained(Event):
    owner: str
    key: str
    name: str
    rarity: str = "common"
    removed: bool = False


@dataclass
class GenderShift(Event):
    name: str
    before: str
    after: str
    dissonance_rests: int = 0


@dataclass
class HumanityShift(Event):
    name: str
    before: int
    after: int
    lost: bool = False
    derangement: bool = False
    trait: str = "Humanity"


@dataclass
class PowerUsed(Event):
    name: str
    power: str
    discipline: str = ""
    target: str = ""
    success: bool = True
    ok: bool = True
    reason: str = ""


@dataclass
class RiteCast(Event):
    name: str
    rite: str
    tradition: str = ""
    target: str = ""
    success: bool = True
    ok: bool = True
    reason: str = ""
    missing: tuple = ()


@dataclass
class StoryBeat(Event):
    text: str
    event_key: str = ""


@dataclass
class TaskUpdated(Event):
    task: str
    state: str
    summary: str = ""
    actor: str = "party"


@dataclass
class EventTransition(Event):
    from_event: str
    to_event: str
    title: str = ""


@runtime_checkable
class Presenter(Protocol):

    def emit(self, event: Event) -> None: ...

    def read_action(self) -> str: ...
