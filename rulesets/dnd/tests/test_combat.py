from __future__ import annotations

import random
import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.combat import CombatController, Fighter
from engine.dice import ScriptedDice
from engine.events import AttackResolved, CombatEnded, Event
from engine.llm import FakeLLMClient
from engine.outcome import Band
from rulesets.dnd.core.dnd import DnDRuleset
from engine.state import GameState
from engine.turnmodel import Attack, Pass


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


def _fighter(rs, name, *, hp, max_hp, ac=12, intelligence=2, side="party"):
    c = rs.make_pc(name)
    c.sheet.update(hp=hp, max_hp=max_hp, ac=ac, intelligence=intelligence)
    return Fighter(c, side)


def test_hit_applies_damage():
    rs = DnDRuleset(dice=ScriptedDice(15, 4))
    tm = rs.turn_model()
    hero = rs.make_pc("Hero")
    goblin = rs.make_enemy("Goblin", hp=7, ac=12)
    res = tm.resolve_attack(hero, goblin)
    assert res.hit and res.band is Band.SUCCESS, res
    assert res.damage == 6, res
    rs.apply_damage(goblin, res.damage)
    assert goblin.sheet["hp"] == 1 and not rs.is_defeated(goblin)


def test_miss_deals_nothing():
    rs = DnDRuleset(dice=ScriptedDice(3))
    tm = rs.turn_model()
    res = tm.resolve_attack(rs.make_pc("Hero"), rs.make_enemy("Goblin", ac=12))
    assert not res.hit and res.band is Band.FAILURE and res.damage == 0, res


def test_crit_doubles_the_dice():
    rs = DnDRuleset(dice=ScriptedDice(20, 3, 5))
    tm = rs.turn_model()
    res = tm.resolve_attack(rs.make_pc("Hero"), rs.make_enemy("Goblin", ac=12))
    assert res.band is Band.CRITICAL and res.hit, res
    assert res.damage == 10, res


def test_natural_one_is_a_botch():
    rs = DnDRuleset(dice=ScriptedDice(1))
    tm = rs.turn_model()
    res = tm.resolve_attack(rs.make_pc("Hero"), rs.make_enemy("Goblin", ac=12))
    assert not res.hit and res.band is Band.BOTCH and res.damage == 0, res


def test_estimate_is_pure():
    rs = DnDRuleset(dice=ScriptedDice())
    tm = rs.turn_model()
    hero = rs.make_pc("Hero")
    sturdy = rs.make_enemy("Ogre", hp=7, ac=12)
    est = tm.estimate_attack(hero, sturdy)
    assert abs(est.hit_chance - 0.65) < 1e-9, est
    assert est.expected_damage == 5.5 and not est.could_drop, est
    frail = rs.make_enemy("Imp", hp=4, ac=12)
    assert tm.estimate_attack(hero, frail).could_drop


def test_initiative_orders_by_total():
    rs = DnDRuleset(dice=ScriptedDice(5, 18, 12))
    tm = rs.turn_model()
    a = rs.make_pc("A")
    b = rs.make_enemy("B")
    c = rs.make_enemy("C")
    order = tm.initiative_order([a, b, c])
    assert [combatant.name for combatant, _ in order] == ["B", "C", "A"], order


def test_pc_wins_a_one_hit_fight():
    rs = DnDRuleset(dice=ScriptedDice(18, 2, 15, 4))
    fake = FakeLLMClient(default_text="Steel flashes.",
                         default_json='{"action": "attack", "target": "Goblin"}')
    state = GameState(pc=rs.make_pc("Hero"), location="a guardroom")
    goblin = rs.make_enemy("Goblin", hp=4, ac=10)
    pres = ScriptedPresenter(["attack Goblin"])
    victor = CombatController(fake, pres, state, rs, enemies=[goblin]).run()
    assert victor == "party", victor
    assert goblin.sheet["hp"] <= 0
    kills = [e for e in pres.of_type(AttackResolved) if e.defeated]
    assert kills and kills[0].defender == "Goblin", pres.of_type(AttackResolved)
    assert pres.of_type(CombatEnded)[0].victor == "party"


def test_ai_focus_fires_the_wounded():
    from engine import ai
    rs = DnDRuleset(dice=ScriptedDice())
    tm = rs.turn_model()
    brute = Fighter(rs.make_enemy("Brute", attack=("jab", 4, "1d4"), intelligence=1), "enemies")
    healthy = _fighter(rs, "Healthy", hp=10, max_hp=10)
    wounded = _fighter(rs, "Wounded", hp=5, max_hp=10)
    action = ai.choose_action(brute, [healthy, wounded], [], rs, tm, random.Random(0))
    assert isinstance(action, Attack) and action.target.name == "Wounded", action


def test_ai_prioritizes_a_kill():
    from engine import ai
    rs = DnDRuleset(dice=ScriptedDice())
    tm = rs.turn_model()
    smasher = Fighter(rs.make_enemy("Smasher", attack=("smash", 4, "1d10+3"), intelligence=1), "enemies")
    droppable = _fighter(rs, "Droppable", hp=3, max_hp=10)
    full = _fighter(rs, "Full", hp=10, max_hp=10)
    action = ai.choose_action(smasher, [droppable, full], [], rs, tm, random.Random(0))
    assert isinstance(action, Attack) and action.target.name == "Droppable", action


def test_ai_passes_with_no_opponents():
    from engine import ai
    rs = DnDRuleset(dice=ScriptedDice())
    tm = rs.turn_model()
    lone = Fighter(rs.make_enemy("Lone", intelligence=1), "enemies")
    assert isinstance(ai.choose_action(lone, [], [], rs, tm, random.Random(0)), Pass)


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
