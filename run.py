from __future__ import annotations

import sys
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from engine.cli import CliPresenter
from engine.engine import ExplorationEngine
from engine.llm import FakeLLMClient, LlamaServerClient, OpenAIClient
from rulesets.dnd.core.dnd import DnDRuleset
from rulesets.storyteller.core.storyteller import StorytellerRuleset
from engine.state import GameState


def _arg(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def _server_url(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    raw = _arg(argv, "--server")
    if raw:
        return raw.rstrip("/").removesuffix("/completion")
    return "http://127.0.0.1:8080"


def real_client(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--openai" in argv:
        return OpenAIClient(base_url=_arg(argv, "--server", "http://127.0.0.1:8080"),
                            endpoint="chat" if "--chat" in argv else "completions",
                            model=_arg(argv, "--api-model", "local-model"),
                            api_key=_arg(argv, "--api-key"))
    return LlamaServerClient(base_url=_server_url(argv))


def build_client(use_fake: bool, *, combat: bool = False):
    if use_fake:
        if combat:
            return FakeLLMClient(
                default_text="Steel rings on steel in the cramped guardroom.",
                default_json='{"action": "attack", "target": "Goblin"}',
            )
        return FakeLLMClient(
            default_text=(
                "A draft stirs the dust at your feet. The torch gutters; the iron "
                "door ahead stays shut, but it does not look locked."
            )
        )
    return real_client()


def run_combat_demo(use_fake: bool) -> int:
    from engine.combat import CombatController
    from engine.zones import Arena, Zone
    ruleset = DnDRuleset()
    state = GameState(pc=ruleset.make_pc("Wren"), location="a ruined gatehouse")
    arena = Arena(
        zones={
            "yard": Zone("yard", frozenset({"ledge", "gate"})),
            "ledge": Zone("ledge", frozenset({"yard"}), cover="heavy", elevation=1),
            "gate": Zone("gate", frozenset({"yard"}), is_exit=True),
        },
        placements={"Wren": "yard", "Mara": "yard", "Brute": "yard",
                    "Goblin": "ledge", "Archer": "ledge"},
    )
    companions = [ruleset.make_companion("Mara")]
    enemies = [
        ruleset.make_enemy("Brute", hp=11, ac=12, attack=("club", 4, "1d8+1")),
        ruleset.make_enemy("Goblin", hp=7, ac=13, attack=("scimitar", 4, "1d6+1")),
        ruleset.make_enemy("Archer", hp=6, ac=12, attack=("bow", 4, "1d6"), reach="ranged"),
    ]

    class AutoPresenter(CliPresenter):
        def read_action(self):
            print("> attack Goblin")
            return "attack Goblin"
    presenter = (AutoPresenter(show_state_deltas=True) if use_fake
                 else CliPresenter(show_state_deltas=True))
    controller = CombatController(
        build_client(use_fake, combat=True), presenter, state, ruleset,
        enemies=enemies, companions=companions, arena=arena)
    print("Combat demo. You (Wren) and Mara hold the yard; a Brute is on you, a")
    print("Goblin and an Archer wait on the high ledge. Gate = the way out.")
    if use_fake:
        print("(--fake: Wren auto-attacks the Goblin, so she crosses to the ledge")
        print(" and eats an opportunity attack from the Brute on the way.)\n")
    victor = controller.run()
    print(f"\nResult: {victor}.")
    return 0


def build_ruleset(argv: list[str]):
    if "--st" in argv or "--storyteller" in argv:
        return StorytellerRuleset()
    return DnDRuleset()


def run_st_combat_demo(use_fake: bool) -> int:
    from engine.combat import CombatController
    from engine.events import Menu
    rs = StorytellerRuleset()
    state = GameState(pc=rs.make_pc("Lucius"), location="a blood-scented warehouse")
    foe = rs.make_enemy("Gangrel", soak=2, disciplines={"Protean": 2, "Fortitude": 2})
    foe.sheet["health_taken"] = 2

    class AutoPresenter(CliPresenter):
        def __init__(self, **kw):
            super().__init__(**kw)
            self._menu_pending = False

        def emit(self, event):
            if isinstance(event, Menu):
                self._menu_pending = True
            super().emit(event)

        def read_action(self):
            if self._menu_pending:
                self._menu_pending = False
                print("> 1  (blur)")
                return "1"
            print("> attack Gangrel")
            return "attack Gangrel"

    presenter = (AutoPresenter(show_state_deltas=True) if use_fake
                 else CliPresenter(show_state_deltas=True))
    client = (FakeLLMClient(default_text="Claws rake the dark.",
                            default_json='{"action": "attack", "target": "Gangrel"}')
              if use_fake else real_client())
    print("Storyteller / Vampire demo: Lucius faces a Gangrel. Resolution is d10 pools;")
    print("each round all combatants DECLARE in reverse initiative, then RESOLVE in")
    print("order. Lucius spends BLOOD on Celerity to act twice a turn; the Gangrel, an")
    print("enemy the engine drives, invokes Protean to grow aggravated CLAWS and then")
    print("rends with them. Potence adds to damage; the seven-level wound track fills")
    print("toward torpor. (Disciplines also resolve via use_discipline outside combat.)\n")
    victor = CombatController(client, presenter, state, rs, enemies=[foe]).run()
    print(f"\nResult: {victor}.")
    return 0


def main(argv: list[str]) -> int:
    use_fake = "--fake" in argv
    ruleset = build_ruleset(argv)
    if "--combat" in argv:
        if isinstance(ruleset, StorytellerRuleset):
            return run_st_combat_demo(use_fake)
        return run_combat_demo(use_fake)
    if "--create" in argv:
        from engine.creation import CharacterCreator
        pc = CharacterCreator(CliPresenter(), ruleset).run()
    else:
        pc = ruleset.make_pc("Lucius" if isinstance(ruleset, StorytellerRuleset) else "Wren")
    state = GameState(
        pc=pc,
        location="a cold stone antechamber lit by one guttering torch",
    )
    engine = ExplorationEngine(
        client=build_client(use_fake),
        presenter=CliPresenter(show_state_deltas=use_fake),
        state=state,
        ruleset=ruleset,
    )
    print("Type to play. 'help' for commands, 'quit' to exit.")
    engine.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
