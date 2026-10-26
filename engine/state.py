from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Combatant:
    name: str
    is_pc: bool = False
    statuses: set[str] = field(default_factory=set)
    sheet: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "is_pc": self.is_pc,
            "statuses": sorted(self.statuses),
            "sheet": self.sheet,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Combatant":
        return cls(
            name=d["name"],
            is_pc=d.get("is_pc", False),
            statuses=set(d.get("statuses", [])),
            sheet=d.get("sheet", {}),
        )


@dataclass
class Turn:
    role: str
    text: str


@dataclass
class GameState:
    pc: Combatant
    location: str = "a dim room with no obvious way out"
    mode: str = "exploration"
    history: list[Turn] = field(default_factory=list)
    flags: dict = field(default_factory=dict)

    HISTORY_LIMIT = 12

    def record(self, role: str, text: str) -> None:
        self.history.append(Turn(role, text))
        if len(self.history) > self.HISTORY_LIMIT:
            self.history = self.history[-self.HISTORY_LIMIT:]

    def recent(self, n: int = 6) -> list[Turn]:
        return self.history[-n:]

    def to_dict(self) -> dict:
        return {
            "pc": self.pc.to_dict(),
            "location": self.location,
            "mode": self.mode,
            "history": [{"role": t.role, "text": t.text} for t in self.history],
            "flags": self.flags,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        s = cls(
            pc=Combatant.from_dict(d["pc"]),
            location=d.get("location", ""),
            mode=d.get("mode", "exploration"),
            flags=d.get("flags", {}),
        )
        s.history = [Turn(t["role"], t["text"]) for t in d.get("history", [])]
        return s


def save_game(state: GameState, path: str | Path) -> None:
    Path(path).write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")


def load_game(path: str | Path) -> GameState:
    return GameState.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
