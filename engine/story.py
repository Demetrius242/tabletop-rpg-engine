from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field

from .difficulty import DifficultyBand
from .events import EventTransition, ItemGained, StoryBeat, TaskUpdated
from .llm import DETERMINISTIC
from .scene import Presence


@dataclass(frozen=True)
class NpcPhase:
    key: str
    summary: str
    skill: str = ""
    difficulty: str = "medium"
    advance_on: str = "success"
    cue: str = ""


@dataclass(frozen=True)
class NpcTask:
    key: str
    npc: str
    summary: str
    phases: tuple = ()
    cadence: str = "action"
    start_when: object = True
    abort_when: object = False
    on_complete: tuple = ()


@dataclass(frozen=True)
class Outcome:
    key: str
    when: object
    effects: tuple = ()
    summary: str = ""


@dataclass(frozen=True)
class Task:
    key: str
    summary: str = ""
    actor: str = "party"
    outcomes: tuple = ()
    repeatable: bool = False
    hidden: bool = False


@dataclass(frozen=True)
class Transition:
    when: object
    to: str


@dataclass(frozen=True)
class StoryEvent:
    key: str
    title: str
    intro_cue: str = ""
    scene_key: str = ""
    entry_effects: tuple = ()
    tasks: tuple = ()
    npc_tasks: tuple = ()
    transitions: tuple = ()
    tags: tuple = ()


@dataclass(frozen=True)
class Adventure:
    key: str
    title: str
    start_event: str
    events: dict = field(default_factory=dict)
    party: tuple = ()
    metadata: dict = field(default_factory=dict)


_BAND_ORDER = ["botch", "failure", "marginal", "success", "exceptional", "critical"]
_ALARM_ORDER = ["unaware", "suspicious", "alert"]
_call_cache: dict = {}


def _resolve_call(path: str):
    fn = _call_cache.get(path)
    if fn is None:
        mod, _, name = path.rpartition(".")
        fn = getattr(importlib.import_module(mod), name)
        _call_cache[path] = fn
    return fn


def _rank(order: list, value, default=0) -> int:
    try:
        return order.index(value)
    except ValueError:
        return default


@dataclass
class StoryContext:
    scene_key: str = ""
    zone: str = ""
    visited: frozenset = frozenset()
    flags: dict = field(default_factory=dict)
    defeated: frozenset = frozenset()
    present: frozenset = frozenset()
    inventory: frozenset = frozenset()
    last_skill: str = ""
    last_band: str = ""
    last_success: bool = False
    tag: str = ""
    task_states: dict = field(default_factory=dict)
    npc_progress: dict = field(default_factory=dict)
    alarm: str = "unaware"
    victor: str = ""
    actor: str = ""
    scene: object = None


