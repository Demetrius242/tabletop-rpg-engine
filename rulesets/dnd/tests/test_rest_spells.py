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


def _cleric(rs, wis=16):
    return rs.build_pc({"name": "Davna", "race": "human", "class": "cleric", "background": "acolyte",
                        "alignment": "lg",
                        "abilities": {"wis": wis, "con": 14, "str": 13, "cha": 12, "dex": 10, "int": 8},
                        "skills": ["medicine", "persuasion"]})


def _bard(rs):
    return rs.build_pc({"name": "Lyra", "race": "half_elf", "class": "bard", "background": "charlatan",
                        "alignment": "cg",
                        "abilities": {"cha": 16, "dex": 14, "con": 13, "wis": 12, "int": 10, "str": 8},
                        "skills": []})


def test_prepare_spells_validates_and_caps():
    rs = DnDRuleset()
    pc = _cleric(rs, wis=16)
    sc = pc.sheet["spellcasting"]
    assert sc["spells_method"] == "prepared"
    prepared = rs.prepare_spells(pc, ["cure_wounds", "bless", "fireball", "bless", "spirit_guardians",
                                      "command", "aid", "guardian_of_faith"])
    assert "fireball" not in prepared
    assert prepared.count("bless") == 1
    assert len(prepared) == sc["spells_count"]
    assert all(p in [s for s in prepared] for p in prepared)


def test_prepared_only_for_prepared_casters():
    rs = DnDRuleset()
    assert rs.prepare_spells(_bard(rs), ["charm_person"]) is None


def test_set_known_spells_for_known_casters():
    rs = DnDRuleset()
    bard = _bard(rs)
    known = rs.set_known_spells(bard, ["healing_word", "charm_person", "vicious_mockery",
                                       "fireball", "disguise_self", "faerie_fire"])
    assert "vicious_mockery" not in known and "fireball" not in known
    assert len(known) <= bard.sheet["spellcasting"]["spells_count"]
    assert "healing_word" in known and "charm_person" in known


def test_set_cantrips_caps_at_class_count():
    rs = DnDRuleset()
    bard = _bard(rs)
    cantrips = rs.set_cantrips(bard, ["vicious_mockery", "mage_hand", "minor_illusion",
                                      "light", "fireball"])
    assert "fireball" not in cantrips
    assert len(cantrips) == bard.sheet["spellcasting"]["cantrips_known"]


def test_long_rest_heals_and_refreshes():
    rs = DnDRuleset()
    pc = _cleric(rs)
    pc.sheet["hp"] = 1
    out = rs.long_rest(pc)
    assert pc.sheet["hp"] == pc.sheet["max_hp"] and out["healed"] >= 1
    assert pc.sheet["spell_slots_remaining"] == pc.sheet["spell_slots"]
    assert out["slots_restored"] is True


def test_long_rest_can_reprepare():
    rs = DnDRuleset()
    pc = _cleric(rs)
    out = rs.long_rest(pc, prepared=["cure_wounds", "healing_word", "bless", "aid"])
    assert out["reprepared"] is True
    assert pc.sheet["spellcasting"]["prepared"]
    assert "cure_wounds" in pc.sheet["spellcasting"]["prepared"]


def test_rest_command_through_the_engine():
    rs = DnDRuleset()
    pc = _cleric(rs)
    pc.sheet["hp"] = 3
    client = FakeLLMClient()
    state = GameState(pc=pc, location="a quiet camp")
    eng = ExplorationEngine(client=client, presenter=None, state=state, ruleset=rs)
    class _P:
        def __init__(self): self.events = []
        def emit(self, e): self.events.append(e)
    eng.presenter = _P()
    eng._handle_ooc("rest")
    msgs = [e.text for e in eng.presenter.events if isinstance(e, SystemMessage)]
    assert any("long rest" in m for m in msgs)
    assert pc.sheet["hp"] == pc.sheet["max_hp"]


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
