import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.engine import NARRATOR_SYSTEM, ExplorationEngine
from engine.llm import FakeLLMClient
from engine.ruleset import Ruleset
from engine.state import Combatant, GameState
from rulesets.dnd.core.dnd import DnDRuleset


class _Pres:
    def __init__(self, inputs=()):
        self._i = list(inputs)
        self.events = []

    def emit(self, e):
        self.events.append(e)

    def read_action(self):
        if not self._i:
            raise EOFError
        return self._i.pop(0)


def _warlock(rs):
    return rs.build_pc({"name": "Mara", "race": "tiefling", "class": "warlock",
                        "background": "charlatan", "alignment": "cn",
                        "abilities": {"cha": 15, "con": 14, "dex": 13, "int": 10, "wis": 12, "str": 8},
                        "skills": ["deception", "arcana"]})


def test_briefing_contains_identity_alignment_and_seed():
    rs = DnDRuleset()
    brief = rs.narrator_briefing(_warlock(rs))
    assert "You are Mara" in brief and "Tiefling Warlock" in brief
    assert "Charlatan background" in brief
    assert "Chaotic Neutral" in brief
    assert "False Identity" in brief
    assert "Personality:" in brief and "Ideal:" in brief
    assert "Bond:" in brief and "Flaw:" in brief


def test_briefing_is_second_person_and_clean():
    rs = DnDRuleset()
    brief = rs.narrator_briefing(_warlock(rs))
    assert "You are" in brief and " he " not in brief and " she " not in brief
    assert ".." not in brief


def test_briefing_omits_alignment_when_absent():
    rs = DnDRuleset()
    rs.setting = None
    bare = Combatant(name="Nobody", is_pc=True, sheet={})
    assert rs.narrator_briefing(bare) == ""


def test_world_brief_is_present_with_an_active_setting():
    rs = DnDRuleset()
    bare = Combatant(name="Nobody", is_pc=True, sheet={})
    brief = rs.narrator_briefing(bare)
    assert "World briefing" in brief and "Forgotten Realms" in brief
    assert "Character briefing" not in brief


def test_exploration_narrator_prompt_includes_briefing():
    rs = DnDRuleset()
    client = FakeLLMClient(default_text="The hall is still.")
    state = GameState(pc=_warlock(rs), location="a torchlit hall")
    ExplorationEngine(client=client, presenter=_Pres([]), state=state, ruleset=rs).run()
    prompt = client.calls[0].prompt
    assert "Character briefing" in prompt and "You are Mara" in prompt
    assert NARRATOR_SYSTEM.split("\n")[0] in prompt


class _NoBriefRuleset(Ruleset):
    def resolve_check(self, *a, **k): raise NotImplementedError
    def modifier_for(self, *a, **k): return 0
    def skill_names(self): return []
    def skill_tags(self, skill): return set()
    def situational_difficulty_delta(self, *a, **k): return 0
    def difficulty_for_band(self, band): raise NotImplementedError
    def health_descriptor(self, actor): return "unhurt"
    def apply_damage(self, actor, amount, dtype=None): pass
    def is_defeated(self, actor): return False
    def health_fraction(self, actor): return 1.0
    def turn_model(self): raise NotImplementedError
    def make_pc(self, name): return Combatant(name=name, is_pc=True, sheet={})
    def try_special_action(self, pc, text): return None
    def morality(self): return None


def test_default_ruleset_leaves_prompt_unbriefed():
    rs = _NoBriefRuleset()
    client = FakeLLMClient(default_text="...")
    state = GameState(pc=rs.make_pc("Solo"), location="a void")
    ExplorationEngine(client=client, presenter=_Pres([]), state=state, ruleset=rs).run()
    prompt = client.calls[0].prompt
    assert "Character briefing" not in prompt


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
