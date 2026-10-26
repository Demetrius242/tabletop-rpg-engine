from __future__ import annotations

import random
import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine import ai
from engine.combat import CombatController, Fighter
from engine.dice import ScriptedDice
from engine.events import (AttackResolved, CombatEnded, Event, Fled, MoraleBroke,
                        Moved, OrderIssued, SocialResolved)
from engine.llm import FakeLLMClient
from rulesets.dnd.core.dnd import DnDRuleset
from engine.state import GameState
from engine.turnmodel import Attack
from engine.zones import Arena, Zone


class ScriptedPresenter:
    def __init__(self, inputs=()):
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


def _build(rs, *, enemies, companions=(), arena=None, inputs=(),
           default_json='{"action": "pass"}'):
    state = GameState(pc=rs.make_pc("Wren"), location="a hall")
    pres = ScriptedPresenter(inputs)
    client = FakeLLMClient(default_text="Blades meet.", default_json=default_json)
    ctrl = CombatController(client, pres, state, rs, enemies=enemies,
                            companions=companions, arena=arena)
    return ctrl, pres


def _two_zone(a="A", b="B", placements=None):
    return Arena(
        zones={a: Zone(a, frozenset({b})), b: Zone(b, frozenset({a}))},
        placements=placements or {},
    )


def _party_fighter(rs, name, *, hp, max_hp, side="party"):
    c = rs.make_pc(name)
    c.sheet.update(hp=hp, max_hp=max_hp)
    return Fighter(c, side)


def test_shortest_path_and_step():
    chain = {n: Zone(n, frozenset(adj)) for n, adj in
             {"A": "B", "B": "AC", "C": "BD", "D": "C"}.items()}
    arena = Arena({n: Zone(n, frozenset(z.adjacent)) for n, z in
                   {"A": Zone("A", frozenset({"B"})),
                    "B": Zone("B", frozenset({"A", "C"})),
                    "C": Zone("C", frozenset({"B", "D"})),
                    "D": Zone("D", frozenset({"C"}))}.items()})
    assert arena.shortest_path("A", "D") == ["A", "B", "C", "D"]
    assert arena.step_toward("A", "D") == "B"
    assert arena.step_toward("A", "A") is None


def test_melee_reach_requires_same_zone():
    rs = DnDRuleset(dice=ScriptedDice())
    arena = _two_zone(placements={"Wren": "A", "Goblin": "B"})
    ctrl, _ = _build(rs, enemies=[rs.make_enemy("Goblin")], arena=arena)
    pc, gob = ctrl.by_name["wren"], ctrl.by_name["goblin"]
    assert not ctrl._in_reach(pc, gob)
    gob.zone = "A"
    assert ctrl._in_reach(pc, gob)


def test_ranged_reaches_across_zones():
    rs = DnDRuleset(dice=ScriptedDice())
    arena = _two_zone(placements={"Wren": "A", "Archer": "B"})
    ctrl, _ = _build(rs, enemies=[rs.make_enemy("Archer", attack=("bow", 4, "1d6"),
                                                reach="ranged")], arena=arena)
    assert ctrl._in_reach(ctrl.by_name["archer"], ctrl.by_name["wren"])


def test_moving_out_of_melee_provokes():
    rs = DnDRuleset(dice=ScriptedDice(15, 3))
    arena = _two_zone(placements={"Wren": "A", "Goblin": "A"})
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")], arena=arena)
    pc, gob = ctrl.by_name["wren"], ctrl.by_name["goblin"]
    budget = ctrl.tm.new_turn_budget(pc.combatant)
    ctrl._move(pc, "B", budget, provoke=True)
    oas = [e for e in pres.of_type(AttackResolved) if e.raw.get("opportunity")]
    assert oas and oas[0].attacker == "Goblin" and oas[0].hit, oas
    assert not gob.reaction_available
    assert pc.combatant.sheet["hp"] == 8 and pc.zone == "B"


def test_retreat_does_not_provoke():
    rs = DnDRuleset(dice=ScriptedDice())
    arena = _two_zone(placements={"Wren": "A", "Goblin": "A"})
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")], arena=arena)
    pc, gob = ctrl.by_name["wren"], ctrl.by_name["goblin"]
    budget = ctrl.tm.new_turn_budget(pc.combatant)
    ctrl._move(pc, "B", budget, provoke=False)
    assert not pres.of_type(AttackResolved)
    assert gob.reaction_available and pc.combatant.sheet["hp"] == 12 and pc.zone == "B"


def test_flee_from_exit_ends_combat():
    rs = DnDRuleset(dice=ScriptedDice(18, 2))
    arena = Arena(
        zones={"gate": Zone("gate", frozenset({"yard"}), is_exit=True),
               "yard": Zone("yard", frozenset({"gate"}))},
        placements={"Wren": "gate", "Goblin": "yard"})
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")], arena=arena,
                        inputs=["flee"], default_json='{"action": "flee"}')
    victor = ctrl.run()
    assert victor == "fled", victor
    assert any(e.name == "Wren" for e in pres.of_type(Fled))
    assert pres.of_type(CombatEnded)[0].victor == "fled"


