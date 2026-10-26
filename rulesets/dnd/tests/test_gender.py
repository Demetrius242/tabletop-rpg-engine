import sys, pathlib

_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.dice import ScriptedDice
from engine.events import GenderShift
from rulesets.dnd.core.dnd import DnDRuleset


class _Rec:
    def __init__(self): self.events = []
    def emit(self, e): self.events.append(e)
    def of(self, t): return [e for e in self.events if isinstance(e, t)]


def _rs(*rolls, default=10):
    return DnDRuleset(dice=ScriptedDice(*rolls, default=default) if rolls else ScriptedDice(default=default))


def _pc(rs, **sel):
    base = {"name": "Test", "race": "human", "class": "bard", "background": "charlatan",
            "alignment": "cn", "abilities": {"str": 10, "dex": 14, "con": 12, "int": 10, "wis": 10, "cha": 16},
            "skills": ["persuasion", "deception"]}
    base.update(sel)
    return rs.build_pc(base)


def test_gender_set_at_creation():
    rs = _rs()
    pc = _pc(rs, gender="female")
    assert pc.sheet["gender_initial"] == "female" and pc.sheet["gender_current"] == "female"
    z = rs.make_enemy("Husk", creature_type="undead")
    assert z.sheet["gender_current"] == "non_applicable"


def test_gender_change_penalty():
    rs = _rs()
    pc = _pc(rs, gender="male")
    rec = _Rec()
    res = rs.set_gender(pc, "female", presenter=rec)
    assert res["changed"] and rec.of(GenderShift)
    assert rs.save_disadvantage(pc, "wis") is True
    assert rs.save_disadvantage(pc, "str") is False
    assert rs.situational_difficulty_delta(pc, "persuasion") == 1
    assert rs.situational_difficulty_delta(pc, "athletics") == 0


def test_gender_dissonance_clears_on_long_rests():
    rs = _rs()
    pc = _pc(rs, gender="male")
    rs.set_gender(pc, "androgynous")
    assert pc.sheet["gender_dissonance"] == 2
    rs.long_rest(pc); rs.long_rest(pc)
    assert pc.sheet["gender_dissonance"] == 0
    assert rs.save_disadvantage(pc, "wis") is False


def test_unknown_gender_is_rejected():
    rs = _rs()
    pc = _pc(rs, gender="female")
    res = rs.set_gender(pc, "nonsense")
    assert not res.get("changed")
    assert pc.sheet["gender_current"] == "female"


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
if __name__ == "__main__":
    ok = 0
    for t in ALL:
        try:
            t(); ok += 1
        except Exception as exc:
            print(f"FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{ok}/{len(ALL)} passed")
    sys.exit(0 if ok == len(ALL) else 1)
