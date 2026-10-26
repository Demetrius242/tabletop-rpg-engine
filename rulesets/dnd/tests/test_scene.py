import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

import engine.combat as combat_mod
from engine.engine import ExplorationEngine
from engine.events import CheckResolved, Narration, StateDelta, SystemMessage
from engine.llm import FakeLLMClient
from engine.scene import Feature, Presence, Scene, SceneZone
from engine.state import Combatant, GameState
from engine.dice import ScriptedDice
from rulesets.dnd.core.dnd import DnDRuleset


class _Pres:
    def __init__(self, inputs=()):
        self._i = list(inputs); self.events = []
    def emit(self, e): self.events.append(e)
    def read_action(self):
        if not self._i:
            raise EOFError
        return self._i.pop(0)


def _dungeon(rs):
    def en(name, hp=11, ac=12):
        return rs.make_enemy(name, hp=hp, ac=ac)
    return Scene(
        key="keep", name="The Ruined Keep", kind="dungeon",
        zones={
            "gate": SceneZone("gate", "The Gatehouse", "A collapsed gate.", adjacent=("court",), is_exit=True),
            "court": SceneZone("court", "The Courtyard", "Open ground.", adjacent=("gate", "hall")),
            "hall": SceneZone("hall", "The Great Hall", "A soot-stained hall.", adjacent=("court", "crypt")),
            "crypt": SceneZone("crypt", "The Crypt", "Cold dark.", adjacent=("hall",)),
        },
        features={
            "rubble": Feature("rubble", "a rubble pile", "gate", interactions=("search",), contents=("potion_of_healing",)),
            "trap": Feature("trap", "a floor-trap", "court", hidden=True, notice="easy"),
            "altar": Feature("altar", "a defaced altar", "hall", interactions=("take",), contents=("scroll_of_revivify",)),
            "door": Feature("door", "an iron door", "hall", locked=True, gates="crypt"),
        },
        presences={
            "surv": Presence("surv", "a frightened survivor", "gate", kind="npc", disposition="friendly"),
            "c1": Presence("c1", "a cultist", "hall", kind="enemy", disposition="hostile", awareness="unaware", combatant=en("Cultist A")),
            "c2": Presence("c2", "a cultist", "hall", kind="enemy", disposition="hostile", awareness="unaware", combatant=en("Cultist B")),
            "boss": Presence("boss", "the cult leader", "crypt", kind="enemy", disposition="hostile", hidden=True, notice="hard", combatant=en("Cult Leader", 20)),
        },
        pc_zone="gate")


def _rogue(rs):
    pc = rs.build_pc({"name": "Aria", "race": "elf", "class": "rogue", "background": "criminal",
                      "alignment": "cn",
                      "abilities": {"dex": 15, "int": 14, "con": 13, "wis": 12, "cha": 10, "str": 8},
                      "skills": ["stealth", "perception", "investigation", "sleight_of_hand"]})
    pc.sheet["proficiencies"] = list(pc.sheet.get("proficiencies", [])) + ["thieves_tools"]
    return pc


def _eng(rs, scene, pc, inputs=()):
    return ExplorationEngine(client=FakeLLMClient(default_text="(narration)"),
                             presenter=_Pres(inputs), state=GameState(pc=pc, location="The Gatehouse"),
                             ruleset=rs, scene=scene)


def test_navigation_respects_adjacency():
    s = _dungeon(DnDRuleset())
    assert s.move_pc("crypt")["ok"] is False
    assert s.move_pc("courtyard")["ok"] is True and s.pc_zone == "court"
    assert s.move_pc("hall")["ok"] is True and s.pc_zone == "hall"


def test_locked_door_gates_a_zone_until_opened():
    s = _dungeon(DnDRuleset())
    s.pc_zone = "hall"
    assert s.can_move("crypt")["ok"] is False
    assert s.unlock("door") is True
    assert s.can_move("crypt")["ok"] is True


def test_search_reveals_by_result_quality():
    s = _dungeon(DnDRuleset())
    s.pc_zone = "court"
    assert s.search("failure")["found_anything"] is False
    found = s.search("success")
    assert any(f.key == "trap" for f in found["features"])
    assert s.feature("trap").hidden is False


def test_take_yields_contents_once():
    s = _dungeon(DnDRuleset())
    s.pc_zone = "hall"
    out = s.take("altar")
    assert out["ok"] and out["items"] == ["scroll_of_revivify"]
    assert s.take("altar")["ok"] is False


def test_reveal_enemies_finds_hidden_foes():
    s = _dungeon(DnDRuleset())
    sensed = s.reveal_enemies()
    names = {d["name"] for d in sensed}
    assert "the cult leader" in names
    assert s.presence("boss").hidden is False
    assert any(d["was_hidden"] for d in sensed)


def test_alertness_and_surprise():
    rs = DnDRuleset(); s = _dungeon(rs)
    s.pc_zone = "hall"
    assert s.alertness() == "unaware"
    handoff = s.to_combat(_rogue(rs))
    assert handoff["surprise"] == "party"
    assert s.alertness() == "alert"


