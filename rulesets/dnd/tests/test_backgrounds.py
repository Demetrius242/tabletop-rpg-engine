import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.additional import backgrounds
from rulesets.dnd.core.dnd import DnDRuleset


def test_every_background_is_well_formed():
    assert len(backgrounds.BACKGROUNDS) >= 12
    for key in backgrounds.ORDER:
        bg = backgrounds.get(key)
        assert len(bg.skills) == 2, f"{key} should grant exactly two skills"
        assert bg.feature[0] and bg.feature[1], f"{key} needs a named feature"
        assert bg.traits and bg.ideals and bg.bonds and bg.flaws


def test_acolyte_grants_expected_content():
    a = backgrounds.get("acolyte")
    assert a.skills == ("insight", "religion")
    assert a.languages == 2
    assert a.feature[0] == "Shelter of the Faithful"


def test_roleplay_seed_bundles_all_narrative_tables():
    seed = backgrounds.roleplay_seed(backgrounds.get("criminal"))
    assert seed["background"] == "Criminal"
    assert seed["feature"]["name"] == "Criminal Contact"
    for k in ("suggested_traits", "suggested_ideals", "suggested_bonds", "suggested_flaws"):
        assert seed[k], f"{k} should be non-empty"


def test_ruleset_lists_backgrounds_and_creation_includes_step():
    rs = DnDRuleset()
    assert "acolyte" in rs.list_backgrounds() and "soldier" in rs.list_backgrounds()
    steps = {s.key: s for s in rs.creation_spec()}
    assert "background" in steps and steps["background"].kind == "choose_one"
    labels = {o.key for o in steps["background"].options}
    assert labels == set(rs.list_backgrounds())


def test_background_skills_merge_into_sheet_and_dedupe():
    rs = DnDRuleset()
    pc = rs.build_pc({"name": "Cass", "race": "human", "class": "fighter",
                      "background": "soldier", "alignment": "ln",
                      "abilities": {"str": 15, "con": 14, "dex": 13, "int": 12, "wis": 10, "cha": 8},
                      "skills": ["athletics", "perception"]})
    profs = pc.sheet["proficiencies"]
    assert profs.count("athletics") == 1
    assert "perception" in profs and "intimidation" in profs
    assert pc.sheet["background"] == "Soldier"
    assert pc.sheet["background_feature"]["name"] == "Military Rank"
    assert pc.sheet["roleplay"]["suggested_bonds"]


def test_tool_and_language_grants_recorded():
    rs = DnDRuleset()
    pc = rs.build_pc({"name": "Finn", "race": "human", "class": "rogue",
                      "background": "criminal", "alignment": "cn",
                      "abilities": {"dex": 15, "con": 14, "int": 13, "wis": 12, "cha": 10, "str": 8},
                      "skills": ["acrobatics", "perception", "investigation", "persuasion"]})
    assert "thieves' tools" in pc.sheet["tool_proficiencies"]
    assert pc.sheet["background_languages"] == 0


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
