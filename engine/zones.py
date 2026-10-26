from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

COVER_AC = {"none": 0, "light": 2, "heavy": 5}


@dataclass(frozen=True)
class Zone:
    name: str
    adjacent: frozenset = frozenset()
    cover: str = "none"
    elevation: int = 0
    hazard: str | None = None
    is_exit: bool = False


@dataclass
class Arena:
    zones: dict
    placements: dict = field(default_factory=dict)

    @classmethod
    def single(cls, names, zone_name: str = "the field") -> "Arena":
        return cls({zone_name: Zone(zone_name)}, {n: zone_name for n in names})

    def zone_of(self, name: str) -> str:
        return self.placements[name]

    def are_adjacent(self, a: str, b: str) -> bool:
        return b in self.zones[a].adjacent

    def neighbors(self, zone: str) -> set:
        return set(self.zones[zone].adjacent)

    def exits(self) -> list:
        return [n for n, z in self.zones.items() if z.is_exit]

    def bfs(self, src: str):
        seen = {src}
        q = deque([src])
        while q:
            z = q.popleft()
            yield z
            for nb in sorted(self.zones[z].adjacent):
                if nb not in seen:
                    seen.add(nb)
                    q.append(nb)

    def shortest_path(self, src: str, dst: str) -> list:
        if src == dst:
            return [src]
        seen = {src}
        q = deque([[src]])
        while q:
            path = q.popleft()
            for nb in sorted(self.zones[path[-1]].adjacent):
                if nb == dst:
                    return path + [nb]
                if nb not in seen:
                    seen.add(nb)
                    q.append(path + [nb])
        return []

    def step_toward(self, src: str, dst: str) -> str | None:
        path = self.shortest_path(src, dst)
        return path[1] if len(path) >= 2 else None
