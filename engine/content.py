from __future__ import annotations

import inspect
import json
from pathlib import Path

from engine.state import Combatant, load_game, save_game
from engine.zones import Arena, Zone

__all__ = ["load_npc", "load_npc_file", "load_location", "load_location_file",
           "save_game", "load_game"]


def load_npc(data: dict, ruleset) -> Combatant:
    name = data["name"]
    factory = getattr(ruleset, "make_enemy", None)
    if factory is not None:
        wanted = {
            "attributes": data.get("attributes"), "abilities": data.get("abilities"),
            "attack": data.get("attack"), "disciplines": data.get("disciplines"),
            "generation": data.get("generation", 13), "humanity": data.get("humanity", 7),
            "soak": data.get("soak"), "intelligence": data.get("intelligence", 2),
            "morale": data.get("morale", 100), "mindless": data.get("mindless", False),
            "comprehends_language": data.get("comprehends_language", True),
        }
        params = inspect.signature(factory).parameters
        kwargs = {k: v for k, v in wanted.items() if k in params and v is not None}
        npc = factory(name, **kwargs)
    else:
        npc = Combatant(name=name, sheet=dict(data.get("sheet", {})))

    npc.sheet["kind"] = data.get("kind", "mortal")
    for key in ("inventory", "known_rituals"):
        if key in data:
            npc.sheet[key] = list(data[key])
    if data.get("persona"):
        npc.sheet["persona"] = data["persona"]
    if data.get("statuses"):
        npc.statuses.update(data["statuses"])
    return npc


def load_npc_file(path: str | Path, ruleset) -> Combatant:
    return load_npc(json.loads(Path(path).read_text(encoding="utf-8")), ruleset)


def load_location(data: dict) -> Arena:
    zones = {}
    for z in data["zones"]:
        zones[z["name"]] = Zone(
            name=z["name"],
            adjacent=frozenset(z.get("adjacent", [])),
            cover=z.get("cover", "none"),
            elevation=int(z.get("elevation", 0)),
            hazard=z.get("hazard"),
            is_exit=bool(z.get("is_exit", False)),
        )
    return Arena(zones=zones, placements=dict(data.get("placements", {})))


def load_location_file(path: str | Path) -> Arena:
    return load_location(json.loads(Path(path).read_text(encoding="utf-8")))
