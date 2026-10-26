from __future__ import annotations

import json
from dataclasses import dataclass

from .llm import DETERMINISTIC, LLMClient, PromptBuilder


@dataclass(frozen=True)
class Sin:
    rating: int
    description: str


@dataclass(frozen=True)
class Morality:
    name: str
    trait: str
    virtue: str
    sins: tuple


_MORAL_GRAMMAR = (
    'root ::= ws "{" ws "\\"severity\\"" ws ":" ws sev ws "}" ws\n'
    'sev  ::= "0" | "1" | "2" | "3" | "4" | "5"\n'
    'ws   ::= [ \\t\\n]*\n'
)


def build_moral_system(morality: Morality) -> str:
    lines = [
        f"You rate whether the action the player just took is a moral transgression "
        f"under a code called {morality.name}, and how severe. Reply with ONLY a "
        f'JSON object {{"severity": N}}, where N is 0-5:',
        "0 = not a transgression (ordinary, justified, defensive, or trivial).",
    ]
    for s in sorted(morality.sins, key=lambda x: x.rating):
        lines.append(f"{s.rating} = {s.description}.")
    lines.append("Judge the ACTION taken, not mere words, thoughts, or feelings, and "
                 "not violence that is clearly self-defense. When in doubt, answer 0.")
    return "\n".join(lines)


def _first_obj(s: str) -> str:
    i, j = s.find("{"), s.rfind("}")
    return s[i:j + 1] if i != -1 and j != -1 and j > i else "{}"


class MoralClassifier:
    def __init__(self, morality: Morality):
        self.morality = morality
        self.system = build_moral_system(morality)

    def severity(self, client: LLMClient, builder: PromptBuilder, action: str) -> int:
        prompt = builder.build(system=self.system, history=None, user=action)
        sampling = DETERMINISTIC.with_stops(builder.stops)
        raw = client.complete(prompt, sampling, grammar=_MORAL_GRAMMAR).text
        try:
            return max(0, min(5, int(json.loads(_first_obj(raw))["severity"])))
        except (ValueError, KeyError, TypeError):
            return 0
