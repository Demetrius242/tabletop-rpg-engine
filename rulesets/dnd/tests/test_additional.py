import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.creation import CharacterCreator
from engine.events import Menu
from rulesets.dnd.additional import alignment, classes, proficiencies, races
from rulesets.dnd.core.dnd import DnDRuleset


class Scripted:
    def __init__(self, inputs):
        self._i = list(inputs)
        self.events = []

    def emit(self, e):
        self.events.append(e)

    def read_action(self):
        if not self._i:
            raise EOFError("creation asked for more input than scripted")
        return self._i.pop(0)

    def menus(self):
        return [e for e in self.events if isinstance(e, Menu)]


def test_nine_alignments_with_correct_axes():
    assert len(alignment.ALIGNMENTS) == 9 and len(alignment.ORDER) == 9
    assert alignment.get("lg").law == "lawful" and alignment.get("lg").morality == "good"
    assert alignment.get("ce").law == "chaotic" and alignment.get("ce").morality == "evil"
    assert alignment.get("tn").law == "neutral" and alignment.get("tn").morality == "neutral"


def test_alignment_true_presented_mask():
    p = alignment.profile("le")
    assert not p.is_masking and p.true.label == "Lawful Evil"
    assert "Lawful Evil" in p.narration_note()
    masked = alignment.profile("ne", "ng")
    assert masked.is_masking
    note = masked.narration_note()
    assert "presents as Neutral Good" in note and "truly Neutral Evil" in note


def test_full_roster_includes_the_requested_races():
    assert set(races.ORDER) == set(races.RACES)
    for key in ("halfling", "tiefling", "human", "elf", "dwarf"):
        assert key in races.RACES


def test_tiefling_traits():
    t = races.get("tiefling")
    assert t.ability_bonuses == {"cha": 2, "int": 1}
    assert "fire" in t.resistances and t.darkvision == 60
    names = [n for n, _ in t.traits]
    assert "Infernal Legacy" in names and "Hellish Resistance" in names


def test_halfling_traits():
    h = races.get("halfling")
    assert h.ability_bonuses == {"dex": 2, "cha": 1} and h.size == "Small"
    names = [n for n, _ in h.traits]
    assert "Lucky" in names and "Brave" in names


def test_some_races_grant_skill_proficiencies():
    assert races.get("elf").skills == ("perception",)
    assert races.get("half_orc").skills == ("intimidation",)


def test_all_twelve_classes_present_and_well_formed():
    assert len(classes.CLASSES) == 12 and len(classes.ORDER) == 12
    for key in classes.ORDER:
        c = classes.get(key)
        assert c.hit_die in (6, 8, 10, 12)
        assert len(c.saving_throws) == 2
        assert c.weapon and len(c.weapon) == 2
        assert len(c.skill_list) >= 2 and c.skill_choices >= 2
        assert c.features, f"{key} should list level-1 features"


def test_spellcasting_types_are_correct():
    assert classes.get("warlock").spellcasting == ("pact", "cha")
    assert classes.get("paladin").spellcasting[0] == "half"
    assert classes.get("ranger").spellcasting[0] == "half"
    assert classes.get("wizard").spellcasting == ("prepared", "int")
    assert classes.get("sorcerer").spellcasting == ("full", "cha")
    for non_caster in ("barbarian", "fighter", "monk", "rogue"):
        assert classes.get(non_caster).spellcasting is None


def test_rogue_picks_four_skills_bard_picks_three():
    assert classes.get("rogue").skill_choices == 4
    assert classes.get("bard").skill_choices == 3
    assert classes.get("bard").skill_list == classes.ALL_SKILLS


def test_proficiency_bonus_and_spell_stats():
    assert proficiencies.proficiency_bonus(1) == 2
    assert proficiencies.proficiency_bonus(5) == 3
    stats = proficiencies.spell_stats(16, level=1)
    assert stats["spell_save_dc"] == 13 and stats["spell_attack_bonus"] == 5


def test_resolve_skill_proficiencies_filters_caps_and_tops_up():
    skill_list = ("stealth", "acrobatics", "perception", "investigation")
    out = proficiencies.resolve_skill_proficiencies(skill_list, 2, ["arcana", "stealth"])
    assert out[0] == "stealth" and len(out) == 2 and all(s in skill_list for s in out)
    out2 = proficiencies.resolve_skill_proficiencies(skill_list, 2, ["stealth", "acrobatics"],
                                                      race_skills=("intimidation",))
    assert out2 == ["stealth", "acrobatics", "intimidation"]
    out3 = proficiencies.resolve_skill_proficiencies(skill_list, 2,
                                                     ["stealth", "acrobatics", "perception"])
    assert len(out3) == 2


def test_proficiency_bonus_applies_to_checks_and_saves():
    rs = DnDRuleset()
    pc = rs.build_pc({"name": "Grok", "race": "half_orc", "class": "barbarian", "alignment": "cn",
                      "abilities": {"str": 15, "con": 14, "dex": 13, "int": 10, "wis": 12, "cha": 8},
                      "skills": ["athletics", "survival"]})
    assert rs.modifier_for(pc, "athletics") == 5
    assert rs.modifier_for(pc, "medicine") == 1
    assert "intimidation" in pc.sheet["proficiencies"]
    assert rs.save_modifier(pc, "str") == 5 and rs.save_modifier(pc, "dex") == 1


def test_interactive_tiefling_warlock_build():
    rs = DnDRuleset()
    pres = Scripted(["Mara", "Tiefling", "Warlock", "Charlatan", "Chaotic Neutral",
                     "8", "13", "14", "10", "12", "15",
                     "deception, arcana",
                     "1", "2", "1", "2"])
    pc = CharacterCreator(pres, rs).run()
    s = pc.sheet
    assert s["abilities"]["cha"] == 17 and s["abilities"]["int"] == 11
    assert "deception" in s["proficiencies"] and "arcana" in s["proficiencies"]
    assert "sleight_of_hand" in s["proficiencies"]
    assert s["background"] == "Charlatan" and s["background_feature"]["name"] == "False Identity"
    assert s["roleplay"]["chosen"]["ideal"] and s["roleplay"]["chosen"]["flaw"]
    sc = s["spellcasting"]
    assert sc["type"] == "pact" and sc["ability"] == "cha"
    assert sc["spell_save_dc"] == 13 and sc["spell_attack_bonus"] == 5
    assert sc["cantrips_known"] == 2 and sc["spells_method"] == "known"
    assert s["alignment"] == "Chaotic Neutral" and "fire" in s["resistances"]
    assert s["attacks"][0]["name"] == "eldritch blast" and s["attacks"][0]["reach"] == "ranged"
    skill_menu = [m for m in pres.menus() if "skill proficiencies" in m.prompt][0]
    assert "(choose 2)" in skill_menu.prompt


def test_interactive_rogue_picks_four():
    rs = DnDRuleset()
    pres = Scripted(["Sly", "Halfling", "Rogue", "Soldier", "Chaotic Good",
                     "8", "15", "12", "13", "10", "14",
                     "1 2 3 4",
                     "1", "1", "1", "1"])
    pc = CharacterCreator(pres, rs).run()
    rogue_menu = [m for m in pres.menus() if "skill proficiencies" in m.prompt][0]
    assert "(choose 4)" in rogue_menu.prompt
    assert len(pc.sheet["proficiencies"]) >= 4 and "intimidation" in pc.sheet["proficiencies"]
    assert pc.sheet["abilities"]["dex"] == 17


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