def evaluate(cond, ctx: StoryContext) -> bool:
    if cond is None or cond is False:
        return False
    if cond is True:
        return True
    if isinstance(cond, list):
        return all(evaluate(c, ctx) for c in cond)
    if not isinstance(cond, dict):
        return bool(cond)
    if not cond:
        return True
    if "all" in cond:
        return all(evaluate(c, ctx) for c in cond["all"])
    if "any" in cond:
        return any(evaluate(c, ctx) for c in cond["any"])
    if "not" in cond:
        return not evaluate(cond["not"], ctx)
    if "at" in cond:
        return ctx.zone == cond["at"]
    if "in_scene" in cond:
        return ctx.scene_key == cond["in_scene"]
    if "visited" in cond:
        return cond["visited"] in ctx.visited
    if "flag" in cond:
        name = cond["flag"]
        return ctx.flags.get(name) == cond["eq"] if "eq" in cond else bool(ctx.flags.get(name))
    if "defeated" in cond:
        return cond["defeated"] in ctx.defeated
    if "present" in cond:
        key = cond["present"]
        if key not in ctx.present:
            return False
        p = ctx.scene.presence(key) if ctx.scene is not None else None
        if "zone" in cond:
            return p is not None and p.zone == cond["zone"]
        if cond.get("in_party_zone"):
            return p is not None and p.zone == ctx.zone
        return True
    if "has_item" in cond:
        return cond["has_item"] in ctx.inventory
    if "check" in cond:
        if ctx.last_skill != cond["check"]:
            return False
        if "band_at_least" in cond:
            return _rank(_BAND_ORDER, ctx.last_band, -1) >= _rank(_BAND_ORDER, cond["band_at_least"])
        if "band_is" in cond:
            return ctx.last_band == cond["band_is"]
        if "success" in cond:
            return ctx.last_success == bool(cond["success"])
        return bool(ctx.last_band)
    if "tag" in cond:
        return ctx.tag == cond["tag"]
    if "task" in cond:
        state = cond.get("state")
        if state == "done":
            return cond["task"] in ctx.task_states
        return ctx.task_states.get(cond["task"]) == state
    if "npc_task" in cond:
        prog = ctx.npc_progress.get(cond["npc_task"], {})
        if cond.get("done"):
            return bool(prog.get("done"))
        if "phase_at_least" in cond:
            return int(prog.get("phase", 0)) >= int(cond["phase_at_least"])
        return bool(prog)
    if "alarm" in cond:
        return _rank(_ALARM_ORDER, ctx.alarm) >= _rank(_ALARM_ORDER, cond["alarm"])
    if "awareness" in cond:
        p = ctx.scene.presence(cond["awareness"]) if ctx.scene is not None else None
        cur = getattr(p, "awareness", "unaware") if p is not None else "unaware"
        return _rank(_ALARM_ORDER, cur) >= _rank(_ALARM_ORDER, cond.get("at_least", "alert"))
    if "victor" in cond:
        return ctx.victor == cond["victor"]
    if "call" in cond:
        return bool(_resolve_call(cond["call"])(ctx))
    return False


def _first_obj(s: str) -> str:
    i, j = s.find("{"), s.rfind("}")
    return s[i:j + 1] if i != -1 and j != -1 and j > i else "{}"


def _story_grammar(tags: list) -> str:
    alts = " | ".join(f'"\\"{t}\\""' for t in tags + ["none"])
    return ('root ::= ws "{" ws "\\"tag\\"" ws ":" ws tag ws "}" ws\n'
            f'tag  ::= {alts}\n'
            'ws   ::= [ \\t\\n]*\n')


def _build_story_system(entries: list) -> str:
    lines = ["Classify what the player is trying to do right now. Reply with ONLY a JSON object "
             '{"tag": "..."} choosing exactly one tag:']
    for tag, desc, _ in entries:
        lines.append(f'"{tag}" = {desc}.')
    lines.append('"none" = none of the above / unclear.')
    return "\n".join(lines)


class StoryClassifier:

    def __init__(self, tags):
        self.entries = [(t, d, tuple(k)) for (t, d, k) in (tags or ())]
        self.tags = [t for t, _, _ in self.entries]
        self.system = _build_story_system(self.entries) if self.entries else ""
        self.grammar = _story_grammar(self.tags) if self.tags else ""

    def classify(self, client, builder, action: str) -> str:
        if not self.tags:
            return ""
        try:
            prompt = builder.build(system=self.system, history=None, user=action)
            raw = client.complete(prompt, DETERMINISTIC.with_stops(builder.stops),
                                  grammar=self.grammar).text
            tag = json.loads(_first_obj(raw)).get("tag")
            if tag in self.tags:
                return tag
        except Exception:
            pass
        return self._keyword(action)

    def _keyword(self, action: str) -> str:
        a = (action or "").lower()
        for tag, _, kws in self.entries:
            if any(k in a for k in kws):
                return tag
        return ""


