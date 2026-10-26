from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DifficultyBand(str, Enum):
    TRIVIAL = "trivial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    NEARLY_IMPOSSIBLE = "nearly_impossible"


_ORDER = [
    DifficultyBand.TRIVIAL, DifficultyBand.EASY, DifficultyBand.MEDIUM,
    DifficultyBand.HARD, DifficultyBand.VERY_HARD, DifficultyBand.NEARLY_IMPOSSIBLE,
]


def shift(band: DifficultyBand, steps: int) -> DifficultyBand:
    i = max(0, min(len(_ORDER) - 1, _ORDER.index(band) + steps))
    return _ORDER[i]


@dataclass(frozen=True)
class CheckContext:
    approach: str = ""
    actor_statuses: frozenset = frozenset()
    skill_tags: frozenset = frozenset()
    impairment_delta: int = 0
    lighting: str | None = None
    footing: str | None = None
    target_alertness: str | None = None
    has_proper_tools: bool | None = None
    time_pressure: bool = False
    base_override: DifficultyBand | None = None


DEFAULT_STATUS_DELTAS = {
    "poisoned": (1, "all"),
    "frightened": (1, "all"),
    "exhausted": (1, "all"),
    "restrained": (1, "physical"),
    "prone": (1, "physical"),
    "blinded": (2, "sight"),
    "invisible": (-1, "physical"),
}

DEFAULT_MITIGATORS = (
    "careful", "cautio", "quiet", "slow", "sneak", "methodical",
    "patient", "take my time", "taking my time", "using cover",
)
DEFAULT_AGGRAVATORS = (
    "quick", "hast", "rush", "reckless", "blind", "barehand",
    "plain sight", "frantic", "panic",
)


class DifficultyAssessor:

    def __init__(self, status_deltas=None, mitigators=None, aggravators=None):
        self.status_deltas = dict(status_deltas or DEFAULT_STATUS_DELTAS)
        self.mitigators = tuple(mitigators or DEFAULT_MITIGATORS)
        self.aggravators = tuple(aggravators or DEFAULT_AGGRAVATORS)

    def assess(self, skill: str, ctx: CheckContext) -> tuple[DifficultyBand, list[str]]:
        steps = 0
        reasons: list[str] = []
        tags = ctx.skill_tags
        base = ctx.base_override or DifficultyBand.MEDIUM

        if ctx.lighting == "dim" and "sight" in tags:
            steps += 1; reasons.append("dim light")
        elif ctx.lighting == "dark" and "sight" in tags:
            steps += 2; reasons.append("darkness")
        if ctx.footing in ("unstable", "slippery") and "physical" in tags:
            steps += 1; reasons.append("poor footing")
        if ctx.time_pressure:
            steps += 1; reasons.append("time pressure")
        if ctx.has_proper_tools is True:
            steps -= 1; reasons.append("right tools")
        elif ctx.has_proper_tools is False and "tool" in tags:
            steps += 1; reasons.append("no proper tools")

        if "opposed" in tags and ctx.target_alertness:
            if ctx.target_alertness == "alert":
                steps += 1; reasons.append("target alert")
            elif ctx.target_alertness == "unaware":
                steps -= 1; reasons.append("target unaware")

        for st in sorted(ctx.actor_statuses):
            delta, scope = self.status_deltas.get(st, (0, "all"))
            if delta and (scope == "all" or scope in tags):
                steps += delta; reasons.append(st)

        if ctx.impairment_delta:
            steps += ctx.impairment_delta; reasons.append("impaired")

        lex = self._lexical_delta(ctx.approach)
        if lex:
            steps += lex
            reasons.append("cautious approach" if lex < 0 else "rash approach")

        return shift(base, steps), reasons

    def _lexical_delta(self, approach: str) -> int:
        t = (approach or "").lower()
        mit = any(w in t for w in self.mitigators)
        agg = any(w in t for w in self.aggravators)
        if mit and not agg:
            return -1
        if agg and not mit:
            return 1
        return 0
