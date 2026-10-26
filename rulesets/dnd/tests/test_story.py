import sys, pathlib, json, shutil

_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.combat import CombatController
from engine.dice import ScriptedDice
from engine.engine import ExplorationEngine
from engine.events import EventTransition, StoryBeat, TaskUpdated
from engine.llm import FakeLLMClient
from engine.outcome import Band, Outcome
from engine.story import (Adventure, StoryClassifier, StoryController, StoryEvent, Task,
                          Outcome as SOutcome, evaluate)
from rulesets.dnd.core.dnd import DnDRuleset
from web import catalog as C


class Rec:
    def __init__(self, inputs=()):
        self.events = []
        self.inputs = list(inputs)
    def emit(self, e):
        self.events.append(e)
    def read_action(self):
        if not self.inputs:
            raise EOFError
        return self.inputs.pop(0)


class Intent:
    def __init__(self, skill="", typ="dialogue"):
        self.skill = skill
        self.type = typ


def _session(dice_default=15):
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "oota_ch1")
    rs.dice = ScriptedDice(default=dice_default)
    rec = Rec()
    eng = ExplorationEngine(client=FakeLLMClient(default_text="..."), presenter=rec,
                            state=state, ruleset=rs, scene=scene)
    eng.story = StoryController.start(rs.build_adventure("oota_ch1"), eng)
    return rs, state, eng, rec


def _check(band):
    return Outcome(success=band in ("marginal", "success", "exceptional", "critical"),
                   band=Band(band), magnitude=1)


def test_dsl_predicates_and_composition():
    from engine.story import StoryContext
    ctx = StoryContext(scene_key="velkynvelve", zone="slave_pens", visited=frozenset({"slave_pens"}),
                       flags={"allies_freed": True}, defeated=frozenset({"ilvara"}),
                       present=frozenset({"jimjar"}), inventory=frozenset({"drow_poison_vial"}),
                       last_skill="sleight_of_hand", last_band="success", last_success=True,
                       tag="toward_lake", task_states={"free_allies": "full"},
                       npc_progress={"r": {"phase": 2, "done": False}}, alarm="suspicious")
    cases = [
        ({"at": "slave_pens"}, True), ({"at": "x"}, False),
        ({"flag": "allies_freed"}, True), ({"flag": "allies_freed", "eq": False}, False),
        ({"defeated": "ilvara"}, True), ({"has_item": "drow_poison_vial"}, True),
        ({"check": "sleight_of_hand", "band_at_least": "success"}, True),
        ({"check": "sleight_of_hand", "band_at_least": "critical"}, False),
        ({"check": "athletics", "band_at_least": "marginal"}, False),
        ({"tag": "toward_lake"}, True), ({"tag": "toward_forge"}, False),
        ({"task": "free_allies", "state": "full"}, True),
        ({"task": "free_allies", "state": "done"}, True),
        ({"npc_task": "r", "phase_at_least": 2}, True), ({"npc_task": "r", "done": True}, False),
        ({"alarm": "suspicious"}, True), ({"alarm": "alert"}, False),
        ({"all": [{"at": "slave_pens"}, {"flag": "allies_freed"}]}, True),
        ({"any": [{"at": "x"}, {"flag": "allies_freed"}]}, True),
        ({"not": {"at": "x"}}, True), ([{"at": "slave_pens"}, {"defeated": "ilvara"}], True),
        (True, True), ({}, True), (False, False), (None, False),
    ]
    bad = [(c, exp, evaluate(c, ctx)) for c, exp in cases if evaluate(c, ctx) != exp]
    assert not bad, bad


def test_dsl_json_serializable():
    tree = {"all": [{"at": "slave_pens"}, {"any": [{"tag": "toward_lake"},
            {"check": "persuasion", "band_at_least": "success"}]}, {"not": {"flag": "x"}}]}
    assert json.loads(json.dumps(tree)) == tree


def test_classifier_keyword_fallback():
    sc = StoryClassifier([("toward_lake", "to the water", ("lake", "water", "boat")),
                          ("toward_forge", "to the forge", ("forge", "gate", "smoke"))])
    assert sc._keyword("I run toward the water") == "toward_lake"
    assert sc._keyword("make for the forge gate") == "toward_forge"
    assert sc._keyword("I wait and listen") == ""
    assert sc.classify(FakeLLMClient(default_text="hmm"), __import__("engine.llm", fromlist=["PromptBuilder"]).PromptBuilder(),
                       "toward the boats on the water") == "toward_lake"


def test_all_oota_scenes_build():
    rs = DnDRuleset(); rs.use_setting("forgotten_realms")
    for key in ("velkynvelve", "gracklstugh_gate", "sloobludop_shore"):
        assert rs.build_scene(key) is not None, key


def test_event_entry_loads_scene_and_emits():
    rs, state, eng, rec = _session()
    eng.story.on_start()
    assert eng.story.current == "velkynvelve_escape"
    assert eng.scene is not None and eng.scene.key == "velkynvelve"
    assert state.flags["story"]["current"] == "velkynvelve_escape"
    assert any(isinstance(e, EventTransition) for e in rec.events)
    assert any(isinstance(e, StoryBeat) for e in rec.events)
    assert {"ront", "pog"} <= set(eng.scene.presences)


def _free_allies(band):
    rs, state, eng, rec = _session()
    eng.story.on_start()
    eng.story.on_action("pick the lock", Intent("sleight_of_hand", "check_action"), _check(band), "")
    return state, eng


