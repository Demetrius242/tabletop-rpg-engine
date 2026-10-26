from __future__ import annotations

import random
import re
from typing import Protocol, runtime_checkable


@runtime_checkable
class Dice(Protocol):
    def roll(self, sides: int) -> int: ...


class RandomDice:
    def __init__(self, seed: int | None = None):
        self._r = random.Random(seed)

    def roll(self, sides: int) -> int:
        return self._r.randint(1, sides)


class ScriptedDice:

    def __init__(self, *results: int, default: int = 10):
        self._q = list(results)
        self.default = default
        self.rolls: list[tuple[int, int]] = []

    def queue(self, *results: int) -> "ScriptedDice":
        self._q.extend(results)
        return self

    def roll(self, sides: int) -> int:
        value = self._q.pop(0) if self._q else self.default
        value = max(1, min(sides, value))
        self.rolls.append((sides, value))
        return value


_NOTATION = re.compile(r"^\s*(\d+)\s*d\s*(\d+)\s*([+-]\s*\d+)?\s*$", re.I)


def _parse_notation(expr: str) -> tuple[int, int, int]:
    m = _NOTATION.match(expr)
    if not m:
        raise ValueError(f"bad dice notation: {expr!r}")
    n, sides = int(m.group(1)), int(m.group(2))
    mod = int(m.group(3).replace(" ", "")) if m.group(3) else 0
    return n, sides, mod


def roll_notation(dice: Dice, expr: str) -> int:
    n, sides, mod = _parse_notation(expr)
    return sum(dice.roll(sides) for _ in range(n)) + mod


def average_notation(expr: str) -> float:
    n, sides, mod = _parse_notation(expr)
    return n * (sides + 1) / 2 + mod


def dice_only(expr: str) -> str:
    n, sides, _ = _parse_notation(expr)
    return f"{n}d{sides}"
