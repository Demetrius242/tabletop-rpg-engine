from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Band(str, Enum):
    BOTCH = "botch"
    FAILURE = "failure"
    MARGINAL = "marginal"
    SUCCESS = "success"
    EXCEPTIONAL = "exceptional"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Outcome:
    success: bool
    band: Band
    magnitude: int
    is_botch: bool = False
    is_crit: bool = False
    raw: dict = field(default_factory=dict)


class Difficulty:
    pass


@dataclass(frozen=True)
class StaticDifficulty(Difficulty):
    dc: int
    label: str = ""


@dataclass(frozen=True)
class OpposedDifficulty(Difficulty):
    target: object
    skill: str


@dataclass(frozen=True)
class PoolDifficulty(Difficulty):
    target: int
    required: int = 1
    label: str = ""