def test_to_combat_places_present_enemies_on_the_zone_graph():
    rs = DnDRuleset(); s = _dungeon(rs); pc = _rogue(rs)
    s.pc_zone = "hall"
    s.unlock("door")
    handoff = s.to_combat(pc)
    enames = {e.name for e in handoff["enemies"]}
    assert "Cultist A" in enames and "Cultist B" in enames
    assert "Cult Leader" in enames
    arena = handoff["arena"]
    assert set(arena.zones) == {"gate", "court", "hall", "crypt"}
    assert arena.placements[pc.name] == "hall"
    assert arena.placements["Cult Leader"] == "crypt"


def test_exploration_verbs_are_handled_in_python():
    rs = DnDRuleset(); rs.dice = ScriptedDice(default=18)
    s = _dungeon(rs); pc = _rogue(rs); eng = _eng(rs, s, pc)
    assert eng._scene_action("go to the courtyard") is True and s.pc_zone == "court"
    assert eng._scene_action("search") is True and s.feature("trap").hidden is False
    assert eng._scene_action("go to the hall") is True and s.pc_zone == "hall"
    assert eng._scene_action("open the iron door") is True and s.feature("door").locked is False
    assert eng._scene_action("go to the crypt") is True and s.pc_zone == "crypt"
    assert eng._scene_action("I shout a warning to my friend") is False


def test_loot_is_granted_through_the_ruleset():
    rs = DnDRuleset(); rs.dice = ScriptedDice(default=18)
    s = _dungeon(rs); pc = _rogue(rs); eng = _eng(rs, s, pc)
    s.pc_zone = "hall"
    for k in ("c1", "c2"):
        del s.presences[k]
    eng._scene_action("take the altar")
    assert "scroll_of_revivify" in pc.sheet["inventory"]


def test_scene_brief_reaches_the_narrator_prompt():
    rs = DnDRuleset(); s = _dungeon(rs); pc = _rogue(rs); eng = _eng(rs, s, pc)
    s.pc_zone = "hall"
    eng._scene_action("look around")
    prompt = eng.client.calls[-1].prompt
    assert "Scene (these facts are true" in prompt
    assert "Great Hall" in prompt and "a cultist" in prompt


def test_failed_steal_raises_the_alarm():
    rs = DnDRuleset(); rs.dice = ScriptedDice(default=1)
    s = _dungeon(rs); pc = _rogue(rs); eng = _eng(rs, s, pc)
    s.pc_zone = "hall"
    eng._scene_action("steal the altar")
    assert s.alertness() != "unaware"
    assert "scroll_of_revivify" not in pc.sheet["inventory"]


def test_engine_combat_handoff_uses_scene_enemies(monkeypatch):
    rs = DnDRuleset(); s = _dungeon(rs); pc = _rogue(rs)
    s.pc_zone = "hall"
    captured = {}

    class _StubController:
        def __init__(self, client, presenter, state, ruleset, *, enemies, companions=(),
                     arena=None, builder=None, rng=None, surprise=None, story=None,
                     narrator_override=None):
            captured["enemies"] = [e.name for e in enemies]
            captured["arena_zones"] = set(arena.zones) if arena else set()
            captured["pc_zone"] = arena.placements[state.pc.name] if arena else None
            for e in enemies:
                if "Cultist" in e.name:
                    e.sheet["hp"] = 0

        def run(self):
            return "party"

    monkeypatch.setattr(combat_mod, "CombatController", _StubController)
    eng = _eng(rs, s, pc)
    eng._start_combat("I attack the cultists")
    assert "Cultist A" in captured["enemies"] and "Cultist B" in captured["enemies"]
    assert captured["arena_zones"] == {"gate", "court", "hall", "crypt"}
    assert captured["pc_zone"] == "hall"
    assert "present_enemies" not in eng.state.flags and "combat_arena" not in eng.state.flags
    assert "c1" not in s.presences and "c2" not in s.presences
    assert "boss" in s.presences


def test_authored_barrow_builds_with_real_enemies():
    rs = DnDRuleset()
    assert "watchers_barrow" in rs.list_scenes()
    s = rs.build_scene("watchers_barrow")
    assert s is not None and set(s.zones) == {"entrance", "antechamber", "gallery", "deep_chamber"}
    foes = [p for p in s.presences.values() if p.kind == "enemy"]
    assert len(foes) >= 3 and all(isinstance(p.combatant, Combatant) for p in foes)
    boss = s.presence("leader")
    assert boss.hidden is True
    s.reveal_enemies()
    assert boss.hidden is False
    s.pc_zone = "gallery"
    s.unlock("sealed_door")
    handoff = s.to_combat(rs.make_pc("Tester"))
    assert all(isinstance(e, Combatant) for e in handoff["enemies"])
    assert "deep_chamber" in handoff["arena"].zones


def test_unknown_scene_key_returns_none():
    assert DnDRuleset().build_scene("no_such_place") is None


class _MP:
    def __init__(self): self._undo = []
    def setattr(self, obj, name, val):
        self._undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, val)
    def undo(self):
        for obj, name, val in reversed(self._undo):
            setattr(obj, name, val)


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    import inspect
    failed = 0
    for t in ALL:
        mp = _MP()
        try:
            if "monkeypatch" in inspect.signature(t).parameters:
                t(mp)
            else:
                t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {t.__name__}: {e}")
        except Exception as e:
            failed += 1
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}")
        finally:
            mp.undo()
    print(f"\n{len(ALL) - failed}/{len(ALL)} passed")
    raise SystemExit(1 if failed else 0)
