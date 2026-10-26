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
from engine.difficulty import DifficultyBand
from engine.dice import ScriptedDice
from engine.engine import ExplorationEngine
from engine.events import AttackResolved, CheckResolved, CombatEnded, Event
from engine.llm import FakeLLMClient
from engine.outcome import Band, PoolDifficulty
from rulesets.dnd.core.dnd import DnDRuleset
from rulesets.storyteller.core.storyteller import StorytellerRuleset
from rulesets.storyteller.core.storyteller_combat import band_for_net
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


class RecordingCtx:
    def __init__(self):
        self.calls = []

    def is_active(self, c): return True
    def combat_over(self): return False
    def begin_round(self): self.calls.append(("begin_round", None))
    def declare(self, c): self.calls.append(("declare", c.name))
    def announce_turn(self, c): self.calls.append(("announce", c.name))
    def resolve(self, c): self.calls.append(("resolve", c.name))
    def begin_turn(self, c): self.calls.append(("begin_turn", c.name))
    def take_turn(self, c): self.calls.append(("take_turn", c.name))


def _probe(rs, *, dex=2, brawl=1):
    return rs.make_enemy("Probe", attributes={"dexterity": dex}, abilities={"brawl": brawl})


def test_pool_marginal_is_native():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 2, 2))
    out = rs.resolve_check(_probe(rs), "brawl", PoolDifficulty(target=6))
    assert out.band is Band.MARGINAL and out.success and out.magnitude == 1, out


def test_pool_botch_needs_a_one():
    rs = StorytellerRuleset(dice=ScriptedDice(1, 2, 3))
    out = rs.resolve_check(_probe(rs), "brawl", PoolDifficulty(target=6))
    assert out.band is Band.BOTCH and not out.success and out.is_botch


def test_failure_without_a_one_is_not_a_botch():
    rs = StorytellerRuleset(dice=ScriptedDice(2, 3, 4))
    out = rs.resolve_check(_probe(rs), "brawl", PoolDifficulty(target=6))
    assert out.band is Band.FAILURE and not out.is_botch and not out.success


def test_ones_cancel_successes():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 1))
    out = rs.resolve_check(_probe(rs), "brawl", PoolDifficulty(target=6))
    assert out.band is Band.MARGINAL and out.magnitude == 1, out


def test_exceptional_success():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 7, 8, 9, 10, 6))
    out = rs.resolve_check(_probe(rs, dex=3, brawl=3), "brawl", PoolDifficulty(target=6))
    assert out.band is Band.EXCEPTIONAL and out.magnitude == 6, out


def test_storyteller_never_emits_critical():
    assert all(band_for_net(s, o, s - o) is not Band.CRITICAL
               for s in range(0, 12) for o in range(0, 5))


def test_harder_band_raises_the_target_number():
    assert StorytellerRuleset().difficulty_for_band(DifficultyBand.MEDIUM).target == 6
    assert StorytellerRuleset().difficulty_for_band(DifficultyBand.HARD).target == 7
    easy = StorytellerRuleset(dice=ScriptedDice(6, 6, 6))
    hard = StorytellerRuleset(dice=ScriptedDice(6, 6, 6))
    assert easy.resolve_check(_probe(easy), "brawl", PoolDifficulty(target=6)).success
    assert not hard.resolve_check(_probe(hard), "brawl", PoolDifficulty(target=7)).success


def test_wounds_raise_check_difficulty():
    rs = StorytellerRuleset()
    actor = rs.make_pc("Lucius")
    assert rs.situational_difficulty_delta(actor, "brawl") == 0
    actor.sheet["health_taken"] = 4
    assert rs.situational_difficulty_delta(actor, "brawl") == 2
    actor.sheet["health_taken"] = 6
    assert rs.situational_difficulty_delta(actor, "brawl") == 3


def test_wounds_cut_the_combat_pool():
    rs = StorytellerRuleset(dice=ScriptedDice(2, 2, 2))
    tm = rs.turn_model()
    attacker = rs.make_enemy("Brute", attributes={"dexterity": 3}, abilities={"brawl": 2})
    attacker.sheet["health_taken"] = 4
    res = tm.resolve_attack(attacker, rs.make_enemy("Target"))
    assert res.raw["pool"] == 3, res.raw


