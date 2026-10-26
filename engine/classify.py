from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from .llm import DETERMINISTIC, LLMClient, PromptBuilder, Sampling


class IntentType(str, Enum):
    DIALOGUE = "dialogue"
    TRIVIAL_ACTION = "trivial_action"
    OOC_COMMAND = "ooc_command"
    CHECK_ACTION = "check_action"
    COMBAT_START = "combat_start"


@dataclass(frozen=True)
class Intent:
    type: IntentType
    detail: str = ""
    skill: str = ""
    approach: str = ""


_GRAMMAR_TEMPLATE = r'''
root          ::= ws ( check_obj | simple_obj ) ws
simple_obj    ::= "{" ws "\"intent\"" ws ":" ws simple_intent ws "," ws "\"detail\"" ws ":" ws string ws "}"
simple_intent ::= "\"dialogue\"" | "\"trivial_action\"" | "\"ooc_command\"" | "\"combat_start\""
check_obj     ::= "{" ws "\"intent\"" ws ":" ws "\"check_action\"" ws "," ws "\"skill\"" ws ":" ws skill ws "," ws "\"approach\"" ws ":" ws string ws "}"
skill         ::= __SKILLS__
string        ::= "\"" char* "\""
char          ::= [^"\\] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F])
ws            ::= [ \t\n]*
'''


def _alt(values) -> str:
    return " | ".join('"\\"' + v + '\\""' for v in values)


def build_intent_grammar(skills) -> str:
    return _GRAMMAR_TEMPLATE.replace("__SKILLS__", _alt(skills))


_BASE_SYSTEM = (
    "You are the input router for a text RPG. Read the player's input and classify "
    "it into EXACTLY one intent. Reply with ONLY a JSON object, no prose.\n"
    "Intents:\n"
    '- dialogue: the player speaks, asks, or addresses a character. '
    'Fields: {"intent","detail"}.\n'
    "- trivial_action: a simple physical action that needs no dice "
    "(pick something up, open an unlocked door, look around). "
    'Fields: {"intent","detail"}.\n'
    "- ooc_command: a meta/game command, not an in-world action "
    "(help, save, quit, status, look, rest). "
    'Fields: {"intent","detail"}.\n'
    "- check_action: an action whose success is uncertain and needs a dice roll "
    "(climb a sheer wall, pick a lock, sneak past a guard, persuade someone). "
    'Fields: {"intent","skill","approach"}. Name the skill being used and a short '
    "approach describing HOW they do it. Do NOT judge how hard it is.\n"
    "- combat_start: the player attacks or moves to fight a creature, starting a "
    'fight. Fields: {"intent","detail"}.'
)


def build_classify_system(skills) -> str:
    return _BASE_SYSTEM + "\nAvailable skills: " + ", ".join(skills) + "."


class Classifier:
    def __init__(self, skills, sampling: Sampling = DETERMINISTIC):
        self.skills = list(skills)
        self.sampling = sampling
        self.grammar = build_intent_grammar(self.skills)
        self.system = build_classify_system(self.skills)

    @classmethod
    def for_ruleset(cls, ruleset) -> "Classifier":
        return cls(ruleset.skill_names())

    def classify(self, client: LLMClient, builder: PromptBuilder, user_input: str) -> Intent:
        prompt = builder.build(system=self.system, history=None, user=user_input)
        sampling = self.sampling.with_stops(builder.stops)
        raw = client.complete(prompt, sampling, grammar=self.grammar).text
        return self._parse(raw)

    @staticmethod
    def _parse(raw: str) -> Intent:
        try:
            obj = json.loads(_first_json_object(raw))
            itype = IntentType(obj["intent"])
        except (ValueError, KeyError):
            return Intent(IntentType.DIALOGUE, detail=raw.strip()[:120])
        if itype is IntentType.CHECK_ACTION:
            return Intent(
                itype,
                skill=str(obj.get("skill", "")),
                approach=str(obj.get("approach", "")),
            )
        return Intent(itype, detail=str(obj.get("detail", "")))


def _first_json_object(s: str) -> str:
    start = s.find("{")
    if start == -1:
        raise ValueError("no JSON object found")
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
    raise ValueError("unbalanced JSON object")