def test_free_allies_full_partial_fail():
    state, eng = _free_allies("success")
    assert eng.story.task_states["free_allies"] == "full" and state.flags.get("allies_freed") is True
    assert eng.scene.presence("guard_a").awareness == "unaware"
    state, eng = _free_allies("marginal")
    assert eng.story.task_states["free_allies"] == "partial" and state.flags.get("allies_freed") is True
    assert eng.scene.presence("guard_a").awareness == "suspicious"
    state, eng = _free_allies("botch")
    assert eng.story.task_states["free_allies"] == "fail" and not state.flags.get("allies_freed")
    assert eng.scene.presence("guard_a").awareness == "alert"


def test_route_tag_branches():
    for phrase, dest, route in [("we flee toward the dark water", "sloobludop_arrival", "lake"),
                                ("head for the forge smoke", "gracklstugh_arrival", "forge")]:
        rs, state, eng, rec = _session()
        eng.story.on_start()
        eng.story.enter_event("underdark_flight")
        tag = eng.story.classify_tag(phrase)
        eng.story.on_action(phrase, Intent("", "dialogue"), None, tag)
        assert eng.story.current == dest and state.flags.get("route") == route, (phrase, eng.story.current)


def test_move_transition_to_flight():
    rs, state, eng, rec = _session()
    eng.story.on_start()
    eng.story.on_action("pick the lock", Intent("sleight_of_hand", "check_action"), _check("success"), "")
    res = eng.scene.move_pc("rope_bridge"); assert res["ok"]
    eng.story.on_move(res["zone"])
    assert eng.story.current == "underdark_flight" and eng.scene is None


def test_ilvara_ritual_ticks_per_round_and_completes():
    rs, state, eng, rec = _session(dice_default=20)
    eng.story.on_start()
    prog = lambda: eng.story.npc_progress["ilvara_ritual"]
    eng.story.on_combat_round(); assert prog()["phase"] == 1
    eng.story.on_combat_round(); assert prog()["phase"] == 2
    eng.story.on_combat_round()
    assert prog()["done"] is True
    assert eng.scene.presence("quaggoth").zone == "priestess_platform"


def test_ilvara_ritual_aborts_when_she_is_defeated():
    rs, state, eng, rec = _session(dice_default=20)
    eng.story.on_start()
    eng.scene.presence("ilvara").combatant.sheet["hp"] = 0
    eng.story.on_combat_round()
    assert eng.story.npc_progress["ilvara_ritual"]["phase"] == 0
    assert eng.story.npc_progress["ilvara_ritual"]["done"] is False


def test_pursuit_advances_over_long_rests():
    rs, state, eng, rec = _session()
    eng.story.on_start()
    eng.story.enter_event("underdark_flight")
    eng.story.on_long_rest(); eng.story.on_long_rest()
    assert eng.story.npc_progress["pursuit"]["done"] is True and state.flags.get("hunted") is True


def test_combat_controller_invokes_story_hooks():
    from engine.state import GameState
    rs = DnDRuleset()
    rs.dice = ScriptedDice(default=1)
    state = GameState(pc=rs.make_pc("Hero"))

    class Spy:
        def __init__(self): self.rounds = 0; self.turns = []
        def on_combat_round(self): self.rounds += 1
        def on_combat_turn(self, a): self.turns.append(a)
        def on_combat_end(self, v): self.ended = v

    spy = Spy()

    class PassPresenter(Rec):
        def read_action(self): return "pass"

    foe = rs.make_enemy("Goblin", hp=50, ac=25, attack=("club", 0, "1d4"))
    ctrl = CombatController(FakeLLMClient(default_text=".", default_json='{"action":"pass"}'),
                            PassPresenter(), state, rs, enemies=[foe],
                            rng=__import__("random").Random(1), story=spy)
    ctrl.run()
    assert spy.rounds >= 1 and spy.turns
    assert getattr(spy, "ended", None) is None


def test_default_inert_without_story():
    rs, state, scene, comps = C.build_session("dnd", "forgotten_realms", "watchers_barrow")
    rs.dice = ScriptedDice(default=12)
    pres = Rec(inputs=["look", "quit"])
    eng = ExplorationEngine(client=FakeLLMClient(default_text="A quiet barrow."),
                            presenter=pres, state=state, ruleset=rs, scene=scene)
    assert eng.story is None
    eng.run()
    assert "story" not in state.flags


def test_save_load_round_trip_preserves_story():
    rs, state, eng, rec = _session()
    eng.story.on_start()
    eng.story.on_action("pick the lock", Intent("sleight_of_hand", "check_action"), _check("success"), "")
    res = eng.scene.move_pc("rope_bridge"); eng.story.on_move(res["zone"])
    assert eng.story.current == "underdark_flight"
    slot = "__story_test__"
    try:
        C.save_session(slot, ruleset_key="dnd", setting_key="forgotten_realms", story_key="oota_ch1",
                       state=state, scene=eng.scene, companions=[])
        rk, sk, stk, rs2, state2, scene2, comps2 = C.load_saved(slot)
        assert state2.flags.get("allies_freed") is True and "story" in state2.flags
        eng2 = ExplorationEngine(client=FakeLLMClient(default_text="."), presenter=Rec(),
                                 state=state2, ruleset=rs2, scene=scene2)
        ctrl2 = StoryController.hydrate(rs2.build_adventure("oota_ch1"), eng2, state2.flags["story"])
        assert ctrl2.current == "underdark_flight"
        assert ctrl2.task_states.get("free_allies") == "full"
        eng2.story = ctrl2
        ctrl2.on_action("toward the water", Intent("", "dialogue"), None, ctrl2.classify_tag("toward the water"))
        assert ctrl2.current == "sloobludop_arrival"
    finally:
        shutil.rmtree(C.SAVES_DIR / slot, ignore_errors=True)


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
