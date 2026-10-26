from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.classify import Classifier, IntentType
from engine.engine import ExplorationEngine
from engine.events import Event, Narration, SessionEnd, SystemMessage
from engine.llm import FakeLLMClient
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


def _engine(inputs, fake, ruleset=None, **kw):
    ruleset = ruleset or DnDRuleset()
    state = GameState(pc=ruleset.make_pc("Test"), location="a test room")
    pres = ScriptedPresenter(inputs)
    eng = ExplorationEngine(
        client=fake, presenter=pres, state=state, ruleset=ruleset, **kw)
    return eng, pres


def test_dialogue_produces_narration():
    fake = FakeLLMClient().queue(
        "The antechamber is silent.",
        '{"intent": "dialogue", "detail": "greets the dark"}',
        "Your voice echoes and dies. Nothing answers.",
    )
    eng, pres = _engine(['"Hello?" I call out.'], fake)
    eng.run()
    narrations = pres.of_type(Narration)
    assert len(narrations) == 2, narrations
    assert "echoes" in narrations[-1].text


def test_quit_ends_session():
    fake = FakeLLMClient().queue(
        "An opening scene.",
        '{"intent": "ooc_command", "detail": "quit"}',
    )
    eng, pres = _engine(["quit"], fake)
    eng.run()
    assert pres.of_type(SessionEnd), "expected a SessionEnd event"
    assert eng.running is False


def test_status_command_reports_condition():
    fake = FakeLLMClient().queue(
        "An opening scene.",
        '{"intent": "ooc_command", "detail": "status"}',
    )
    eng, pres = _engine(["status"], fake)
    eng.run()
    msgs = pres.of_type(SystemMessage)
    assert any("unhurt" in m.text for m in msgs), msgs


def test_classifier_uses_grammar_and_zero_temp():
    fake = FakeLLMClient().queue(
        "Opening.", '{"intent": "dialogue", "detail": ""}', "Reply."
    )
    eng, pres = _engine(["say hi"], fake)
    eng.run()
    classify_calls = [c for c in fake.calls if c.grammar is not None]
    assert classify_calls, "classifier never ran with a grammar"
    assert classify_calls[0].sampling.temperature == 0.0


def test_classifier_parse_fallback():
    assert Classifier._parse("not json at all").type is IntentType.DIALOGUE
    parsed = Classifier._parse('{"intent": "trivial_action", "detail": "open"}')
    assert parsed.type is IntentType.TRIVIAL_ACTION
    assert parsed.detail == "open"


def test_save_creates_file():
    fake = FakeLLMClient().queue(
        "Opening.", '{"intent": "ooc_command", "detail": "save"}'
    )
    save_file = os.path.join(tempfile.mkdtemp(), "save.json")
    eng, pres = _engine(["save"], fake, save_path=save_file)
    eng.run()
    assert os.path.exists(save_file)


def test_narrator_override_replaces_base_prompt():
    from engine.engine import NARRATOR_SYSTEM
    fake = FakeLLMClient()
    custom = "You are a terse, hardboiled noir narrator. One sentence only."
    eng, _ = _engine([], fake, narrator_override=custom)
    sys_prompt = eng._narrator_system("exploration")
    assert custom in sys_prompt
    assert NARRATOR_SYSTEM not in sys_prompt
    eng2, _ = _engine([], FakeLLMClient())
    assert NARRATOR_SYSTEM in eng2._narrator_system("exploration")


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
