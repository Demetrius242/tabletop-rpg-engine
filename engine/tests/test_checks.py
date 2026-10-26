from __future__ import annotations

import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.dice import ScriptedDice
from engine.engine import ExplorationEngine
from engine.events import CheckResolved, Event, Narration
from engine.llm import FakeLLMClient
from engine.outcome import Band, StaticDifficulty
from rulesets.dnd.core.dnd import DnDRuleset
from engine.state import GameState


class ScriptedPresenter:
    def __init__(self, inputs):
        self._inputs = list(inputs)
        self.events: list[Event] = []

    def emit(self, event):
        self.events.append(event)

    def read_action(self):
        if not self._inputs:
            raise EOFError
        return self._inputs.pop(0)

    def of_type(self, t):
        return [e for e in self.events if isinstance(e, t)]


def _pc(rs):
    return rs.make_pc("Test")


def test_success_on_meeting_dc():
    rs = DnDRuleset(dice=ScriptedDice(11))
    o = rs.resolve_check(_pc(rs), "stealth", StaticDifficulty(15))
    assert o.success and o.band is Band.SUCCESS, o


def test_failure_below_dc():
    rs = DnDRuleset(dice=ScriptedDice(6))
    o = rs.resolve_check(_pc(rs), "stealth", StaticDifficulty(15))
    assert not o.success and o.band is Band.FAILURE, o


def test_natural_one_is_botch():
    rs = DnDRuleset(dice=ScriptedDice(1))
    o = rs.resolve_check(_pc(rs), "stealth", StaticDifficulty(5))
    assert o.is_botch and not o.success and o.band is Band.BOTCH, o


def test_natural_twenty_is_critical():
    rs = DnDRuleset(dice=ScriptedDice(20))
    o = rs.resolve_check(_pc(rs), "stealth", StaticDifficulty(30))
    assert o.is_crit and o.success and o.band is Band.CRITICAL, o


def test_big_margin_is_exceptional():
    rs = DnDRuleset(dice=ScriptedDice(16))
    o = rs.resolve_check(_pc(rs), "stealth", StaticDifficulty(10))
    assert o.band is Band.EXCEPTIONAL, o


def test_dnd_never_emits_marginal():
    rs = DnDRuleset(dice=ScriptedDice(11))
    o = rs.resolve_check(_pc(rs), "stealth", StaticDifficulty(15))
    assert o.band is not Band.MARGINAL


def test_proficiency_changes_modifier():
    rs = DnDRuleset()
    pc = _pc(rs)
    assert rs.modifier_for(pc, "stealth") == 4
    assert rs.modifier_for(pc, "arcana") == 0
    assert rs.modifier_for(pc, "dex") == 2


def _engine(inputs, fake, rs):
    state = GameState(pc=_pc(rs), location="a moonlit corridor")
    pres = ScriptedPresenter(inputs)
    eng = ExplorationEngine(client=fake, presenter=pres, state=state, ruleset=rs)
    return eng, pres


def test_engine_check_emits_band_and_narration():
    rs = DnDRuleset(dice=ScriptedDice(11))
    fake = FakeLLMClient().queue(
        "The corridor stretches before you.",
        '{"intent": "check_action", "skill": "stealth", '
        '"approach": "hugging the shadows"}',
        "You melt into the dark and slip past unseen.",
    )
    eng, pres = _engine(["I sneak past the guard"], fake, rs)
    eng.run()
    checks = pres.of_type(CheckResolved)
    assert len(checks) == 1, checks
    assert checks[0].success and checks[0].band == "success", checks[0]
    assert pres.of_type(Narration), "expected narration after the check"


def test_model_never_receives_the_numbers():
    rs = DnDRuleset(dice=ScriptedDice(11))
    fake = FakeLLMClient().queue(
        "Opening.",
        '{"intent": "check_action", "skill": "stealth", '
        '"approach": "creeping"}',
        "Narration.",
    )
    eng, pres = _engine(["sneak"], fake, rs)
    eng.run()
    narrate_prompts = [c.prompt for c in fake.calls if c.grammar is None]
    after_check = narrate_prompts[-1]
    for leak in ("15", "11", "DC", " dc"):
        assert leak not in after_check, f"number/DC leaked into narration: {leak!r}"


def test_engine_assesses_difficulty_in_python():
    rs = DnDRuleset(dice=ScriptedDice(10))
    fake = FakeLLMClient().queue(
        "A pitch-black cellar.",
        '{"intent": "check_action", "skill": "perception", '
        '"approach": "straining to see"}',
        "You make out little in the dark.",
    )
    state = GameState(pc=_pc(rs), location="a pitch-black cellar")
    state.flags["scene"] = {"lighting": "dark"}
    pres = ScriptedPresenter(["I look around"])
    eng = ExplorationEngine(client=fake, presenter=pres, state=state, ruleset=rs)
    eng.run()
    chk = pres.of_type(CheckResolved)[0]
    assert chk.difficulty == "very_hard", chk
    assert "darkness" in chk.raw.get("difficulty_reasons", [])


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for t in ALL:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(ALL) - failed}/{len(ALL)} passed")
    raise SystemExit(1 if failed else 0)
