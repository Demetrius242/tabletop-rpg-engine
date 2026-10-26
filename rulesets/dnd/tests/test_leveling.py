import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from rulesets.dnd.additional import leveling
from rulesets.dnd.core.dnd import DnDRuleset


def test_proficiency_bonus_by_level():
    assert [leveling.proficiency_bonus(l) for l in (1, 4, 5, 9, 13, 17, 20)] == [2, 2, 3, 4, 5, 6, 6]


def test_hp_uses_fixed_average():
    assert leveling.max_hp(6, 1, 0) == 6
    assert leveling.max_hp(6, 5, 0) == 22
    assert leveling.max_hp(6, 20, 0) == 82
    assert leveling.max_hp(10, 1, 2) == 12
    assert leveling.max_hp(10, 5, 2) == 44


def test_caster_type_mapping():
    assert leveling.caster_type(("full", "cha")) == "full"
    assert leveling.caster_type(("prepared", "wis")) == "full"
    assert leveling.caster_type(("half", "wis")) == "half"
    assert leveling.caster_type(("pact", "cha")) == "pact"
    assert leveling.caster_type(None) is None


def test_full_caster_slots():
    assert leveling.spell_slots("full", 1) == {"level_1": 2}
    assert leveling.spell_slots("full", 5) == {"level_1": 4, "level_2": 3, "level_3": 2}
    s20 = leveling.spell_slots("full", 20)
    assert s20["level_1"] == 4 and s20["level_9"] == 1 and s20["level_6"] == 2


def test_half_caster_slots_start_at_level_two():
    assert leveling.spell_slots("half", 1) == {}
    assert leveling.spell_slots("half", 2) == {"level_1": 2}
    assert leveling.spell_slots("half", 5) == {"level_1": 4, "level_2": 2}


def test_warlock_pact_slots():
    assert leveling.spell_slots("pact", 1) == {"pact_slots": 1, "pact_slot_level": 1}
    assert leveling.spell_slots("pact", 5) == {"pact_slots": 2, "pact_slot_level": 3}
    assert leveling.spell_slots("pact", 11) == {"pact_slots": 3, "pact_slot_level": 5}
    assert leveling.spell_slots("pact", 20) == {"pact_slots": 4, "pact_slot_level": 5}


def test_cumulative_features_grow():
    l1 = leveling.cumulative_features("barbarian", 1)
    l5 = leveling.cumulative_features("barbarian", 5)
    assert any(n == "Rage" for n, _ in l1)
    assert len(l5) > len(l1)
    assert any(n == "Extra Attack" for n, _ in l5)


def test_asi_counts_including_fighter_and_rogue_extras():
    assert leveling.asi_count("wizard", 20) == 5
    assert leveling.asi_count("fighter", 6) == 2
    assert leveling.asi_count("fighter", 20) == 7
    assert leveling.asi_count("rogue", 10) == 3


def test_class_resources_scale():
    ab = {"str": 16, "dex": 16, "con": 14, "cha": 16, "wis": 14, "int": 12}
    assert leveling.class_resources("barbarian", 1, ab)["rages"] == 2
    assert leveling.class_resources("barbarian", 20, ab)["rages"] == "unlimited"
    assert leveling.class_resources("monk", 5, ab)["ki_points"] == 5
    assert leveling.class_resources("monk", 11, ab)["martial_arts_die"] == "1d8"
    assert leveling.class_resources("rogue", 9, ab)["sneak_attack"] == "5d6"
    assert leveling.class_resources("rogue", 20, ab)["sneak_attack"] == "10d6"
    assert leveling.class_resources("fighter", 20, ab)["attacks_per_action"] == 4
    assert leveling.class_resources("paladin", 7, ab)["lay_on_hands_pool"] == 35
    assert leveling.class_resources("warlock", 17, ab)["eldritch_blast_beams"] == 4


def test_progression_covers_all_twenty_levels():
    rows = leveling.progression("fighter", 10, None)
    assert len(rows) == 20 and rows[0]["level"] == 1 and rows[-1]["level"] == 20


