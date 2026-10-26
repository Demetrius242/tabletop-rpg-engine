from __future__ import annotations

import sys
from pathlib import Path

import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.combat import CombatController, parse_power_invocation
from engine.dice import ScriptedDice
from engine.events import AttackResolved, Event, PowerUsed
from engine.llm import FakeLLMClient
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


def _vamp(rs, name, *, disc, willpower=5, generation=10, blood=10, attrs=None, abils=None, soak=2):
    v = rs.make_enemy(name, attributes=(attrs or {}), abilities=(abils or {}),
                      disciplines=disc, generation=generation, soak=soak)
    v.sheet["willpower"] = willpower
    v.sheet["blood"] = blood
    return v


SOCIAL = {"manipulation": 3, "charisma": 3, "wits": 3, "perception": 2}
TALK = {"intimidation": 2, "subterfuge": 2, "stealth": 2, "awareness": 1}


def test_rating_gates_a_power():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 6, 6))
    one = _vamp(rs, "Apprentice", disc={"Dominate": 1}, attrs=SOCIAL, abils=TALK)
    eyes = _vamp(rs, "Victim", disc={}, willpower=4)
    assert rs.use_discipline(one, "Dominate", "command", eyes).ok
    blocked = rs.use_discipline(one, "Dominate", "mesmerize", eyes)
    assert not blocked.ok and blocked.reason == "insufficient_dots"


def test_protean_claws_cost_blood():
    rs = StorytellerRuleset()
    g = _vamp(rs, "Gangrel", disc={"Protean": 2}, blood=10)
    res = rs.use_discipline(g, "Protean", "feral_claws")
    assert res.ok and res.success and res.blood_spent == 1
    assert "claws" in g.statuses and g.sheet["blood"] == 9
    dry = _vamp(rs, "Spent", disc={"Protean": 2}, blood=0)
    out = rs.use_discipline(dry, "Protean", "feral_claws")
    assert not out.ok and out.reason == "not_enough_blood" and "claws" not in dry.statuses


def test_per_turn_blood_cap_limits_powers():
    rs = StorytellerRuleset()
    g = _vamp(rs, "Gangrel", disc={"Protean": 5}, blood=10)
    assert rs.use_discipline(g, "Protean", "feral_claws").ok
    second = rs.use_discipline(g, "Protean", "mist_form")
    assert not second.ok and second.reason == "not_enough_blood" and "mist" not in g.statuses


def test_dominate_cannot_bend_stronger_blood():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 6, 6))
    childe = _vamp(rs, "Childe", disc={"Dominate": 3}, generation=11, attrs=SOCIAL, abils=TALK)
    elder = _vamp(rs, "Elder", disc={}, generation=8, willpower=5)
    out = rs.use_discipline(childe, "Dominate", "command", elder)
    assert not out.ok and out.reason == "blood_too_strong"


def test_dominate_requires_open_eyes():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 6, 6))
    d = _vamp(rs, "Master", disc={"Dominate": 3}, attrs=SOCIAL, abils=TALK)
    blind = _vamp(rs, "Blindfold", disc={}, willpower=4)
    blind.statuses.add("blinded")
    assert rs.use_discipline(d, "Dominate", "command", blind).reason == "no_eye_contact"
    raging = _vamp(rs, "Berserk", disc={}, willpower=4)
    raging.sheet["_frenzied"] = True
    assert rs.use_discipline(d, "Dominate", "command", raging).reason == "target_unreachable"


def test_dominate_command_resisted_by_willpower():
    rs = StorytellerRuleset(dice=ScriptedDice(4, 4, 2, 2, 2))
    d = _vamp(rs, "Master", disc={"Dominate": 1}, attrs=SOCIAL, abils=TALK)
    weak = _vamp(rs, "Weak", disc={}, willpower=4)
    res = rs.use_discipline(d, "Dominate", "command", weak, param="flee")
    assert res.success and "dominated" in weak.statuses
    assert weak.sheet["_dominated_command"] == "flee"
    rs2 = StorytellerRuleset(dice=ScriptedDice(6, 6, 2, 2, 2))
    d2 = _vamp(rs2, "Master", disc={"Dominate": 1}, attrs=SOCIAL, abils=TALK)
    iron = _vamp(rs2, "Iron", disc={}, willpower=8)
    out = rs2.use_discipline(d2, "Dominate", "command", iron)
    assert not out.success and "dominated" not in iron.statuses