def test_order_to_mindless_ally_is_void():
    rs = DnDRuleset(dice=ScriptedDice())
    comp = rs.make_companion("Hound")
    comp.sheet.update(comprehends_language=False, mindless=True)
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")], companions=[comp])
    pc, ally = ctrl.by_name["wren"], ctrl.by_name["hound"]
    ctrl._issue_order(pc, "Hound", "focus", "Goblin", [ally],
                      ctrl._living("enemies"))
    issued = pres.of_type(OrderIssued)[0]
    assert not issued.delivered and ally.directive == ""


def test_order_to_normal_ally_sets_directive():
    rs = DnDRuleset(dice=ScriptedDice())
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")],
                        companions=[rs.make_companion("Mara")])
    pc, ally = ctrl.by_name["wren"], ctrl.by_name["mara"]
    ctrl._issue_order(pc, "Mara", "focus", "Goblin", [ally], ctrl._living("enemies"))
    issued = pres.of_type(OrderIssued)[0]
    assert issued.delivered and ally.directive == "focus" and ally.directive_target == "Goblin"


def test_social_to_mindless_enemy_is_void():
    rs = DnDRuleset(dice=ScriptedDice())
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Ooze", mindless=True)])
    pc, ooze = ctrl.by_name["wren"], ctrl.by_name["ooze"]
    ctrl._social(pc, "Ooze", "intimidate", [ooze])
    res = pres.of_type(SocialResolved)[0]
    assert not res.delivered and ooze.combatant.sheet["morale"] == 100


def test_intimidate_breaks_morale():
    rs = DnDRuleset(dice=ScriptedDice(15))
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin", morale=50)])
    pc, gob = ctrl.by_name["wren"], ctrl.by_name["goblin"]
    ctrl._social(pc, "Goblin", "intimidate", [gob])
    res = pres.of_type(SocialResolved)[0]
    assert res.delivered and res.band == "success" and res.effect == "breaking", res
    assert gob.broken and gob.combatant.sheet["morale"] == 10


def test_broken_enemy_in_exit_routs():
    rs = DnDRuleset(dice=ScriptedDice())
    arena = Arena(zones={"gate": Zone("gate", frozenset(), is_exit=True)},
                  placements={"Wren": "gate", "Goblin": "gate"})
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")], arena=arena)
    gob = ctrl.by_name["goblin"]
    gob.broken = True
    ctrl._rout(gob, ctrl.tm.new_turn_budget(gob.combatant))
    assert gob.fled
    broke = pres.of_type(MoraleBroke)[0]
    assert broke.name == "Goblin" and broke.outcome == "routed"


def test_taunt_forces_enemy_onto_pc():
    rs = DnDRuleset(dice=ScriptedDice(15))
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")])
    pc, gob = ctrl.by_name["wren"], ctrl.by_name["goblin"]
    ctrl._social(pc, "Goblin", "taunt", [gob])
    assert gob.taunted_by == "Wren"
    assert ctrl._priority_target(gob) == "Wren"


def test_focus_order_sets_priority():
    rs = DnDRuleset(dice=ScriptedDice())
    ctrl, _ = _build(rs, enemies=[rs.make_enemy("Goblin"), rs.make_enemy("Goblin")],
                     companions=[rs.make_companion("Mara")])
    mara = ctrl.by_name["mara"]
    mara.directive = "focus"
    mara.directive_target = "Goblin 2"
    assert ctrl._priority_target(mara) == "Goblin 2"


def test_ai_honors_priority_target():
    rs = DnDRuleset(dice=ScriptedDice())
    tm = rs.turn_model()
    enemy = Fighter(rs.make_enemy("Smasher", intelligence=1), "enemies")
    alpha = _party_fighter(rs, "Alpha", hp=5, max_hp=10)
    beta = _party_fighter(rs, "Beta", hp=10, max_hp=10)
    action = ai.choose_action(enemy, [alpha, beta], [], rs, tm, random.Random(0),
                              priority_target="Beta")
    assert isinstance(action, Attack) and action.target.name == "Beta", action


def test_ai_closes_distance_when_no_target():
    rs = DnDRuleset(dice=ScriptedDice(15, 3))
    arena = _two_zone("yard", "ledge", placements={"Wren": "yard", "Goblin": "ledge"})
    ctrl, pres = _build(rs, enemies=[rs.make_enemy("Goblin")], arena=arena)
    gob = ctrl.by_name["goblin"]
    ctrl._ai_turn(gob, ctrl.tm.new_turn_budget(gob.combatant))
    assert gob.zone == "yard"
    hits = [e for e in pres.of_type(AttackResolved) if e.attacker == "Goblin"]
    assert hits and hits[0].defender == "Wren" and hits[0].hit
    assert ctrl.by_name["wren"].combatant.sheet["hp"] == 8


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
