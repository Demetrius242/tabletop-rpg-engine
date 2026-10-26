from __future__ import annotations

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.creation import CharacterCreator
from engine.events import CharacterCreated, Event, Menu, SystemMessage
from engine.ruleset import Ruleset
from rulesets.dnd.core.dnd import DnDRuleset
from engine.state import Combatant


class ScriptedPresenter:
    def __init__(self, inputs):
        self._inputs = list(inputs)
        self.events: list[Event] = []

    def emit(self, event):
        self.events.append(event)

    def read_action(self):
        if not self._inputs:
            raise EOFError("creation asked for more input than scripted")
        return self._inputs.pop(0)

    def of_type(self, t):
        return [e for e in self.events if isinstance(e, t)]


def _create(rs, inputs):
    pres = ScriptedPresenter(inputs)
    pc = CharacterCreator(pres, rs).run()
    return pc, pres


def test_spec_is_ordered_and_typed():
    spec = DnDRuleset().creation_spec()
    assert [s.key for s in spec] == ["name", "race", "class", "background", "alignment",
                                     "abilities", "skills", "trait", "ideal", "bond", "flaw"]
    kinds = {s.key: s.kind for s in spec}
    assert kinds == {"name": "text", "race": "choose_one", "class": "choose_one",
                     "background": "choose_one", "alignment": "choose_one",
                     "abilities": "assign", "skills": "choose_many",
                     "trait": "choose_one", "ideal": "choose_one",
                     "bond": "choose_one", "flaw": "choose_one"}


def test_build_dwarf_fighter():
    rs = DnDRuleset()
    pc, pres = _create(rs, ["Borin", "Dwarf", "Fighter", "Soldier", "Lawful Good",
                            "15", "14", "13", "12", "10", "8",
                            "athletics, perception",
                            "1", "1", "1", "1"])
    s = pc.sheet
    assert pc.name == "Borin" and pc.is_pc
    assert s["abilities"] == {"str": 15, "dex": 14, "con": 15,
                              "int": 12, "wis": 11, "cha": 8}
    assert s["max_hp"] == 12 and s["ac"] == 16
    atk = s["attacks"][0]
    assert atk["name"] == "longsword" and atk["bonus"] == 4 and atk["damage"] == "1d8+2"
    assert s["proficiencies"] == ["athletics", "perception", "intimidation"]
    assert s["save_proficiencies"] == ["str", "con"]
    assert s["race"] == "Dwarf" and s["class"] == "Fighter"
    assert s["background"] == "Soldier" and s["alignment"] == "Lawful Good"
    assert pres.of_type(CharacterCreated)[0].name == "Borin"


def test_elf_rogue_picks_four_and_gets_race_skill():
    rs = DnDRuleset()
    pc, _ = _create(rs, ["Sly", "Elf", "Rogue", "Soldier", "Chaotic Neutral",
                         "8", "15", "12", "13", "10", "14",
                         "stealth, acrobatics, investigation, deception",
                         "1", "1", "1", "1"])
    s = pc.sheet
    assert s["abilities"]["dex"] == 17 and s["abilities"]["int"] == 14
    atk = s["attacks"][0]
    assert atk["name"] == "shortsword" and atk["bonus"] == 5 and atk["damage"] == "1d6+3"
    assert s["ac"] == 15 and s["max_hp"] == 9
    assert "perception" in s["proficiencies"] and "intimidation" in s["proficiencies"]
    assert len(s["proficiencies"]) >= 5
    assert s["save_proficiencies"] == ["dex", "int"]


def test_bad_choice_reprompts():
    rs = DnDRuleset()
    pc, pres = _create(rs, ["Aria", "Orc", "Elf", "Wizard", "Sage", "True Neutral",
                            "8", "14", "13", "15", "12", "10",
                            "arcana, investigation",
                            "1", "1", "1", "1"])
    race_menus = [e for e in pres.of_type(Menu) if e.prompt == "Choose a race"]
    assert len(race_menus) == 2
    assert pc.sheet["race"] == "Elf"


def test_empty_name_reprompts():
    rs = DnDRuleset()
    pc, pres = _create(rs, ["", "Mara", "Human", "Cleric", "Acolyte", "Neutral Good",
                            "8", "13", "14", "10", "15", "12",
                            "insight, religion",
                            "1", "1", "1", "1"])
    assert pc.name == "Mara"
    assert any("enter a value" in e.text for e in pres.of_type(SystemMessage))


def test_created_pc_is_combat_ready():
    rs = DnDRuleset()
    pc, _ = _create(rs, ["Wren", "Human", "Fighter", "Soldier", "Lawful Good",
                         "15", "14", "13", "12", "10", "8",
                         "athletics, perception",
                         "1", "1", "1", "1"])
    assert not rs.is_defeated(pc) and rs.health_descriptor(pc) == "unhurt"
    est = rs.turn_model().estimate_attack(pc, rs.make_enemy("Goblin"))
    assert est.hit_chance > 0 and est.expected_damage > 0


class _MinimalRuleset(Ruleset):
    def resolve_check(self, *a, **k): raise NotImplementedError
    def modifier_for(self, *a, **k): return 0
    def skill_names(self): return []
    def difficulty_for_band(self, band): raise NotImplementedError
    def health_descriptor(self, actor): return "fine"
    def apply_damage(self, actor, amount, dtype=None): pass
    def is_defeated(self, actor): return False
    def health_fraction(self, actor): return 1.0
    def turn_model(self): raise NotImplementedError
    def make_pc(self, name): return Combatant(name=name, is_pc=True, sheet={})


def test_default_spec_is_name_only():
    rs = _MinimalRuleset()
    spec = rs.creation_spec()
    assert len(spec) == 1 and spec[0].kind == "text"
    pc, _ = _create(rs, ["Solo"])
    assert pc.name == "Solo" and pc.is_pc


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
