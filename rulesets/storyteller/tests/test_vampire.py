from __future__ import annotations

import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.combat import CombatController
from engine.creation import CharacterCreator
from engine.dice import ScriptedDice
from engine.engine import ExplorationEngine
from engine.events import (AttackResolved, CelerityActivated, CombatEnded, Event,
                        Frenzied, HumanityShift)
from engine.llm import FakeLLMClient, PromptBuilder
from engine.morality import MoralClassifier
from engine.outcome import PoolDifficulty
from rulesets.storyteller.core.storyteller import StorytellerRuleset
from engine.state import GameState


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


def test_generation_sets_blood_pool():
    rs = StorytellerRuleset()
    pc = rs.make_pc("Fledgling")
    assert pc.sheet["blood_max"] == 10 and pc.sheet["blood_per_turn"] == 1
    elder = rs.make_enemy("Elder", generation=8)
    assert elder.sheet["blood_max"] == 15 and elder.sheet["blood_per_turn"] == 3


def test_blood_spend_respects_per_turn_cap():
    rs = StorytellerRuleset()
    v = rs.make_pc("Thirsty")
    assert rs.spend_blood(v, 1) and v.sheet["blood"] == 9
    assert not rs.spend_blood(v, 1)
    rs.end_turn(v)
    assert rs.spend_blood(v, 1) and v.sheet["blood"] == 8


def test_combat_heal_costs_blood():
    rs = StorytellerRuleset()
    v = rs.make_pc("Wounded")
    v.sheet["health_taken"] = 3
    did, levels = rs.combat_heal(v)
    assert did and levels == 1 and v.sheet["health_taken"] == 2 and v.sheet["blood"] == 9
    assert rs.combat_heal(v) == (False, 0)


def test_potence_adds_automatic_damage():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 2, 2, 2, 2))
    atk = rs.make_enemy("Brute", attributes={"dexterity": 3}, abilities={"brawl": 2},
                        disciplines={"Potence": 2})
    res = rs.turn_model().resolve_attack(atk, rs.make_enemy("Mortal", soak=2))
    assert res.damage == 3, res


def test_fortitude_adds_soak():
    def brute(rs):
        return rs.make_enemy("Brute", attributes={"dexterity": 3}, abilities={"brawl": 2})
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 2, 2))
    assert rs.turn_model().resolve_attack(brute(rs), rs.make_enemy("Mortal", soak=2)).damage == 3
    rs2 = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 2, 2))
    res = rs2.turn_model().resolve_attack(
        brute(rs2), rs2.make_enemy("Elder", soak=2, disciplines={"Fortitude": 3}))
    assert res.hit and res.damage == 0, res


def test_auspex_sharpens_perception_only():
    rs = StorytellerRuleset(dice=ScriptedDice(2, 2, 2))
    seer = rs.make_enemy("Seer", attributes={"perception": 2},
                         abilities={"awareness": 1}, disciplines={"Auspex": 2})
    out = rs.resolve_check(seer, "awareness", PoolDifficulty(target=6))
    assert out.success and out.magnitude == 2, out
    rs2 = StorytellerRuleset(dice=ScriptedDice(2, 2, 2))
    bruiser = rs2.make_enemy("Bruiser", attributes={"dexterity": 2},
                             abilities={"brawl": 1}, disciplines={"Auspex": 2})
    assert not rs2.resolve_check(bruiser, "brawl", PoolDifficulty(target=6)).success


def test_celerity_grants_extra_actions_in_one_turn():
    rs = StorytellerRuleset(dice=ScriptedDice(9, 1, 6, 6, 2, 2, 2, 6, 6, 2, 2, 2))
    fake = FakeLLMClient(default_text="A blur of motion.",
                         default_json='{"action": "attack", "target": "Dummy"}')
    state = GameState(pc=rs.make_pc("Lucius"), location="a flooded car park")
    dummy = rs.make_enemy("Dummy", soak=4)
    dummy.sheet["health_taken"] = 5
    pres = ScriptedPresenter(["1", "attack Dummy", "attack Dummy"])
    victor = CombatController(fake, pres, state, rs, enemies=[dummy]).run()
    assert victor == "party", victor
    assert pres.of_type(CelerityActivated) and pres.of_type(CelerityActivated)[0].extra_actions == 1
    pc_hits = [e for e in pres.of_type(AttackResolved) if e.attacker == "Lucius"]
    assert len(pc_hits) == 2, pc_hits
    assert state.pc.sheet["blood"] == 9


