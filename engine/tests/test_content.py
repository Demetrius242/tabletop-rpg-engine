import sys, pathlib
_root = pathlib.Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))

from engine.content import (load_game, load_location_file, load_npc_file, save_game)
from engine.state import GameState
from rulesets.storyteller.core.storyteller import StorytellerRuleset

DATA = _root / "data"


def test_every_npc_file_builds_a_combatant():
    rs = StorytellerRuleset()
    for path in sorted((DATA / "npcs").glob("*.json")):
        npc = load_npc_file(path, rs)
        assert npc.name and npc.sheet.get("kind")
        assert npc.sheet.get("soak", 0) >= 0
        res = rs.turn_model().resolve_attack(rs.make_pc("Tester"), npc)
        assert hasattr(res, "hit")


def test_ghoul_loads_with_its_kind_for_rituals():
    rs = StorytellerRuleset()
    ghoul = load_npc_file(DATA / "npcs" / "ghoul_renfield.json", rs)
    assert ghoul.sheet["kind"] == "ghoul"


def test_every_location_file_builds_a_connected_arena():
    for path in sorted((DATA / "locations").glob("*.json")):
        arena = load_location_file(path)
        assert arena.zones
        assert arena.exits()
        for name, zone in arena.zones.items():
            for adj in zone.adjacent:
                assert adj in arena.zones


def test_example_save_round_trips():
    state = load_game(DATA / "saves" / "example_aisling.json")
    assert isinstance(state, GameState)
    assert state.pc.sheet["known_rituals"] and state.pc.sheet["inventory"]
    rs = StorytellerRuleset()
    assert isinstance(rs.health_descriptor(state.pc), str)

    out = _root / "data" / "saves" / "_roundtrip_tmp.json"
    save_game(state, out)
    again = load_game(out)
    assert again.pc.name == state.pc.name and again.flags == state.flags
    out.unlink()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