def _fighter(rs):
    return rs.build_pc({"name": "Roon", "race": "human", "class": "fighter",
                        "background": "soldier", "alignment": "ln",
                        "abilities": {"str": 15, "con": 14, "dex": 13, "int": 12, "wis": 10, "cha": 8},
                        "skills": ["athletics", "perception"]})


def test_advance_to_level_updates_sheet():
    rs = DnDRuleset()
    pc = _fighter(rs)
    rs.advance_to_level(pc, 5)
    assert pc.sheet["level"] == 5 and pc.sheet["proficiency_bonus"] == 3
    assert pc.sheet["attacks_per_action"] == 2
    assert pc.sheet["attacks"][0]["bonus"] == 6
    rs.advance_to_level(pc, 20)
    assert pc.sheet["proficiency_bonus"] == 6 and pc.sheet["attacks_per_action"] == 4
    assert pc.sheet["asi_pending"] == 7
    assert pc.sheet["max_hp"] > 100


def test_level_up_increments_and_scales_spell_dc():
    rs = DnDRuleset()
    wiz = rs.build_pc({"name": "Veya", "race": "human", "class": "wizard",
                       "background": "sage", "alignment": "tn",
                       "abilities": {"int": 16, "con": 14, "dex": 13, "wis": 12, "cha": 10, "str": 8},
                       "skills": ["arcana", "investigation"]})
    dc1 = wiz.sheet["spellcasting"]["spell_save_dc"]
    assert dc1 == 13 and wiz.sheet["level"] == 1
    rs.advance_to_level(wiz, 5)
    assert wiz.sheet["spellcasting"]["spell_save_dc"] == 14
    assert wiz.sheet["spell_slots"]["level_3"] == 2
    rs.level_up(wiz)
    assert wiz.sheet["level"] == 6


def _mk(rs, cls, skills=("athletics", "perception")):
    return rs.build_pc({"name": "Lvl", "race": "human", "class": cls, "background": "soldier",
                        "alignment": "ng", "skills": list(skills),
                        "abilities": {"str": 15, "dex": 13, "con": 14, "int": 12, "wis": 12, "cha": 14}})


def test_subclasses_exist_for_every_class():
    from rulesets.dnd.additional import subclasses as SC
    rs = DnDRuleset()
    for ck in rs.classes:
        assert SC.has_subclasses(ck), f"{ck} should have subclasses"
        assert 1 <= SC.subclass_level(ck) <= 3


def test_level_up_is_staged_and_applies_only_on_long_rest():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    assert f.sheet["level"] == 1
    rs.award_level_up(f)
    assert rs.level_up_state(f)["available"] and rs.level_up_state(f)["target_level"] == 2
    assert f.sheet["level"] == 1
    rs.long_rest(f)
    assert f.sheet["level"] == 2 and not rs.level_up_state(f)["available"]


def test_subclass_choice_offered_and_folds_features_in():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    rs.award_level_up(f); rs.long_rest(f)
    rs.award_level_up(f)
    slots = [s["key"] for s in rs.level_up_state(f)["slots"]]
    assert "subclass" in slots
    rs.set_level_choice(f, "subclass", "champion")
    assert rs.level_up_state(f)["ready"]
    rs.set_level_choice(f, "subclass", "battle_master")
    assert rs.level_up_state(f)["choices"]["subclass"] == "battle_master"
    rs.long_rest(f)
    assert f.sheet["subclass"] == "battle_master"
    assert "Combat Superiority" in f.sheet["class_features"]


def test_asi_raises_ability_on_apply():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    for _ in range(2):
        rs.award_level_up(f); rs.long_rest(f)
    rs.award_level_up(f)
    assert "asi" in [s["key"] for s in rs.level_up_state(f)["slots"]]
    before = f.sheet["abilities"]["dex"]
    rs.set_level_choice(f, "asi", "dex"); rs.long_rest(f)
    assert f.sheet["abilities"]["dex"] == before + 2 and f.sheet["level"] == 4


def test_cancel_level_up_discards_it():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    rs.award_level_up(f)
    assert rs.cancel_level_up(f) and not rs.level_up_state(f)["available"]
    rs.long_rest(f)
    assert f.sheet["level"] == 1


