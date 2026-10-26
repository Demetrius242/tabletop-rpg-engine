from __future__ import annotations

from dataclasses import dataclass, field

from .state import Combatant
from .zones import Arena, Zone

_NOTICE_ORDER = ("obvious", "trivial", "easy", "moderate", "hard", "formidable")
_NOTICE_RANK = {n: i for i, n in enumerate(_NOTICE_ORDER)}
_BAND_ORDER = ("botch", "failure", "marginal", "success", "exceptional", "critical")
_BAND_RANK = {b: i for i, b in enumerate(_BAND_ORDER)}
_BAND_REVEALS = {"botch": -1, "failure": -1, "marginal": _NOTICE_RANK["trivial"],
                 "success": _NOTICE_RANK["easy"], "exceptional": _NOTICE_RANK["hard"],
                 "critical": _NOTICE_RANK["formidable"]}


@dataclass
class Feature:
    key: str
    name: str
    zone: str
    description: str = ""
    interactions: tuple = ()
    contents: tuple = ()
    hidden: bool = False
    notice: str = "easy"
    locked: bool = False
    gates: str = ""
    note: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class Presence:
    key: str
    name: str
    zone: str
    kind: str = "npc"
    disposition: str = "neutral"
    awareness: str = "unaware"
    hidden: bool = False
    notice: str = "moderate"
    combatant: Combatant | None = None
    card: object = None
    note: str = ""
    follows_pc: bool = False


@dataclass
class SceneZone:
    key: str
    name: str
    description: str = ""
    adjacent: tuple = ()
    cover: str = "none"
    elevation: int = 0
    is_exit: bool = False
    mood: str = ""
    hazard: str = ""
    merchants: tuple = ()

    def to_zone(self) -> Zone:
        return Zone(self.key, frozenset(self.adjacent), self.cover, self.elevation, None, self.is_exit)


