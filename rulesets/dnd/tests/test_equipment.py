import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.core.dnd import DnDRuleset
from rulesets.dnd.additional import equipment as EQ


def _pc(cls, **abil):
    rs = DnDRuleset()
    ab = {"str": 15, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10}
    ab.update(abil)
    pc = rs.build_pc({"name": "T", "race": "human", "class": cls, "background": "soldier",
                      "alignment": "ln", "abilities": ab})
    for k in ("longsword", "greataxe", "shield", "chain_mail", "leather_armor", "dagger"):
        if k not in pc.sheet["inventory"]:
            pc.sheet["inventory"].append(k)
    return rs, pc


def test_slots_and_groups_present():
    assert EQ.SLOTS[:3] == ["main_hand", "off_hand", "armor"]
    assert EQ.SLOT_GROUP["amulet"] == "jewelry" and EQ.SLOT_GROUP["main_hand"] == "weapon"
    assert len(EQ.SLOTS) == 10


def test_class_armor_proficiency_gates_equip():
    rs, fighter = _pc("fighter")
    assert rs.equip_item(fighter, "chain_mail", "armor")["ok"]
    rs, wizard = _pc("wizard")
    assert not rs.equip_item(wizard, "chain_mail", "armor")["ok"]
    assert not rs.equip_item(wizard, "longsword", "main_hand")["ok"]
    assert rs.equip_item(wizard, "dagger", "main_hand")["ok"]


def test_ac_recomputes_from_armor_and_shield():
    rs, f = _pc("fighter")
    rs.equip_item(f, "leather_armor", "armor")
    assert f.sheet["ac"] == 12
    rs.equip_item(f, "shield", "off_hand")
    assert f.sheet["ac"] == 14
    rs.unequip_item(f, "armor")
    rs.equip_item(f, "chain_mail", "armor")
    assert f.sheet["ac"] == 18


def test_two_handed_weapon_locks_off_hand():
    rs, f = _pc("fighter")
    assert rs.equip_item(f, "greataxe", "main_hand")["ok"]
    assert not rs.equip_item(f, "shield", "off_hand")["ok"]
    rs.unequip_item(f, "main_hand")
    assert rs.equip_item(f, "longsword", "main_hand")["ok"]
    assert rs.equip_item(f, "shield", "off_hand")["ok"]


def test_no_equipping_in_combat():
    rs, f = _pc("fighter")
    assert not rs.equip_item(f, "longsword", "main_hand", in_combat=True)["ok"]
    assert rs.equip_item(f, "longsword", "main_hand", in_combat=False)["ok"]


def test_equipped_weapon_sets_the_attack():
    rs, f = _pc("fighter")
    rs.equip_item(f, "longsword", "main_hand")
    atk = f.sheet["attacks"][0]
    assert atk["name"] == "Longsword" and atk["bonus"] == 5
    assert atk["reach"] == "melee"


def test_encumbrance_tracks_weight_and_slows():
    rs, f = _pc("fighter", str=8)
    str_score = f.sheet["abilities"]["str"]
    enc = rs.encumbrance_status(f)
    assert enc["capacity"] == str_score * 15
    f.sheet["inventory"] += ["chain_mail"] * 4
    enc2 = rs.encumbrance_status(f)
    assert enc2["weight"] > enc["weight"]
    assert enc2["status"] == "heavily encumbered" and enc2["speed_penalty"] == -20
    assert rs.effective_speed(f) < f.sheet["speed"]


def test_equipment_view_has_ten_slots_and_encumbrance():
    rs, f = _pc("fighter")
    rs.equip_item(f, "longsword", "main_hand")
    view = rs.equipment_view(f)
    assert len(view["slots"]) == 10
    assert any(s["item"] and s["item"]["name"] == "Longsword" for s in view["slots"])
    assert "status" in view["encumbrance"]


ALL = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
if __name__ == "__main__":
    ok = 0
    for t in ALL:
        try:
            t(); ok += 1
        except Exception as exc:
            print(f"FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{ok}/{len(ALL)} passed")
    sys.exit(0 if ok == len(ALL) else 1)
