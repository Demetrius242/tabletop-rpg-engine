import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.core.dnd import DnDRuleset


def _pc(rs, cls, level=1, **abilities):
    base = {"str": 10, "dex": 10, "con": 14, "int": 10, "wis": 10, "cha": 10}
    base.update(abilities)
    pc = rs.build_pc({"name": "T", "race": "human", "class": cls, "background": "sage",
                      "alignment": "tn", "abilities": base, "skills": []})
    if level > 1:
        rs.advance_to_level(pc, level)
    return pc


def test_build_initializes_remaining_pools():
    rs = DnDRuleset()
    wiz = _pc(rs, "wizard", int=16)
    assert wiz.sheet["spell_slots_remaining"] == wiz.sheet["spell_slots"]
    assert "gold" in wiz.sheet and isinstance(wiz.sheet["inventory"], list)


def test_casting_spends_lowest_sufficient_slot():
    rs = DnDRuleset()
    wiz = _pc(rs, "wizard", 5, int=16)
    r = rs.cast_spell(wiz, "fireball")
    assert r["cast"] and r["slot_used"] == 3
    assert wiz.sheet["spell_slots_remaining"]["level_3"] == 1
    rs.cast_spell(wiz, "magic_missile")
    assert wiz.sheet["spell_slots_remaining"]["level_1"] == 3


def test_cantrips_are_free():
    rs = DnDRuleset()
    wiz = _pc(rs, "wizard", int=16)
    before = dict(wiz.sheet["spell_slots_remaining"])
    r = rs.cast_spell(wiz, "fire_bolt")
    assert r["cast"] and r["slot_used"] == 0 and wiz.sheet["spell_slots_remaining"] == before


def test_upcasting_when_low_level_slots_are_gone():
    rs = DnDRuleset()
    wiz = _pc(rs, "wizard", 5, int=16)
    for _ in range(4):
        rs.cast_spell(wiz, level=1)
    r = rs.cast_spell(wiz, level=1)
    assert r["cast"] and r["slot_used"] == 2


def test_running_out_of_slots_fails():
    rs = DnDRuleset()
    wiz = _pc(rs, "wizard", int=16)
    casts = [rs.cast_spell(wiz, level=1)["cast"] for _ in range(6)]
    assert casts[0] is True and casts[-1] is False


def test_warlock_pact_slots_and_short_rest():
    rs = DnDRuleset()
    war = _pc(rs, "warlock", 5, cha=16)
    assert war.sheet["spell_slots_remaining"].get("pact_slots") == 2
    assert rs.cast_spell(war, "hex")["cast"] and rs.cast_spell(war, "hex")["cast"]
    assert rs.cast_spell(war, "hex")["cast"] is False
    rs.short_rest(war)
    assert war.sheet["spell_slots_remaining"]["pact_slots"] == 2


def test_resource_pools_spend_and_long_rest_refills():
    rs = DnDRuleset()
    barb = _pc(rs, "barbarian", str=16)
    assert rs.resource_remaining(barb, "rages") == 2
    assert rs.spend_resource(barb, "rages") and rs.spend_resource(barb, "rages")
    assert rs.resource_remaining(barb, "rages") == 0
    assert rs.spend_resource(barb, "rages") is False
    rs.long_rest(barb)
    assert rs.resource_remaining(barb, "rages") == 2


def test_short_rest_refreshes_only_short_rest_pools():
    rs = DnDRuleset()
    monk = _pc(rs, "monk", 5, dex=16, wis=14)
    assert rs.resource_remaining(monk, "ki_points") == 5
    for _ in range(4):
        rs.spend_resource(monk, "ki_points")
    assert rs.resource_remaining(monk, "ki_points") == 1
    rs.short_rest(monk)
    assert rs.resource_remaining(monk, "ki_points") == 5


def test_lay_on_hands_spends_variable_amounts():
    rs = DnDRuleset()
    pal = _pc(rs, "paladin", 5, cha=14, str=15)
    pool = rs.resource_remaining(pal, "lay_on_hands_pool")
    assert isinstance(pool, int) and pool >= 5
    assert rs.spend_resource(pal, "lay_on_hands_pool", 5)
    assert rs.resource_remaining(pal, "lay_on_hands_pool") == pool - 5
    assert rs.spend_resource(pal, "lay_on_hands_pool", pool) is False


def test_level_up_refreshes_to_new_maxima():
    rs = DnDRuleset()
    wiz = _pc(rs, "wizard", int=16)
    rs.cast_spell(wiz, level=1)
    rs.advance_to_level(wiz, 3)
    assert wiz.sheet["spell_slots_remaining"] == wiz.sheet["spell_slots"]


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