@dataclass
class Scene:
    key: str
    name: str
    kind: str = "site"
    zones: dict = field(default_factory=dict)
    features: dict = field(default_factory=dict)
    presences: dict = field(default_factory=dict)
    pc_zone: str = ""
    hooks: tuple = ()
    flags: dict = field(default_factory=dict)
    merchants: tuple = ()

    def __post_init__(self):
        if not self.pc_zone and self.zones:
            self.pc_zone = next(iter(self.zones))

    def merchants_here(self) -> list:
        z = self.here()
        zone_m = list(getattr(z, "merchants", ()) or []) if z is not None else []
        return zone_m or list(self.merchants or [])

    def zone(self, key: str) -> SceneZone | None:
        return self.zones.get(key)

    def here(self) -> SceneZone | None:
        return self.zones.get(self.pc_zone)

    def _resolve_zone(self, ref: str) -> str | None:
        r = (ref or "").strip().lower()
        if r in self.zones:
            return r
        for k, z in self.zones.items():
            if z.name.lower() == r or r in z.name.lower() or r in k:
                return k
        return None

    def exits(self, zone: str | None = None) -> list:
        z = self.zones.get(zone or self.pc_zone)
        return list(z.adjacent) if z else []

    def _gate_blocking(self, dest: str):
        for f in self.features.values():
            if f.gates == dest and f.locked:
                return f
        return None

    def can_move(self, dest_ref: str) -> dict:
        dest = self._resolve_zone(dest_ref)
        if dest is None:
            return {"ok": False, "reason": "no_such_zone", "message": f"There's no '{dest_ref}' from here."}
        if dest == self.pc_zone:
            return {"ok": False, "reason": "already_here", "message": "You're already there."}
        if dest not in self.exits():
            return {"ok": False, "reason": "not_adjacent",
                    "message": f"You can't reach {self.zones[dest].name} directly from here."}
        gate = self._gate_blocking(dest)
        if gate is not None:
            return {"ok": False, "reason": "blocked", "gate": gate.key,
                    "message": f"The way is blocked by {gate.name}."}
        return {"ok": True, "dest": dest}

    def move_pc(self, dest_ref: str) -> dict:
        res = self.can_move(dest_ref)
        if not res["ok"]:
            return res
        self.pc_zone = res["dest"]
        for p in self.presences.values():
            if p.follows_pc:
                p.zone = self.pc_zone
        z = self.zones[self.pc_zone]
        return {"ok": True, "zone": self.pc_zone, "message": f"You move to {z.name}.",
                "alertness": self.alertness()}

    def features_in(self, zone: str | None = None, *, include_hidden=False) -> list:
        z = zone or self.pc_zone
        return [f for f in self.features.values()
                if f.zone == z and (include_hidden or not f.hidden)]

    def presences_in(self, zone: str | None = None, *, include_hidden=False) -> list:
        z = zone or self.pc_zone
        return [p for p in self.presences.values()
                if p.zone == z and (include_hidden or not p.hidden)]

    def feature(self, ref: str):
        r = (ref or "").strip().lower()
        if r in self.features:
            return self.features[r]
        for f in self.features.values():
            if f.name.lower() == r or r in f.name.lower() or r in f.key:
                return f
        return None

    def presence(self, ref: str):
        r = (ref or "").strip().lower()
        if r in self.presences:
            return self.presences[r]
        for p in self.presences.values():
            if p.name.lower() == r or r in p.name.lower() or r in p.key:
                return p
        return None

    def search(self, band: str, zone: str | None = None) -> dict:
        z = zone or self.pc_zone
        ceiling = _BAND_REVEALS.get(band, -1)
        found_f, found_p = [], []
        for f in self.features.values():
            if f.zone == z and f.hidden and _NOTICE_RANK.get(f.notice, 99) <= ceiling:
                f.hidden = False
                found_f.append(f)
        for p in self.presences.values():
            if p.zone == z and p.hidden and _NOTICE_RANK.get(p.notice, 99) <= ceiling:
                p.hidden = False
                found_p.append(p)
        return {"features": found_f, "presences": found_p,
                "found_anything": bool(found_f or found_p)}

    def reveal_enemies(self, *, zones: list | None = None) -> list:
        sensed = []
        for p in self.presences.values():
            if p.kind != "enemy":
                continue
            if zones is not None and p.zone not in zones:
                continue
            sensed.append({"name": p.name, "zone": p.zone, "zone_name": self.zones[p.zone].name,
                           "was_hidden": p.hidden})
            p.hidden = False
        return sensed

    def unlock(self, feature_ref: str) -> bool:
        f = self.feature(feature_ref)
        if f is None or not f.locked:
            return False
        f.locked = False
        f.state["unlocked"] = True
        return True

    def take(self, feature_ref: str) -> dict:
        f = self.feature(feature_ref)
        if f is None or f.hidden:
            return {"ok": False, "message": "There's nothing like that to take here.", "items": []}
        if f.locked:
            return {"ok": False, "message": f"{f.name} is locked.", "items": []}
        if f.state.get("taken"):
            return {"ok": False, "message": f"You've already cleared out {f.name}.", "items": []}
        items = list(f.contents)
        f.state["taken"] = True
        return {"ok": True, "items": items, "feature": f.name,
                "message": (f"You take what {f.name} held." if items else f"{f.name} holds nothing of use.")}

    def mark(self, feature_ref: str, key: str, value=True) -> None:
        f = self.feature(feature_ref)
        if f is not None:
            f.state[key] = value

    def _enemy_participants(self) -> list:
        here = self.pc_zone
        near = set(self.exits(here)) | {here}
        return [p for p in self.presences.values() if p.kind == "enemy" and p.zone in near]

    def alertness(self) -> str:
        levels = ["unaware", "suspicious", "alert"]
        worst = 0
        for p in self._enemy_participants():
            worst = max(worst, levels.index(p.awareness) if p.awareness in levels else 0)
        return levels[worst]

    def raise_alarm(self, level: str = "alert") -> None:
        for p in self._enemy_participants():
            order = ["unaware", "suspicious", "alert"]
            if order.index(level) > order.index(p.awareness if p.awareness in order else "unaware"):
                p.awareness = level

    def to_combat(self, pc: Combatant) -> dict:
        enemies = [p for p in self._enemy_participants() if p.combatant is not None]
        companions = [p for p in self.presences_in()
                      if p.kind == "npc" and p.disposition == "friendly" and p.combatant is not None]
        placements = {pc.name: self.pc_zone}
        for p in enemies + companions:
            placements[p.combatant.name] = p.zone
        arena = Arena({k: z.to_zone() for k, z in self.zones.items()}, placements)
        surprise = "party" if self.alertness() == "unaware" and enemies else ""
        self.raise_alarm("alert")
        return {"enemies": [p.combatant for p in enemies],
                "companions": [p.combatant for p in companions],
                "arena": arena, "surprise": surprise}

    def brief(self) -> str:
        z = self.here()
        if z is None:
            return ""
        lines = [f"You are in: {z.name}." + (f" {z.description}" if z.description else "")]
        if z.mood:
            lines.append(f"Mood: {z.mood}.")
        npcs = [p for p in self.presences_in() if p.kind == "npc"]
        foes = [p for p in self.presences_in() if p.kind == "enemy"]
        feats = self.features_in()
        if npcs:
            lines.append("People here: "
                         + "; ".join(f"{p.name} ({p.disposition})" for p in npcs) + ".")
        if foes:
            lines.append("Also here: "
                         + "; ".join(f"{p.name} [{p.awareness} of you]" for p in foes) + ".")
        if feats:
            lines.append("You can see: " + ", ".join(f.name for f in feats) + ".")
        exits = [self.zones[e].name for e in self.exits()]
        if exits:
            lines.append("Ways on: " + ", ".join(exits) + ".")
        return ("Scene (these facts are true; narrate only what is here and never invent exits, "
                "people, or objects that aren't listed):\n" + "\n".join(lines))

    def check_factors(self) -> dict:
        z = self.here()
        factors = dict(self.flags.get("factors", {}))
        if z is not None:
            factors.update(self.flags.get("zone_factors", {}).get(z.key, {}))
        alert = self.alertness()
        if alert != "unaware":
            factors["target_alertness"] = "alert" if alert == "alert" else "wary"
        return factors

    def to_dict(self) -> dict:
        def zone_d(z):
            return {"key": z.key, "name": z.name, "description": z.description,
                    "adjacent": list(z.adjacent), "cover": z.cover, "elevation": z.elevation,
                    "is_exit": z.is_exit, "mood": z.mood, "hazard": z.hazard}

        def feat_d(f):
            return {"key": f.key, "name": f.name, "zone": f.zone, "description": f.description,
                    "interactions": list(f.interactions), "contents": list(f.contents),
                    "hidden": f.hidden, "notice": f.notice, "locked": f.locked, "gates": f.gates,
                    "note": f.note, "state": dict(f.state)}

        def pres_d(p):
            return {"key": p.key, "name": p.name, "zone": p.zone, "kind": p.kind,
                    "disposition": p.disposition, "awareness": p.awareness, "hidden": p.hidden,
                    "notice": p.notice, "note": p.note, "follows_pc": p.follows_pc,
                    "combatant": p.combatant.to_dict() if p.combatant else None}

        return {"key": self.key, "name": self.name, "kind": self.kind, "pc_zone": self.pc_zone,
                "hooks": list(self.hooks), "flags": dict(self.flags),
                "zones": {k: zone_d(z) for k, z in self.zones.items()},
                "features": {k: feat_d(f) for k, f in self.features.items()},
                "presences": {k: pres_d(p) for k, p in self.presences.items()}}

    @classmethod
    def from_dict(cls, d: dict) -> "Scene":
        zones = {k: SceneZone(z["key"], z["name"], z.get("description", ""),
                              tuple(z.get("adjacent", ())), z.get("cover", "none"),
                              z.get("elevation", 0), z.get("is_exit", False), z.get("mood", ""),
                              z.get("hazard", ""))
                 for k, z in d.get("zones", {}).items()}
        features = {k: Feature(f["key"], f["name"], f["zone"], f.get("description", ""),
                               tuple(f.get("interactions", ())), tuple(f.get("contents", ())),
                               f.get("hidden", False), f.get("notice", "easy"), f.get("locked", False),
                               f.get("gates", ""), f.get("note", ""), dict(f.get("state", {})))
                    for k, f in d.get("features", {}).items()}
        presences = {}
        for k, p in d.get("presences", {}).items():
            comb = Combatant.from_dict(p["combatant"]) if p.get("combatant") else None
            presences[k] = Presence(p["key"], p["name"], p["zone"], p.get("kind", "npc"),
                                    p.get("disposition", "neutral"), p.get("awareness", "unaware"),
                                    p.get("hidden", False), p.get("notice", "moderate"), comb, None,
                                    p.get("note", ""), p.get("follows_pc", False))
        return cls(d["key"], d["name"], d.get("kind", "site"), zones, features, presences,
                   d.get("pc_zone", ""), tuple(d.get("hooks", ())), dict(d.get("flags", {})))