def test_known_caster_learns_spell_choice():
    rs = DnDRuleset(); s = _mk(rs, "sorcerer", skills=("arcana", "deception"))
    rs.award_level_up(s)
    sp = [x for x in rs.level_up_state(s)["slots"] if x["key"] == "spells"]
    assert sp and sp[0]["choose"] >= 1 and sp[0]["options"]


def test_multiclass_hp_sums_per_class_hit_dice():
    classes = [{"class_key": "fighter", "level": 1, "hit_die": 10},
               {"class_key": "wizard", "level": 1, "hit_die": 6}]
    assert leveling.multiclass_max_hp(classes, 2) == 18


def test_multiclass_spell_slots_full_plus_full():
    classes = [{"class_key": "cleric", "level": 1}, {"class_key": "wizard", "level": 1}]
    assert leveling.multiclass_caster_level(classes) == 2
    assert leveling.multiclass_spell_slots(classes) == {"level_1": 3}


def test_multiclass_spell_slots_half_caster_rounds_down():
    classes = [{"class_key": "paladin", "level": 2}, {"class_key": "sorcerer", "level": 1}]
    assert leveling.multiclass_caster_level(classes) == 2
    assert leveling.multiclass_spell_slots(classes) == {"level_1": 3}


def test_single_half_caster_uses_native_table():
    assert leveling.multiclass_spell_slots([{"class_key": "paladin", "level": 2}]) == {"level_1": 2}


def test_warlock_pact_stays_separate():
    classes = [{"class_key": "warlock", "level": 2}, {"class_key": "sorcerer", "level": 1}]
    slots = leveling.multiclass_spell_slots(classes)
    pact = leveling.pact_slots_for(classes)
    assert slots == {"level_1": 2} and "pact_slots" not in slots
    assert pact == {"pact_slots": 2, "pact_slot_level": 1}


def test_extra_attack_does_not_stack():
    ab = {"str": 16, "dex": 14, "con": 14, "int": 10, "wis": 12, "cha": 10}
    merged = leveling.merge_class_resources(
        [{"class_key": "fighter", "level": 5}, {"class_key": "ranger", "level": 5}], ab)
    assert merged["attacks_per_action"] == 2


def test_total_level_capped_at_twenty():
    assert leveling.total_level([{"level": 15}, {"level": 10}]) == 20


def test_per_class_subclass_retained_on_recompute():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    f.sheet["classes"] = [
        {"class_key": "fighter", "level": 3, "subclass": "champion",
         "subclass_label": "Champion", "hit_die": 10},
        {"class_key": "rogue", "level": 3, "subclass": "thief",
         "subclass_label": "Thief", "hit_die": 8}]
    rs._recompute_sheet(f)
    assert f.sheet["level"] == 6
    assert "Improved Critical" in f.sheet["class_features"]
    assert "Fast Hands" in f.sheet["class_features"]


def test_legacy_single_class_save_loads():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    rs.award_level_up(f); rs.long_rest(f)
    del f.sheet["classes"]
    f.sheet["subclass"] = ""
    st = rs.level_up_state(f)
    assert st["level"] == 2 and st["classes"][0]["class_key"] == "fighter"
    rs.award_level_up(f); rs.long_rest(f)
    assert f.sheet["level"] == 3 and len(f.sheet["classes"]) == 1


def test_add_new_class_via_levelup():
    rs = DnDRuleset(); f = _mk(rs, "fighter")
    rs.award_level_up(f)
    opts = [o["id"] for s in rs.level_up_state(f)["slots"] if s["key"] == "class" for o in s["options"]]
    assert "new:wizard" in opts
    rs.set_level_choice(f, "class", "new:wizard")
    rs.long_rest(f)
    keys = [(c["class_key"], c["level"]) for c in f.sheet["classes"]]
    assert ("fighter", 1) in keys and ("wizard", 1) in keys
    assert f.sheet["level"] == 2
    assert f.sheet["spell_slots"].get("level_1") == 2


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
