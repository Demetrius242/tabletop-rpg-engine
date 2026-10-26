import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.additional import alignment
from rulesets.dnd.core.dnd import DnDRuleset


def test_detect_evil_and_good_keys_off_six_types():
    for t in ("aberration", "celestial", "elemental", "fey", "fiend", "undead"):
        assert alignment.detect_evil_and_good(t) == t
    for t in ("humanoid", "beast", "dragon", "construct", "giant"):
        assert alignment.detect_evil_and_good(t) is None


def test_protection_disadvantage():
    assert alignment.protection_disadvantage("fiend") is True
    assert alignment.protection_disadvantage("undead") is True
    assert alignment.protection_disadvantage("humanoid") is False


def test_magic_circle_blocks_only_configured_type():
    assert alignment.magic_circle_blocks("fiend", "fiend") is True
    assert alignment.magic_circle_blocks("fiend", "celestial") is False
    assert alignment.magic_circle_blocks("humanoid", "humanoid") is False


def test_good_item_allows_good_wielder_and_blocks_others():
    good = alignment.item_attunement("lg", "holy_avenger")
    assert good["allowed"] is True and "good hands" in good["effect"].lower()
    evil = alignment.item_attunement("ne", "holy_avenger")
    assert evil["allowed"] is False and "non-good" in evil["effect"].lower()
    neutral = alignment.item_attunement("tn", "holy_avenger")
    assert neutral["allowed"] is False


def test_evil_item_requires_evil():
    assert alignment.item_attunement("ce", "talisman_of_ultimate_evil")["allowed"] is True
    assert alignment.item_attunement("lg", "talisman_of_ultimate_evil")["allowed"] is False


def test_two_axis_requirement_is_respected_via_books():
    assert alignment.item_attunement("cg", "book_of_exalted_deeds")["allowed"] is True
    assert alignment.item_attunement("ln", "book_of_exalted_deeds")["allowed"] is False


def test_sentient_conflict_on_opposed_axes():
    assert alignment.sentient_item_conflict("lg", "ce")["conflict"] is True
    assert alignment.sentient_item_conflict("lg", "cg")["conflict"] is True
    assert alignment.sentient_item_conflict("lg", "ng")["conflict"] is False
    assert alignment.sentient_item_conflict("tn", "tn")["conflict"] is False


def test_ruleset_reads_creature_type_for_spells():
    rs = DnDRuleset()
    ghoul = rs.make_enemy("Ghoul", creature_type="undead", alignment="ce")
    guard = rs.make_enemy("Guard", creature_type="humanoid", alignment="ln")
    assert rs.detect_evil_and_good(ghoul) == "undead"
    assert rs.detect_evil_and_good(guard) is None
    assert rs.protection_from_evil_and_good(ghoul) is True
    assert rs.protection_from_evil_and_good(guard) is False
    assert rs.magic_circle_blocks("undead", ghoul) is True


def test_ruleset_item_attunement_uses_character_alignment():
    rs = DnDRuleset()
    paladin = rs.build_pc({"name": "Sir Kay", "race": "human", "class": "paladin",
                           "background": "noble", "alignment": "lg",
                           "abilities": {"str": 15, "cha": 14, "con": 13, "dex": 12, "wis": 10, "int": 8},
                           "skills": []})
    assert rs.attune_item(paladin, "holy_avenger")["allowed"] is True
    assert rs.sentient_item_conflict(paladin, "ce")["conflict"] is True


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