def test_attack_deals_health_levels():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 2, 2))
    tm = rs.turn_model()
    atk = rs.make_enemy("Striker", attributes={"dexterity": 3}, abilities={"brawl": 2})
    target = rs.make_enemy("Mortal", soak=2)
    res = tm.resolve_attack(atk, target)
    assert res.hit and res.band is Band.SUCCESS and res.damage == 3, res


def test_attack_botch_misses():
    rs = StorytellerRuleset(dice=ScriptedDice(1, 2, 3, 4, 5))
    tm = rs.turn_model()
    atk = rs.make_enemy("Striker", attributes={"dexterity": 3}, abilities={"brawl": 2})
    res = tm.resolve_attack(atk, rs.make_enemy("Mortal"))
    assert not res.hit and res.band is Band.BOTCH and res.damage == 0


def test_soak_can_absorb_a_hit():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 2, 2, 2, 2))
    tm = rs.turn_model()
    atk = rs.make_enemy("Striker", attributes={"dexterity": 3}, abilities={"brawl": 2})
    res = tm.resolve_attack(atk, rs.make_enemy("Tough", soak=5))
    assert res.hit and res.damage == 0, res


def test_storyteller_declares_reverse_resolves_forward():
    rs = StorytellerRuleset(dice=ScriptedDice())
    order = [rs.make_enemy("A"), rs.make_enemy("B"), rs.make_enemy("C")]
    ctx = RecordingCtx()
    rs.turn_model().run_round(order, ctx)
    declares = [n for m, n in ctx.calls if m == "declare"]
    resolves = [n for m, n in ctx.calls if m == "resolve"]
    assert ctx.calls[0] == ("begin_round", None)
    assert declares == ["C", "B", "A"], declares
    assert resolves == ["A", "B", "C"], resolves


def test_dnd_round_is_a_single_pass():
    rs = DnDRuleset(dice=ScriptedDice())
    order = [rs.make_enemy("A"), rs.make_enemy("B"), rs.make_enemy("C")]
    ctx = RecordingCtx()
    rs.turn_model().run_round(order, ctx)
    takes = [n for m, n in ctx.calls if m == "take_turn"]
    assert takes == ["A", "B", "C"], takes
    assert not any(m in ("declare", "resolve", "begin_round") for m, _ in ctx.calls)


def test_storyteller_fight_resolves_on_shared_controller():
    rs = StorytellerRuleset(dice=ScriptedDice(8, 2, 6, 2, 2, 2, 2))
    fake = FakeLLMClient(default_text="Fangs flash.",
                         default_json='{"action": "attack", "target": "Ghoul"}')
    state = GameState(pc=rs.make_pc("Lucius"), location="a rain-slick rooftop")
    ghoul = rs.make_enemy("Ghoul")
    ghoul.sheet["health_taken"] = 6
    pres = ScriptedPresenter(["no", "attack Ghoul"])
    victor = CombatController(fake, pres, state, rs, enemies=[ghoul]).run()
    assert victor == "party", victor
    assert rs.is_defeated(ghoul)
    kills = [e for e in pres.of_type(AttackResolved) if e.defeated]
    assert kills and kills[0].defender == "Ghoul"
    assert pres.of_type(CombatEnded)[0].victor == "party"


def test_storyteller_creation_builds_a_vampire():
    rs = StorytellerRuleset()
    pres = ScriptedPresenter(["Lucius", "Ventrue", "4", "3", "3", "2", "2", "1", "Fortitude"])
    pc = CharacterCreator(pres, rs).run()
    s = pc.sheet
    assert pc.name == "Lucius" and s["clan"] == "Ventrue"
    assert s["attributes"]["strength"] == 4 and s["attributes"]["intelligence"] == 1
    assert s["disciplines"] == {"Dominate": 1, "Fortitude": 2, "Presence": 1}, s["disciplines"]
    assert s["soak"] == 5
    assert s["humanity"] == 7 and s["blood_max"] == 10
    assert s["virtues"]["conscience"] == 3


def test_engine_check_path_with_storyteller():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 2, 2, 2))
    fake = FakeLLMClient(default_text="You melt into the fog.",
                         default_json='{"intent":"check_action","skill":"stealth","approach":"slip past"}')
    pres = ScriptedPresenter(["I slip past the watchman"])
    state = GameState(pc=rs.make_pc("Lucius"), location="a fog-choked wynd")
    ExplorationEngine(client=fake, presenter=pres, state=state, ruleset=rs).run()
    checks = pres.of_type(CheckResolved)
    assert checks and checks[0].success and checks[0].band == "success", checks
    assert "pool" in checks[0].raw


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
