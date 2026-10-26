import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.engine import ExplorationEngine
from engine.llm import FakeLLMClient
from engine.state import GameState
from rulesets.dnd.core.dnd import DnDRuleset
from rulesets.dnd.settings import FORGOTTEN_REALMS, SETTINGS, get


class _Pres:
    def __init__(self, inputs=()):
        self._i = list(inputs); self.events = []
    def emit(self, e): self.events.append(e)
    def read_action(self):
        if not self._i: raise EOFError
        return self._i.pop(0)


def test_forgotten_realms_is_well_formed():
    fr = FORGOTTEN_REALMS
    assert fr.key == "forgotten_realms" and fr.tone
    assert len(fr.concepts) >= 4 and len(fr.sights) >= 4
    assert len(fr.locations) >= 5 and len(fr.npcs) >= 4
    assert get("forgotten_realms") is fr and "forgotten_realms" in SETTINGS


def test_locations_have_the_requested_kinds():
    fr = FORGOTTEN_REALMS
    kinds = {loc.kind for loc in fr.locations.values()}
    for needed in ("street", "forest", "tower"):
        assert needed in kinds
    tower = fr.location("lonely_tower")
    assert tower.name and tower.mood and tower.description and tower.hooks


def test_npc_cards_carry_voice_and_hook():
    for key in FORGOTTEN_REALMS.list_npcs():
        npc = FORGOTTEN_REALMS.npc(key)
        assert npc.name and npc.role and npc.description
        assert npc.demeanor and npc.voice and npc.hook


def test_narration_brief_conveys_tone_and_concepts():
    brief = FORGOTTEN_REALMS.narration_brief()
    assert "World briefing" in brief
    assert "Forgotten Realms" in brief and "frontier" in brief
    assert "The Weave" in brief or "Mystra" in brief


def test_ruleset_has_an_active_setting_by_default():
    rs = DnDRuleset()
    assert rs.list_settings() == ["forgotten_realms"]
    assert rs.current_setting().key == "forgotten_realms"
    assert rs.location("waterdeep_night_street").kind == "street"
    assert rs.npc("maela_brightwater").role == "innkeeper"


def test_use_setting_switches_and_can_clear():
    rs = DnDRuleset()
    assert rs.use_setting("forgotten_realms") is True
    assert rs.use_setting("nonexistent") is False
    assert rs.current_setting().key == "forgotten_realms"
    rs.setting = None
    assert rs.world_brief() == "" and rs.location("lonely_tower") is None


def test_world_brief_reaches_the_narrator_prompt():
    rs = DnDRuleset()
    pc = rs.build_pc({"name": "Brae", "race": "human", "class": "fighter", "background": "soldier",
                      "alignment": "ng",
                      "abilities": {"str": 15, "con": 14, "dex": 13, "int": 12, "wis": 10, "cha": 8},
                      "skills": ["athletics", "perception"]})
    client = FakeLLMClient(default_text="The street is quiet.")
    state = GameState(pc=pc, location="a Waterdhavian street")
    ExplorationEngine(client=client, presenter=_Pres([]), state=state, ruleset=rs).run()
    prompt = client.calls[0].prompt
    assert "World briefing" in prompt and "Forgotten Realms" in prompt
    assert "Character briefing" in prompt and "You are Brae" in prompt


def test_npcs_have_full_sheets_and_detailed_dialogue():
    from rulesets.dnd.settings.forgotten_realms import npcs as N
    rs = DnDRuleset(); rs.use_setting("forgotten_realms")
    assert N.npc_keys(), "the setting should ship NPCs"
    for key in N.npc_keys():
        card = N.npc_card(key)
        assert len(card.dialogue_examples) >= 3, f"{key} needs detailed dialogue"
        assert card.mannerisms.strip()
        sheet = N.npc_sheet(key)
        for field in ("abilities", "hp", "ac", "attacks"):
            assert field in sheet, f"{key} sheet missing {field}"
        assert set(("str", "dex", "con", "int", "wis", "cha")) <= set(sheet["abilities"])
    built = rs.build_npc("sergeant_dornan")
    assert built is not None and built.sheet.get("card") is not None


def test_underdark_oota_content_in_forgotten_realms():
    from rulesets.dnd.additional import items
    fr = FORGOTTEN_REALMS
    assert fr.location("velkynvelve_chasm").adventure == "out_of_the_abyss"
    assert len(fr.list_locations("out_of_the_abyss")) >= 8
    rs = DnDRuleset()
    assert rs.use_setting("forgotten_realms") is True
    assert rs.npc("ilvara_mizzrym").role == "drow priestess of Lolth"
    assert rs.npc("ilvara_mizzrym").adventure == "out_of_the_abyss"
    assert "velkynvelve" in rs.list_scenes()
    built = rs.build_npc("jorlan_duskryn")
    assert built is not None and built.sheet["hp"] == 71
    assert "out_of_the_abyss" in built.sheet.get("tags", [])
    assert any(it.key == "fang_of_lolth" for it in items.in_region("out_of_the_abyss"))
    brief = fr.narration_brief()
    assert "Underdark" in brief or "faerzress" in brief.lower()


def test_traders_have_full_sheets_and_detailed_dialogue():
    from rulesets.dnd.settings.forgotten_realms.tradesmen import TRADESMEN
    rs = DnDRuleset(); rs.use_setting("forgotten_realms")
    for key, t in TRADESMEN.items():
        assert t.sheet is not None, f"trader {key} needs a stat block"
        assert "hp" in t.sheet and "abilities" in t.sheet
        assert len(t.card.dialogue_examples) >= 3, f"trader {key} needs detailed dialogue"
    spawned = rs.build_trader("xanthros")
    assert spawned is not None and spawned.sheet.get("card") is not None


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