def test_dread_gaze_terrifies_on_success():
    rs = StorytellerRuleset(dice=ScriptedDice(4, 4, 2, 2, 2))
    p = _vamp(rs, "Toreador", disc={"Presence": 2}, attrs=SOCIAL, abils=TALK)
    prey = _vamp(rs, "Prey", disc={}, willpower=4)
    res = rs.use_discipline(p, "Presence", "dread_gaze", prey)
    assert res.success and "terrified" in prey.statuses
    rs2 = StorytellerRuleset(dice=ScriptedDice(2, 2, 2, 2, 2))
    p2 = _vamp(rs2, "Toreador", disc={"Presence": 2}, attrs=SOCIAL, abils=TALK)
    brave = _vamp(rs2, "Brave", disc={}, willpower=4)
    assert not rs2.use_discipline(p2, "Presence", "dread_gaze", brave).success
    assert "terrified" not in brave.statuses


def test_majesty_and_awe_buff_the_caster():
    rs = StorytellerRuleset(dice=ScriptedDice(8, 8, 2, 2, 2))
    p = _vamp(rs, "Prince", disc={"Presence": 5}, attrs=SOCIAL, abils=TALK)
    assert rs.use_discipline(p, "Presence", "majesty").success and "majesty" in p.statuses
    rs2 = StorytellerRuleset(dice=ScriptedDice(8, 8, 2, 2, 2))
    star = _vamp(rs2, "Star", disc={"Presence": 1}, attrs=SOCIAL, abils=TALK)
    assert rs2.use_discipline(star, "Presence", "awe").success and "awe" in star.statuses


def test_entrancement_binds_the_target():
    rs = StorytellerRuleset(dice=ScriptedDice(4, 4, 2, 2, 2))
    p = _vamp(rs, "Siren", disc={"Presence": 3}, attrs=SOCIAL, abils=TALK)
    thrall = _vamp(rs, "Thrall", disc={}, willpower=4)
    assert rs.use_discipline(p, "Presence", "entrancement", thrall).success
    assert "entranced" in thrall.statuses


def test_cloak_the_gathering_hides_allies():
    rs = StorytellerRuleset(dice=ScriptedDice(8, 8, 2, 2, 2))
    nos = _vamp(rs, "Nosferatu", disc={"Obfuscate": 5}, attrs=SOCIAL, abils=TALK)
    a1 = _vamp(rs, "Friend1", disc={})
    a2 = _vamp(rs, "Friend2", disc={})
    res = rs.use_discipline(nos, "Obfuscate", "cloak_the_gathering", allies=[a1, a2])
    assert res.success and "hidden" in nos.statuses
    assert "hidden" in a1.statuses and "hidden" in a2.statuses


def test_quell_the_beast_drains_frenzy():
    rs = StorytellerRuleset(dice=ScriptedDice(4, 4, 2, 2, 2))
    a = _vamp(rs, "Gangrel", disc={"Animalism": 3}, attrs=SOCIAL, abils=TALK)
    raging = _vamp(rs, "Raging", disc={}, willpower=4)
    raging.sheet["_frenzied"] = True
    res = rs.use_discipline(a, "Animalism", "quell_the_beast", raging)
    assert res.success and not raging.sheet.get("_frenzied") and "cowed" in raging.statuses


def test_drawing_out_the_beast_transfers_frenzy():
    rs = StorytellerRuleset(dice=ScriptedDice(4, 4, 2, 2, 2))
    a = _vamp(rs, "Gangrel", disc={"Animalism": 5}, attrs=SOCIAL, abils=TALK)
    a.sheet["_frenzied"] = True
    victim = _vamp(rs, "Victim", disc={}, willpower=4)
    res = rs.use_discipline(a, "Animalism", "drawing_out_the_beast", victim)
    assert res.success and not a.sheet.get("_frenzied") and victim.sheet.get("_frenzied")


def test_forgetful_mind_resolves_to_a_cue():
    rs = StorytellerRuleset(dice=ScriptedDice(4, 4, 2, 2, 2))
    d = _vamp(rs, "Tremere", disc={"Dominate": 3}, attrs=SOCIAL, abils=TALK)
    mark = _vamp(rs, "Mark", disc={}, willpower=4)
    res = rs.use_discipline(d, "Dominate", "forgetful_mind", mark)
    assert res.ok and res.success and "memory" in res.cue.lower()
    assert not mark.statuses


def test_claws_status_adds_damage():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 2, 2, 2, 2))
    tm = rs.turn_model()
    clawed = rs.make_enemy("Gangrel", attributes={"dexterity": 3}, abilities={"brawl": 2})
    clawed.statuses.add("claws")
    res = tm.resolve_attack(clawed, rs.make_enemy("Mortal", soak=2))
    assert res.damage == 3 and res.raw["claws"] == 2


def test_mist_form_deflects_physical_attacks():
    rs = StorytellerRuleset(dice=ScriptedDice(6, 6, 6, 6, 6))
    tm = rs.turn_model()
    misty = rs.make_enemy("Wraith", soak=2)
    misty.statuses.add("mist")
    res = tm.resolve_attack(rs.make_enemy("Brute", abilities={"brawl": 3}), misty)
    assert not res.hit and res.raw.get("mist") and res.damage == 0