def test_hunger_frenzy_forces_an_attack():
    rs = StorytellerRuleset(dice=ScriptedDice(9, 1, 2, 2, 2, 6, 6, 2, 2, 2))
    fake = FakeLLMClient(default_text="The Beast lunges.",
                         default_json='{"action": "pass"}')
    pc = rs.make_pc("Starving")
    pc.sheet["blood"] = 0
    pc.sheet["disciplines"] = {}
    state = GameState(pc=pc, location="a reeking alley")
    prey = rs.make_enemy("Prey", soak=0)
    prey.sheet["health_taken"] = 6
    pres = ScriptedPresenter([])
    victor = CombatController(fake, pres, state, rs, enemies=[prey]).run()
    assert victor == "party", victor
    assert pres.of_type(Frenzied) and pres.of_type(Frenzied)[0].name == "Starving"
    assert any(e.attacker == "Starving" and e.defeated for e in pres.of_type(AttackResolved))


def test_degeneration_holds_on_a_successful_conscience_roll():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6))
    v = rs.make_pc("Penitent")
    out = rs.degeneration_check(v, severity=5)
    assert out["checked"] and not out["lost"] and v.sheet["humanity"] == 7, out


def test_degeneration_loses_a_dot_on_failure():
    rs = StorytellerRuleset(dice=ScriptedDice(2, 2, 2))
    v = rs.make_pc("Slipping")
    out = rs.degeneration_check(v, severity=4)
    assert out["lost"] and not out["botch"] and v.sheet["humanity"] == 6, out


def test_degeneration_botch_adds_a_derangement():
    rs = StorytellerRuleset(dice=ScriptedDice(1, 2, 2))
    v = rs.make_pc("Cracking")
    out = rs.degeneration_check(v, severity=5)
    assert out["lost"] and out["botch"] and out["derangement"]
    assert v.sheet["humanity"] == 6 and v.sheet["derangements"], v.sheet


def test_minor_sins_do_not_test_the_callous():
    rs = StorytellerRuleset(dice=ScriptedDice(2, 2, 2))
    v = rs.make_pc("Hardened")
    v.sheet["humanity"] = 5
    out = rs.degeneration_check(v, severity=1)
    assert not out["checked"] and v.sheet["humanity"] == 5


def test_build_pc_distributes_clan_disciplines():
    rs = StorytellerRuleset()
    pc = rs.build_pc({"name": "Sol", "clan": "brujah",
                      "attributes": {"strength": 4, "dexterity": 3, "stamina": 3,
                                     "wits": 2, "charisma": 2, "intelligence": 1},
                      "discipline": "celerity"})
    s = pc.sheet
    assert s["clan"] == "Brujah"
    assert s["disciplines"] == {"Celerity": 2, "Potence": 1, "Presence": 1}, s["disciplines"]
    assert s["humanity"] == 7 and s["blood"] == 10 and s["virtues"]["courage"] == 3


def test_moral_classifier_reads_severity():
    rs = StorytellerRuleset()
    clf = MoralClassifier(rs.morality())
    hot = FakeLLMClient(default_json='{"severity": 4}')
    assert clf.severity(hot, PromptBuilder(), "I beat the man bloody") == 4
    cold = FakeLLMClient(default_json='{"oops": true}')
    assert clf.severity(cold, PromptBuilder(), "I greet the man") == 0


def test_engine_moral_pass_erodes_humanity():
    rs = StorytellerRuleset(dice=ScriptedDice(2, 2, 2))
    fake = FakeLLMClient(default_text="Something in you goes quiet.",
                         default_json='{"severity": 5}')
    pres = ScriptedPresenter()
    state = GameState(pc=rs.make_pc("Lucius"), location="a tenement stairwell")
    eng = ExplorationEngine(client=fake, presenter=pres, state=state, ruleset=rs)
    eng._moral_check("I cut the family down where they stand")
    shifts = pres.of_type(HumanityShift)
    assert shifts and shifts[0].lost and shifts[0].after == 6
    assert state.pc.sheet["humanity"] == 6


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
