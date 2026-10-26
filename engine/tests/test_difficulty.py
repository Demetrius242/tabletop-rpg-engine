from __future__ import annotations

import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.difficulty import CheckContext, DifficultyAssessor, DifficultyBand

A = DifficultyAssessor()
B = DifficultyBand


def ctx(**kw):
    return CheckContext(**kw)


def test_base_is_medium():
    band, _ = A.assess("stealth", ctx(skill_tags=frozenset({"physical", "opposed"})))
    assert band is B.MEDIUM


def test_tools_make_it_easier():
    band, _ = A.assess("sleight_of_hand",
                       ctx(skill_tags=frozenset({"physical", "tool"}), has_proper_tools=True))
    assert band is B.EASY


def test_missing_tools_only_hurt_tool_skills():
    no_tools = ctx(skill_tags=frozenset({"physical", "tool"}), has_proper_tools=False)
    assert A.assess("sleight_of_hand", no_tools)[0] is B.HARD
    assert A.assess("athletics", ctx(skill_tags=frozenset({"physical"}),
                                     has_proper_tools=False))[0] is B.MEDIUM


def test_darkness_hits_sight_only():
    assert A.assess("perception", ctx(skill_tags=frozenset({"sight"}),
                                      lighting="dark"))[0] is B.VERY_HARD
    assert A.assess("athletics", ctx(skill_tags=frozenset({"physical"}),
                                     lighting="dark"))[0] is B.MEDIUM


def test_status_penalty_is_scoped():
    blinded = frozenset({"blinded"})
    assert A.assess("perception", ctx(skill_tags=frozenset({"sight"}),
                                      actor_statuses=blinded))[0] is B.VERY_HARD
    assert A.assess("athletics", ctx(skill_tags=frozenset({"physical"}),
                                     actor_statuses=blinded))[0] is B.MEDIUM


def test_poisoned_hits_everything():
    assert A.assess("athletics", ctx(skill_tags=frozenset({"physical"}),
                                     actor_statuses=frozenset({"poisoned"})))[0] is B.HARD


def test_alert_target_hardens_opposed_skills():
    tags = frozenset({"physical", "opposed"})
    assert A.assess("stealth", ctx(skill_tags=tags, target_alertness="alert"))[0] is B.HARD
    assert A.assess("stealth", ctx(skill_tags=tags, target_alertness="unaware"))[0] is B.EASY


def test_lexical_nudges_are_bounded():
    cautious = ctx(skill_tags=frozenset({"physical", "opposed"}),
                   approach="I move very carefully and quietly")
    assert A.assess("stealth", cautious)[0] is B.EASY
    rash = ctx(skill_tags=frozenset({"physical"}), approach="I rush across blindly")
    assert A.assess("athletics", rash)[0] is B.HARD


def test_ruleset_impairment_delta_applies():
    band, reasons = A.assess("athletics",
                             ctx(skill_tags=frozenset({"physical"}), impairment_delta=2))
    assert band is B.VERY_HARD and "impaired" in reasons


def test_clamps_at_both_extremes():
    overload = ctx(
        skill_tags=frozenset({"sight"}), lighting="dark",
        actor_statuses=frozenset({"blinded", "poisoned", "frightened"}),
        time_pressure=True)
    assert A.assess("perception", overload)[0] is B.NEARLY_IMPOSSIBLE
    floor = ctx(skill_tags=frozenset({"physical", "tool"}), has_proper_tools=True,
                base_override=B.TRIVIAL, approach="slowly and carefully")
    assert A.assess("sleight_of_hand", floor)[0] is B.TRIVIAL


def test_reasons_are_reported():
    _, reasons = A.assess("perception", ctx(skill_tags=frozenset({"sight"}),
                                            lighting="dark"))
    assert any("dark" in r for r in reasons)


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
