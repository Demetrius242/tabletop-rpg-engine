import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.combat import CombatController
from engine.dice import ScriptedDice
from engine.llm import FakeLLMClient
from engine.state import GameState
from rulesets.dnd.core.dnd import DnDRuleset


class _Pres:
    def __init__(self):
        self.events = []
    def emit(self, ev):
        self.events.append(ev)
    def read_action(self):
        raise EOFError
    def of_type(self, t):
        return [e for e in self.events if isinstance(e, t)]


def _rs():
    rs = DnDRuleset()
    rs.use_setting(rs.list_settings()[0] if hasattr(rs, "list_settings") else "forgotten_realms")
    return rs


def test_short_rest_spends_hit_dice_to_heal():
    rs = _rs()
    pc = rs.make_pc("Hero")
    pc.sheet["max_hp"] = 20; pc.sheet["hp"] = 5
    pc.sheet["hit_die"] = 8; pc.sheet["hit_dice_total"] = 3; pc.sheet["hit_dice_remaining"] = 3
    rs.dice = ScriptedDice(6, 5)
    res = rs.short_rest(pc, spend_hit_dice=2)
    assert res["hit_dice_spent"] == 2 and res["healed"] > 0
    assert pc.sheet["hp"] > 5 and pc.sheet["hp"] <= 20
    assert res["hit_dice_remaining"] == 1


def test_short_rest_caps_at_max_and_pool():
    rs = _rs()
    pc = rs.make_pc("Hero")
    pc.sheet["max_hp"] = 10; pc.sheet["hp"] = 9
    pc.sheet["hit_die"] = 8; pc.sheet["hit_dice_total"] = 1; pc.sheet["hit_dice_remaining"] = 1
    rs.dice = ScriptedDice(8)
    res = rs.short_rest(pc, spend_hit_dice=5)
    assert res["hit_dice_spent"] == 1 and pc.sheet["hp"] == 10
    assert rs.short_rest(pc, spend_hit_dice=1)["hit_dice_spent"] == 0


def test_haggle_core_persuasion_discount():
    rs = _rs()
    pc = rs.make_pc("Hero")
    tk = rs.list_tradesmen()[0]; item = rs.shop_stock(tk)[0]
    rs.dice = ScriptedDice(19)
    out = rs.haggle(pc, item, tk, approach="persuasion")
    assert out["ok"] and out["price"] <= out["base_price"] and out["discount_pct"] >= 10
    assert rs.haggle_approaches() == ["persuasion", "intimidation"]


def test_hidden_party_surprises_enemies():
    rs = _rs()
    hero = rs.make_pc("Hero"); hero.statuses.add("hidden")
    goblin = rs.make_enemy("Goblin", hp=7, ac=12)
    ctrl = CombatController(FakeLLMClient(), _Pres(), GameState(pc=hero), rs, enemies=[goblin])
    ctrl._roll_initiative(); ctrl._determine_surprise()
    names = ctrl.surprised_names()
    assert "Goblin" in names and "Hero" not in names


def test_no_surprise_by_default():
    rs = _rs()
    hero = rs.make_pc("Hero")
    goblin = rs.make_enemy("Goblin", hp=7, ac=12)
    ctrl = CombatController(FakeLLMClient(), _Pres(), GameState(pc=hero), rs, enemies=[goblin])
    ctrl._roll_initiative(); ctrl._determine_surprise()
    assert ctrl.surprised_names() == []


def test_explicit_surprise_override():
    rs = _rs()
    hero = rs.make_pc("Hero")
    goblin = rs.make_enemy("Goblin", hp=7, ac=12)
    ctrl = CombatController(FakeLLMClient(), _Pres(), GameState(pc=hero), rs,
                            enemies=[goblin], surprise="party")
    ctrl._roll_initiative(); ctrl._determine_surprise()
    assert "Hero" in ctrl.surprised_names()


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