def test_hidden_and_majesty_raise_the_target_number():
    base = StorytellerRuleset(dice=ScriptedDice(6, 6, 2, 2, 2)).turn_model()
    atk = lambda rs: rs.make_enemy("Brute", attributes={"dexterity": 3}, abilities={"brawl": 2})
    rs0 = StorytellerRuleset(dice=ScriptedDice(6, 6, 2, 2, 2))
    assert base.resolve_attack(atk(rs0), rs0.make_enemy("Open", soak=0)).hit
    rsh = StorytellerRuleset(dice=ScriptedDice(6, 6, 2, 2, 2)); tmh = rsh.turn_model()
    hidden = rsh.make_enemy("Unseen", soak=0); hidden.statuses.add("hidden")
    rh = tmh.resolve_attack(atk(rsh), hidden)
    assert rh.raw["target"] == 8 and not rh.hit
    rsm = StorytellerRuleset(dice=ScriptedDice(6, 6, 2, 2, 2)); tmm = rsm.turn_model()
    regal = rsm.make_enemy("Regal", soak=0); regal.statuses.add("majesty")
    rm = tmm.resolve_attack(atk(rsm), regal)
    assert rm.raw["target"] == 9 and not rm.hit


def test_forced_action_reads_statuses():
    rs = StorytellerRuleset()
    def one(setup):
        c = rs.make_enemy("X", disciplines={})
        setup(c)
        return rs.forced_action(c)
    assert one(lambda c: c.statuses.add("terrified")) == "flee"
    assert one(lambda c: c.statuses.add("mist")) == "pass"
    assert one(lambda c: c.statuses.add("entranced")) == "pass"
    assert one(lambda c: c.sheet.__setitem__("_dominated_command", "flee")) == "flee"
    assert one(lambda c: c.sheet.__setitem__("_frenzied", True)) == "attack"
    assert one(lambda c: None) is None


def test_ai_grows_claws_when_it_can():
    rs = StorytellerRuleset()
    able = rs.make_enemy("Gangrel", disciplines={"Protean": 2}, generation=10)
    assert rs.ai_combat_power(able) == "feral_claws"
    able.statuses.add("claws")
    assert rs.ai_combat_power(able) is None
    broke = rs.make_enemy("Gangrel", disciplines={"Protean": 2})
    broke.sheet["blood"] = 1
    assert rs.ai_combat_power(broke) is None


def test_parse_power_invocation_is_explicit_and_reliable():
    rs = StorytellerRuleset()
    actor = rs.make_enemy("V", disciplines={"Protean": 2, "Presence": 2})
    powers = rs.available_combat_powers(actor)
    assert {"feral_claws", "dread_gaze"} <= {p.key for p in powers}

    def P(text):
        return parse_power_invocation(text, powers, ("Ghoul",))

    assert P("use feral claws").power == "feral_claws"
    i = P("invoke dread gaze on the Ghoul")
    assert i.power == "dread_gaze" and i.target == "Ghoul"
    assert P("dread gaze the ghoul").power == "dread_gaze"
    assert P("feral_claws").power == "feral_claws"
    assert P("claws").power == "feral_claws"
    assert P("attack the Ghoul") is None
    assert P("defend") is None
    assert P("I claw my way past him") is None
    assert P("use mist form").power == ""
    assert P("use my discipline").power == ""
    assert parse_power_invocation("use feral claws", [], ("Ghoul",)) is None


def test_power_invocation_through_controller_grows_claws_and_bites():
    rs = StorytellerRuleset(dice=ScriptedDice(9, 1, 2, 2, 2, 2, 2, 6, 2, 2, 2, 2))
    pc = rs.make_pc("Sun")
    pc.sheet["disciplines"] = {"Protean": 2, "Potence": 1}
    state = GameState(pc=pc, location="a drainage tunnel")
    ghoul = rs.make_enemy("Ghoul", soak=2, disciplines={})
    ghoul.sheet["health_taken"] = 4
    client = FakeLLMClient(default_text="Bone and shadow.",
                           default_json='{"action": "attack", "target": "Ghoul"}')
    pres = ScriptedPresenter(["no", "use feral claws", "no", "attack Ghoul"])
    victor = CombatController(client, pres, state, rs, enemies=[ghoul]).run()
    assert victor == "party", victor
    used = pres.of_type(PowerUsed)
    assert used and used[0].power == "Feral Claws" and used[0].success and used[0].ok
    assert "claws" in pc.statuses and pc.sheet["blood"] == 9
    kill = [e for e in pres.of_type(AttackResolved) if e.attacker == "Sun" and e.defeated]
    assert kill and kill[0].raw.get("claws") == 2


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
