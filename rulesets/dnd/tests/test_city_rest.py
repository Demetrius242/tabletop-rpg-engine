import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.engine import ExplorationEngine
from engine.events import SystemMessage
from engine.llm import FakeLLMClient
from engine.state import GameState
from rulesets.dnd.core.dnd import DnDRuleset


def _pc(rs):
    return rs.build_pc({"name": "Aldwin", "race": "human", "class": "fighter", "background": "soldier",
                        "alignment": "ng",
                        "abilities": {"str": 15, "con": 14, "dex": 13, "int": 12, "wis": 10, "cha": 8},
                        "skills": ["athletics", "perception"]})


class _P:
    def __init__(self): self.events = []
    def emit(self, e): self.events.append(e)


def test_rest_context_classifies_locations():
    rs = DnDRuleset()
    assert rs.rest_context("a quiet forest camp") == {"in_settlement": False, "at_inn": False}
    assert rs.rest_context("the High Forest") == {"in_settlement": False, "at_inn": False}
    assert rs.rest_context("Waterdeep, Dock Ward")["in_settlement"] is True
    assert rs.rest_context("Waterdeep, Dock Ward")["at_inn"] is False
    inn = rs.rest_context("the common room of the Wandering Wyvern inn")
    assert inn["in_settlement"] and inn["at_inn"]


def test_wilderness_rests_normally():
    rs = DnDRuleset()
    pc = _pc(rs); pc.sheet["hp"] = 3
    out = rs.rest_attempt(pc, in_settlement=False, at_inn=False, attempts=0)
    assert out["outcome"] == "rested" and pc.sheet["hp"] == pc.sheet["max_hp"]


def test_inn_room_rests_normally_even_in_a_city():
    rs = DnDRuleset()
    pc = _pc(rs); pc.sheet["hp"] = 3
    out = rs.rest_attempt(pc, in_settlement=True, at_inn=True, attempts=5)
    assert out["outcome"] == "rested" and pc.sheet["hp"] == pc.sheet["max_hp"]


def test_open_city_rest_escalates_warned_then_guards_then_arrested():
    rs = DnDRuleset()
    pc = _pc(rs); pc.sheet["hp"] = 3
    first = rs.rest_attempt(pc, in_settlement=True, at_inn=False, attempts=0)
    assert first["outcome"] == "warned" and pc.sheet["hp"] == 3
    second = rs.rest_attempt(pc, in_settlement=True, at_inn=False, attempts=1)
    assert second["outcome"] == "guards" and pc.sheet["hp"] == 3
    third = rs.rest_attempt(pc, in_settlement=True, at_inn=False, attempts=2)
    assert third["outcome"] == "arrested"
    assert pc.sheet["hp"] == pc.sheet["max_hp"]


def test_arrest_levies_a_fine():
    rs = DnDRuleset()
    pc = _pc(rs)
    gold0 = pc.sheet["gold"]
    out = rs.rest_attempt(pc, in_settlement=True, at_inn=False, attempts=3)
    assert out["outcome"] == "arrested" and out["fine"] >= 0
    assert pc.sheet["gold"] == gold0 - out["fine"]


def test_engine_tracks_attempts_and_imprisons():
    rs = DnDRuleset()
    pc = _pc(rs)
    state = GameState(pc=pc, location="a busy Waterdeep street")
    eng = ExplorationEngine(client=FakeLLMClient(), presenter=_P(), state=state, ruleset=rs)
    eng._handle_ooc("i want to rest")
    assert state.flags["rest_attempts"] == 1
    eng._handle_ooc("rest")
    assert state.flags["rest_attempts"] == 2
    eng._handle_ooc("rest")
    assert state.flags.get("imprisoned") is True and state.flags["rest_attempts"] == 0
    msgs = [e.text for e in eng.presenter.events if isinstance(e, SystemMessage)]
    assert any("Watch" in m for m in msgs) and any("cell" in m for m in msgs)


def test_engine_rest_in_wilderness_just_rests():
    rs = DnDRuleset()
    pc = _pc(rs); pc.sheet["hp"] = 2
    state = GameState(pc=pc, location="a quiet camp in the woods")
    eng = ExplorationEngine(client=FakeLLMClient(), presenter=_P(), state=state, ruleset=rs)
    eng._handle_ooc("rest")
    assert pc.sheet["hp"] == pc.sheet["max_hp"]
    assert state.flags.get("rest_attempts", 0) == 0
    msgs = [e.text for e in eng.presenter.events if isinstance(e, SystemMessage)]
    assert any("long rest" in m for m in msgs)


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
