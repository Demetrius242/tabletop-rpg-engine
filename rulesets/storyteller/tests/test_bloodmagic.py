import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.engine import ExplorationEngine
from engine.events import Event, PowerUsed, RiteCast, SystemMessage
from engine.dice import ScriptedDice
from engine.llm import FakeLLMClient
from rulesets.storyteller.additional.rituals import perform_ritual
from rulesets.storyteller.core.storyteller import StorytellerRuleset
from engine.state import GameState


class ScriptedPresenter:
    def __init__(self, inputs=()):
        self._inputs = list(inputs)
        self.events: list[Event] = []

    def emit(self, event):
        self.events.append(event)

    def read_action(self):
        if not self._inputs:
            raise EOFError
        return self._inputs.pop(0)

    def of_type(self, t):
        return [e for e in self.events if isinstance(e, t)]


def _explore(disciplines, inputs, *, dice=None, inventory=None, known=None, blood=10):
    rs = StorytellerRuleset(dice=dice or ScriptedDice(default=8))
    pc = rs.make_pc("Mage")
    pc.sheet["disciplines"] = dict(disciplines)
    pc.sheet["blood"] = blood
    pc.sheet["attributes"]["intelligence"] = 3
    pc.sheet["abilities"]["occult"] = 3
    if inventory is not None:
        pc.sheet["inventory"] = list(inventory)
    if known is not None:
        pc.sheet["known_rituals"] = list(known)
    state = GameState(pc=pc, location="a candlelit haven")
    pres = ScriptedPresenter(inputs)
    ExplorationEngine(client=FakeLLMClient(default_text="The dark answers."),
                      presenter=pres, state=state, ruleset=rs).run()
    return pc, pres


def test_exploration_invokes_a_self_power():
    pc, pres = _explore({"Protean": 2}, ["use feral claws"])
    used = pres.of_type(PowerUsed)
    assert used and used[0].power == "Feral Claws" and used[0].success
    assert "claws" in pc.statuses


def test_exploration_invokes_a_targeted_power():
    pc, pres = _explore({"Presence": 2}, ["use dread gaze on the sentry"])
    used = pres.of_type(PowerUsed)
    assert used and used[0].power == "Dread Gaze" and used[0].success


def test_exploration_offers_help_on_an_unknown_invocation():
    pc, pres = _explore({"Presence": 2}, ["use my discipline"])
    msgs = pres.of_type(SystemMessage)
    assert any("invoke" in m.text.lower() for m in msgs)
    assert not pres.of_type(PowerUsed)


def test_exploration_ordinary_input_is_not_intercepted():
    pc, pres = _explore({"Presence": 2}, ["I study the faded mural"])
    assert not pres.of_type(PowerUsed) and not pres.of_type(RiteCast)


def test_exploration_performs_a_ritual_and_consumes_ingredients():
    pc, pres = _explore({"Path of Blood": 1}, ["perform deflection of wooden doom"],
                        inventory=["splinter"], known=["deflection_of_wooden_doom"])
    rites = pres.of_type(RiteCast)
    assert rites and rites[0].success and rites[0].rite == "Deflection of Wooden Doom"
    assert "stake_warded" in pc.statuses
    assert "splinter" not in pc.sheet["inventory"]


def test_exploration_ritual_blocked_by_missing_ingredient():
    pc, pres = _explore({"Path of Blood": 1}, ["perform deflection of wooden doom"],
                        inventory=[], known=["deflection_of_wooden_doom"])
    rites = pres.of_type(RiteCast)
    assert rites and not rites[0].ok and rites[0].reason == "missing_ingredients"
    assert "splinter" in rites[0].missing
    assert "stake_warded" not in pc.statuses


def _thaumaturge(known=(), inv=(), dice=None):
    rs = StorytellerRuleset(dice=dice or ScriptedDice(default=8))
    m = rs.make_enemy("Tremere", disciplines={"Path of Blood": 3})
    m.sheet["attributes"]["intelligence"] = 3
    m.sheet["abilities"]["occult"] = 3
    m.sheet["known_rituals"] = list(known)
    m.sheet["inventory"] = list(inv)
    return rs, m


def test_ritual_requires_being_learned():
    rs, m = _thaumaturge(known=[], inv=["splinter"])
    res = perform_ritual(rs, m, "deflection_of_wooden_doom")
    assert not res.ok and res.reason == "not_known"
    assert "splinter" in m.sheet["inventory"]


def test_ritual_turned_aside_by_a_protected_target():
    rs, m = _thaumaturge(known=["call_of_the_hungry_dead"], inv=["grave_dirt"])
    saint = rs.make_enemy("Saint")
    saint.statuses.add("warded")
    res = perform_ritual(rs, m, "call_of_the_hungry_dead", saint)
    assert res.ok and not res.success and res.reason == "protected"
    assert "haunted" not in saint.statuses
    assert "grave_dirt" not in m.sheet["inventory"]