class StoryController:
    def __init__(self, adventure: Adventure, engine):
        self.adv = adventure
        self.engine = engine
        self.current = adventure.start_event
        self.task_states: dict = {}
        self.npc_progress: dict = {}
        self.visited: set = set()
        self.objectives: list = []
        self.removed: set = set()
        self._companions: list = []
        self._classifier = StoryClassifier(())
        self._capture_companions()

    @classmethod
    def start(cls, adventure: Adventure, engine) -> "StoryController":
        return cls(adventure, engine)

    @classmethod
    def hydrate(cls, adventure: Adventure, engine, blob: dict) -> "StoryController":
        self = cls(adventure, engine)
        blob = blob or {}
        self.current = blob.get("current", adventure.start_event)
        self.task_states = dict(blob.get("task_states", {}))
        self.npc_progress = {k: dict(v) for k, v in blob.get("npc_progress", {}).items()}
        self.visited = set(blob.get("visited", ()))
        self.objectives = [dict(o) for o in blob.get("objectives", ())]
        self.removed = set(blob.get("removed", ()))
        ev = self.adv.events.get(self.current)
        self._classifier = StoryClassifier(ev.tags if ev else ())
        return self

    def to_dict(self) -> dict:
        return {"adventure": self.adv.key, "current": self.current,
                "task_states": dict(self.task_states),
                "npc_progress": {k: dict(v) for k, v in self.npc_progress.items()},
                "visited": sorted(self.visited), "objectives": [dict(o) for o in self.objectives],
                "removed": sorted(self.removed)}

    def _persist(self) -> None:
        self.engine.state.flags["story"] = self.to_dict()

    @property
    def _event(self) -> StoryEvent | None:
        return self.adv.events.get(self.current)

    def _emit(self, event) -> None:
        self.engine.presenter.emit(event)

    def _beat(self, text: str) -> None:
        if text:
            self._emit(StoryBeat(text=text, event_key=self.current))

    def _capture_companions(self) -> None:
        sc = self.engine.scene
        if sc is not None:
            comps = [p for p in sc.presences.values() if p.follows_pc and p.combatant is not None]
            if comps:
                self._companions = comps

    def _party_combatants(self) -> list:
        out = [self.engine.state.pc]
        out += [p.combatant for p in self._companions if p.combatant is not None]
        return out

    def _context(self, **overrides) -> StoryContext:
        sc = self.engine.scene
        rs = self.engine.ruleset
        defeated = set(self.removed)
        present = set()
        if sc is not None:
            for k, p in sc.presences.items():
                present.add(k)
                if p.combatant is not None and rs.is_defeated(p.combatant):
                    defeated.add(k)
        inv = set()
        for c in self._party_combatants():
            inv.update(c.sheet.get("inventory", []) or [])
        ctx = StoryContext(
            scene_key=sc.key if sc is not None else "",
            zone=sc.pc_zone if sc is not None else "",
            visited=frozenset(self.visited),
            flags=self.engine.state.flags,
            defeated=frozenset(defeated), present=frozenset(present), inventory=frozenset(inv),
            task_states=self.task_states, npc_progress=self.npc_progress,
            alarm=sc.alertness() if sc is not None else "unaware", scene=sc)
        for k, v in overrides.items():
            setattr(ctx, k, v)
        return ctx

    def _apply(self, effects, ctx: StoryContext) -> None:
        for eff in effects or ():
            self._apply_one(eff, ctx)

    def _apply_one(self, eff: dict, ctx: StoryContext) -> None:
        sc = self.engine.scene
        flags = self.engine.state.flags
        if "set_flag" in eff:
            flags[eff["set_flag"]] = eff.get("value", True)
        elif "clear_flag" in eff:
            flags.pop(eff["clear_flag"], None)
        elif "reveal" in eff and sc is not None:
            obj = sc.presence(eff["reveal"]) or sc.feature(eff["reveal"])
            if obj is not None:
                obj.hidden = False
        elif "set_disposition" in eff and sc is not None:
            p = sc.presence(eff["set_disposition"])
            if p is not None:
                p.disposition = eff["to"]
        elif "set_awareness" in eff and sc is not None:
            p = sc.presence(eff["set_awareness"])
            if p is not None:
                p.awareness = eff["to"]
        elif "raise_alarm" in eff and sc is not None:
            sc.raise_alarm(eff["raise_alarm"])
        elif "place" in eff and sc is not None:
            p = sc.presence(eff["place"])
            if p is not None:
                p.zone = eff.get("zone", p.zone)
                p.hidden = False
        elif "remove" in eff:
            if sc is not None:
                sc.presences.pop(eff["remove"], None)
            self.removed.add(eff["remove"])
        elif "grant_item" in eff:
            key = eff["grant_item"]
            pc = self.engine.state.pc
            self.engine.ruleset.grant_item(pc, key)
            info = self.engine.ruleset.item_info(key) if hasattr(self.engine.ruleset, "item_info") else None
            self._emit(ItemGained(owner=pc.name, key=key, name=getattr(info, "name", key),
                                  rarity=getattr(info, "rarity", "common")))
        elif "goto" in eff:
            self.enter_event(eff["goto"])
        elif "cue" in eff:
            self._beat(eff["cue"])
        elif "objective" in eff:
            self._set_objective(eff["objective"], eff.get("state", "add"))
        elif "start_npc_task" in eff:
            self.npc_progress.setdefault(eff["start_npc_task"],
                                         {"phase": 0, "done": False, "active": True})
        elif "complete_task" in eff:
            self.task_states[eff["complete_task"]] = "done"
            self._emit(TaskUpdated(task=eff["complete_task"], state="done"))
        elif "call" in eff:
            _resolve_call(eff["call"])(self, ctx)

    def _set_objective(self, text: str, state: str) -> None:
        for o in self.objectives:
            if o["text"] == text:
                o["state"] = "complete" if state == "complete" else o["state"]
                return
        self.objectives.append({"text": text, "state": "complete" if state == "complete" else "open"})

    def on_start(self) -> None:
        self.enter_event(self.current, initial=True)

    def enter_event(self, key: str, *, initial: bool = False) -> None:
        ev = self.adv.events.get(key)
        if ev is None:
            return
        prev = "" if initial else self.current
        self.current = key
        self._capture_companions()
        if ev.scene_key:
            scene = self.engine.ruleset.build_scene(ev.scene_key)
            if scene is not None:
                for p in self._companions:
                    scene.presences[p.key] = Presence(
                        p.key, p.name, scene.pc_zone, kind="npc", disposition="friendly",
                        combatant=p.combatant, follows_pc=True, note=p.note)
                self.engine.scene = scene
                z = scene.here()
                if z is not None:
                    self.engine.state.location = z.name
                self.visited = {scene.pc_zone}
        else:
            self.engine.scene = None
        self._classifier = StoryClassifier(ev.tags)
        self._emit(EventTransition(from_event=prev, to_event=key, title=ev.title))
        self._beat(ev.intro_cue)
        ctx = self._context()
        self._apply(ev.entry_effects, ctx)
        for nt in ev.npc_tasks:
            prog = self.npc_progress.setdefault(nt.key, {"phase": 0, "done": False, "active": False})
            if not prog["done"] and not prog["active"] and evaluate(nt.start_when, ctx):
                prog["active"] = True
        self._persist()

    def _advance_tasks(self, ctx: StoryContext) -> None:
        ev = self._event
        if ev is None:
            return
        ev_key = self.current
        for task in ev.tasks:
            if task.key in self.task_states and not task.repeatable:
                continue
            for oc in task.outcomes:
                if evaluate(oc.when, ctx):
                    self.task_states[task.key] = oc.key
                    self._emit(TaskUpdated(task=task.key, state=oc.key,
                                           summary=oc.summary or task.summary, actor=task.actor))
                    self._apply(oc.effects, ctx)
                    break
            if self.current != ev_key:
                return

    def _tick_npc_tasks(self, cadence: str, ctx: StoryContext) -> None:
        ev = self._event
        if ev is None:
            return
        for nt in ev.npc_tasks:
            if nt.cadence != cadence:
                continue
            prog = self.npc_progress.setdefault(nt.key, {"phase": 0, "done": False, "active": False})
            if prog["done"]:
                continue
            if evaluate(nt.abort_when, ctx):
                prog["active"] = False
                continue
            if not prog["active"]:
                if not evaluate(nt.start_when, ctx):
                    continue
                prog["active"] = True
            if cadence == "combat_turn" and not self._is_actor(nt, ctx.actor):
                continue
            self._advance_npc_phase(nt, prog, ctx)

    def _is_actor(self, nt: NpcTask, actor: str) -> bool:
        sc = self.engine.scene
        p = sc.presence(nt.npc) if sc is not None else None
        return p is not None and p.combatant is not None and p.combatant.name == actor

    def _advance_npc_phase(self, nt: NpcTask, prog: dict, ctx: StoryContext) -> None:
        idx = prog["phase"]
        if idx >= len(nt.phases):
            return
        phase = nt.phases[idx]
        advance = True
        if phase.skill and phase.advance_on != "always":
            sc = self.engine.scene
            p = sc.presence(nt.npc) if sc is not None else None
            if p is None or p.combatant is None:
                return
            rs = self.engine.ruleset
            diff = rs.difficulty_for_band(DifficultyBand(phase.difficulty))
            advance = rs.resolve_check(p.combatant, phase.skill, diff).success
        if not advance:
            return
        prog["phase"] = idx + 1
        self._beat(phase.cue)
        self._emit(TaskUpdated(task=nt.key, state="advanced", summary=phase.summary, actor=nt.npc))
        if prog["phase"] >= len(nt.phases):
            prog["done"] = True
            prog["active"] = False
            self._apply(nt.on_complete, ctx)
            self._emit(TaskUpdated(task=nt.key, state="done", summary=nt.summary, actor=nt.npc))

    def _check_transitions(self, ctx: StoryContext) -> None:
        ev = self._event
        if ev is None:
            return
        for tr in ev.transitions:
            if evaluate(tr.when, ctx):
                self.enter_event(tr.to)
                return

    def classify_tag(self, user: str) -> str:
        return self._classifier.classify(self.engine.client, self.engine.builder, user)

    def on_action(self, user: str, intent, check_outcome, tag: str) -> None:
        ovr = {"tag": tag or ""}
        if check_outcome is not None:
            ovr.update(last_skill=getattr(intent, "skill", ""), last_band=check_outcome.band.value,
                       last_success=check_outcome.success)
        ctx = self._context(**ovr)
        self._advance_tasks(ctx)
        self._tick_npc_tasks("action", self._context(**ovr))
        self._check_transitions(self._context(**ovr))
        self._persist()

    def on_move(self, zone: str) -> None:
        self.visited.add(zone)
        ctx = self._context()
        self._advance_tasks(ctx)
        self._tick_npc_tasks("action", self._context())
        self._check_transitions(self._context())
        self._persist()

    def on_short_rest(self) -> None:
        self._rest_tick("short_rest")

    def on_long_rest(self) -> None:
        self._rest_tick("long_rest")

    def _rest_tick(self, cadence: str) -> None:
        self._tick_npc_tasks(cadence, self._context())
        self._advance_tasks(self._context())
        self._check_transitions(self._context())
        self._persist()

    def on_combat_turn(self, actor: str) -> None:
        self._tick_npc_tasks("combat_turn", self._context(actor=actor))
        self._persist()

    def on_combat_round(self) -> None:
        self._tick_npc_tasks("combat_round", self._context())
        self._persist()

    def on_combat_end(self, victor: str) -> None:
        ctx = self._context(victor=victor)
        self._advance_tasks(ctx)
        self._check_transitions(self._context(victor=victor))
        self._persist()

    def journal(self) -> dict:
        ev = self._event
        objectives = []
        if ev is not None:
            for task in ev.tasks:
                if task.hidden:
                    continue
                state = self.task_states.get(task.key, "open")
                objectives.append({"key": task.key, "text": task.summary, "state": state,
                                   "done": state != "open"})
        objectives += [{"key": "", "text": o["text"], "state": o["state"],
                        "done": o["state"] == "complete"} for o in self.objectives]
        npc = []
        if ev is not None:
            for nt in ev.npc_tasks:
                prog = self.npc_progress.get(nt.key, {})
                npc.append({"key": nt.key, "summary": nt.summary,
                            "phase": int(prog.get("phase", 0)), "total": len(nt.phases),
                            "done": bool(prog.get("done")), "active": bool(prog.get("active"))})
        return {"adventure": self.adv.title, "chapter": ev.title if ev else "",
                "event": self.current, "objectives": objectives, "npc_tasks": npc}
