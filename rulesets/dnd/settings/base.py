from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WorldConcept:
    name: str
    text: str


@dataclass(frozen=True)
class Location:
    key: str
    name: str
    kind: str
    description: str
    mood: str
    hooks: tuple = ()
    adventure: str = ""


@dataclass(frozen=True)
class NPCCard:
    key: str
    name: str
    role: str
    race: str = "human"
    description: str = ""
    demeanor: str = ""
    voice: str = ""
    mannerisms: str = ""
    dialogue_examples: tuple = ()
    secret: str = ""
    hook: str = ""
    adventure: str = ""


@dataclass(frozen=True)
class Tradesman:
    key: str
    name: str
    location: str
    region: str
    tier: str = "city"
    categories: tuple = ()
    max_rarity: str = "rare"
    min_rarity: str = "common"
    stock_size: int = 6
    rarity_bias: float = 1.0
    markup: float = 1.0
    sell_rate: float = 0.5
    restock_interval: int = 3
    card: NPCCard | None = None
    sheet: dict | None = None


@dataclass(frozen=True)
class Setting:
    key: str
    name: str
    tone: str
    narration_angle: str
    concepts: tuple = ()
    sights: tuple = ()
    locations: dict = field(default_factory=dict)
    npcs: dict = field(default_factory=dict)
    tradesmen: dict = field(default_factory=dict)

    def location(self, key: str) -> Location | None:
        return self.locations.get((key or "").lower())

    def npc(self, key: str) -> NPCCard | None:
        return self.npcs.get((key or "").lower())

    def tradesman(self, key: str) -> "Tradesman | None":
        return self.tradesmen.get((key or "").lower())

    def list_locations(self, adventure: str = "") -> list:
        if not adventure:
            return list(self.locations.keys())
        a = (adventure or "").lower()
        return [k for k, loc in self.locations.items() if (loc.adventure or "").lower() == a]

    def list_npcs(self) -> list:
        return list(self.npcs.keys())

    def list_tradesmen(self) -> list:
        return list(self.tradesmen.keys())

    def submodule(self, name: str):
        import importlib
        try:
            return importlib.import_module(f"rulesets.dnd.settings.{self.key}.{name}")
        except ImportError:
            return None

    def narration_brief(self, max_concepts: int = 5) -> str:
        lines = [f"Setting: {self.name} -- {self.tone}.", self.narration_angle.strip()]
        if self.concepts:
            lines.append("What matters in this world:")
            for c in self.concepts[:max_concepts]:
                lines.append(f"- {c.name}: {c.text}")
        return ("World briefing (let this set the tone, texture, and assumptions of the world; "
                "evoke it through sensory detail and how people act, and never contradict the "
                "established setting):\n" + "\n".join(lines))