def test_ritual_respects_the_target_kind():
    rs, m = _thaumaturge(known=["ward_versus_ghouls"], inv=["vial_of_blood", "salt"])
    human = rs.make_enemy("Bystander")
    res = perform_ritual(rs, m, "ward_versus_ghouls", human)
    assert res.ok and not res.success and res.reason == "wrong_target"

    rs, m = _thaumaturge(known=["ward_versus_ghouls"], inv=["vial_of_blood", "salt"])
    ghoul = rs.make_enemy("Renfield")
    ghoul.sheet["kind"] = "ghoul"
    res = perform_ritual(rs, m, "ward_versus_ghouls", ghoul)
    assert res.ok and res.success and "ghoul_warded" in ghoul.statuses


def test_ritual_can_fail_its_roll_and_still_spend_materials():
    rs, m = _thaumaturge(known=["deflection_of_wooden_doom"], inv=["splinter"],
                         dice=ScriptedDice(default=2))
    res = perform_ritual(rs, m, "deflection_of_wooden_doom")
    assert res.ok and not res.success
    assert "splinter" not in m.sheet["inventory"]
    assert "stake_warded" not in m.statuses


def test_lure_of_flames_burns_for_net_plus_rating():
    rs = StorytellerRuleset(dice=ScriptedDice(8, 8, default=2))
    caster = rs.make_enemy("Pyromancer", disciplines={"Lure of Flames": 2})
    caster.sheet["attributes"]["intelligence"] = 1
    caster.sheet["abilities"]["occult"] = 1
    caster.sheet["blood"] = 5
    target = rs.make_enemy("Kindling", soak=0)
    res = rs.use_discipline(caster, "Lure of Flames", "palm_of_flame", target)
    assert res.success and res.damage_dealt == 3
    assert target.sheet["health_taken"] == 3
    assert caster.sheet["blood"] == 4


def test_theft_of_vitae_wounds_and_feeds_the_caster():
    rs = StorytellerRuleset(dice=ScriptedDice(8, 8, default=2))
    caster = rs.make_enemy("Leech", disciplines={"Path of Blood": 4})
    caster.sheet["attributes"]["intelligence"] = 1
    caster.sheet["abilities"]["occult"] = 1
    caster.sheet["blood"] = 3
    victim = rs.make_enemy("Donor", soak=0)
    victim.sheet["blood"] = 5
    victim.sheet["willpower"] = 3
    res = rs.use_discipline(caster, "Path of Blood", "theft_of_vitae", victim)
    assert res.success and res.damage_dealt == 3
    assert victim.sheet["health_taken"] == 3
    assert victim.sheet["blood"] == 2 and caster.sheet["blood"] == 6


def _caster(disc, dots):
    rs = StorytellerRuleset(dice=ScriptedDice(default=8))
    c = rs.make_enemy("Caster", disciplines={disc: dots})
    c.sheet["blood"] = 10
    return rs, c


def test_obtenebration_entangles_and_blinds():
    rs, c = _caster("Obtenebration", 3)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Obtenebration", "arms_of_the_abyss", prey).success
    assert "entangled" in prey.statuses
    rs, c = _caster("Obtenebration", 2)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Obtenebration", "shroud_of_night", prey).success
    assert "blinded" in prey.statuses


def test_quietus_poisons():
    rs, c = _caster("Quietus", 2)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Quietus", "scorpions_touch", prey).success
    assert "poisoned" in prey.statuses


def test_serpentis_paralyzes_with_a_stare():
    rs, c = _caster("Serpentis", 1)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Serpentis", "eyes_of_the_serpent", prey).success
    assert "paralyzed" in prey.statuses


def test_vicissitude_horrid_form_is_a_self_warform():
    rs, c = _caster("Vicissitude", 4)
    assert rs.use_discipline(c, "Vicissitude", "horrid_form").success
    assert "warform" in c.statuses


def test_chimerstry_confuses():
    rs, c = _caster("Chimerstry", 3)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Chimerstry", "apparition", prey).success
    assert "confused" in prey.statuses


def test_dementation_maddens_and_breaks_minds():
    rs, c = _caster("Dementation", 4)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Dementation", "voice_of_madness", prey).success
    assert "maddened" in prey.statuses and prey.sheet.get("_frenzied")
    rs, c = _caster("Dementation", 5)
    prey = rs.make_enemy("Prey")
    assert rs.use_discipline(c, "Dementation", "total_insanity", prey).success
    assert "insane" in prey.statuses and prey.sheet["derangements"]


def _attack(attacker_statuses=(), defender_statuses=(), soak=2):
    rs = StorytellerRuleset(dice=ScriptedDice(8, 8, 8, 8, 8))
    a = rs.make_enemy("Striker", attributes={"dexterity": 3}, abilities={"brawl": 3})
    for s in attacker_statuses:
        a.statuses.add(s)
    d = rs.make_enemy("Mark", soak=soak)
    for s in defender_statuses:
        d.statuses.add(s)
    return rs.turn_model().resolve_attack(a, d)


def test_armor_of_scales_and_bone_adds_soak():
    r = _attack(defender_statuses=["armored"], soak=2)
    assert r.hit and r.raw["soak"] == 4


def test_a_blinded_attacker_strikes_at_a_penalty():
    r = _attack(attacker_statuses=["blinded"])
    assert r.raw["target"] == 8


def test_the_horrid_war_form_rends_harder():
    r = _attack(attacker_statuses=["warform"])
    assert r.hit and r.raw["claws"] == 3


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} passed")
