import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.additional import spells
from rulesets.dnd.core.dnd import DnDRuleset


def test_every_caster_has_a_list():
    for c in spells.CASTERS:
        assert spells.spells_for_class(c), f"{c} should have spells"


def test_iconic_spells_land_on_the_right_lists():
    fb = spells.get("fireball")
    assert fb.level == 3 and "wizard" in fb.classes and "sorcerer" in fb.classes
    assert "cleric" not in fb.classes
    cw = spells.get("cure_wounds")
    assert "cleric" in cw.classes and "paladin" in cw.classes and "wizard" not in cw.classes
    assert "wizard" in spells.get("counterspell").classes
    assert spells.get("eldritch_blast").classes == ("warlock",)


def test_paladin_and_ranger_have_no_cantrips():
    assert spells.cantrips_for("paladin") == [] and spells.cantrips_for("ranger") == []
    assert max(s.level for s in spells.spells_for_class("paladin")) <= 5
    assert max(s.level for s in spells.spells_for_class("ranger")) <= 5


def test_by_level_groups_and_sorts():
    wiz = spells.by_level("wizard")
    assert 0 in wiz and 9 in wiz
    names_l1 = [s.name for s in wiz[1]]
    assert names_l1 == sorted(names_l1)


def test_known_casters_use_fixed_counts():
    assert spells.spells_known_or_prepared("bard", 1)["method"] == "known"
    assert spells.spells_known_or_prepared("bard", 5)["spells"] == 8
    assert spells.spells_known_or_prepared("sorcerer", 3)["spells"] == 4
    assert spells.spells_known_or_prepared("ranger", 1)["spells"] == 0
    assert spells.spells_known_or_prepared("ranger", 2)["spells"] == 2


def test_prepared_casters_use_ability_plus_level():
    assert spells.spells_known_or_prepared("wizard", 5, 3)["spells"] == 8
    assert spells.spells_known_or_prepared("cleric", 1, 2)["spells"] == 3
    assert spells.spells_known_or_prepared("paladin", 6, 3)["spells"] == 6


def test_cantrips_known_scale():
    assert spells.cantrips_known("wizard", 1) == 3 and spells.cantrips_known("wizard", 10) == 5
    assert spells.cantrips_known("sorcerer", 1) == 4
    assert spells.cantrips_known("fighter", 5) == 0


def test_noncasters_have_no_repertoire():
    out = spells.spells_known_or_prepared("fighter", 10, 2)
    assert out["method"] == "none" and out["spells"] == 0 and out["cantrips"] == 0


def test_sheet_records_repertoire_for_casters():
    rs = DnDRuleset()
    wiz = rs.build_pc({"name": "Vex", "race": "human", "class": "wizard", "background": "sage",
                       "alignment": "tn",
                       "abilities": {"int": 16, "con": 14, "dex": 13, "wis": 12, "cha": 10, "str": 8},
                       "skills": ["arcana", "investigation"]})
    sc = wiz.sheet["spellcasting"]
    assert sc["spells_method"] == "prepared" and sc["spells_count"] == 1 + 3
    assert sc["cantrips_known"] == 3
    rs.advance_to_level(wiz, 9)
    assert wiz.sheet["spellcasting"]["spells_count"] == 9 + 3


def test_ruleset_exposes_class_spell_list():
    rs = DnDRuleset()
    cleric_list = rs.class_spell_list("cleric")
    assert 0 in cleric_list
    names = [n for lvl in cleric_list.values() for (n, _, _) in lvl]
    assert "Cure Wounds" in names and "Spirit Guardians" in names
    assert rs.class_spell_list("barbarian") == {}


def test_available_spells_follows_the_character_class():
    rs = DnDRuleset()
    druid = rs.build_pc({"name": "Thorn", "race": "half_elf", "class": "druid",
                         "background": "hermit", "alignment": "ng",
                         "abilities": {"wis": 15, "con": 14, "dex": 13, "int": 12, "cha": 10, "str": 8},
                         "skills": ["nature", "perception"]})
    avail = rs.available_spells(druid)
    flat = [n for lvl in avail.values() for (n, _, _) in lvl]
    assert "Entangle" in flat and "Call Lightning" in flat


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
