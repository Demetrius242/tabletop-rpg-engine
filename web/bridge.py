from __future__ import annotations

import json
import queue
import re
import threading

from engine import addons as _addons
from engine import events as E
from engine.engine import ExplorationEngine
from engine.llm import FakeLLMClient
from web.catalog import character_view

_SENTINEL = object()

_BAND_LABEL = {"critical": "critical success", "exceptional": "great success", "success": "success",
               "marginal": "narrow success", "failure": "failure", "botch": "critical failure"}


def _title(s: str) -> str:
    return (s or "").replace("_", " ").strip().title()


def serialize_event(ev, party: set) -> dict:
    if isinstance(ev, E.Narration):
        return {"kind": "narration", "text": ev.text}
    if isinstance(ev, E.StoryBeat):
        return {"kind": "narration", "text": ev.text, "story": True}
    if isinstance(ev, E.TaskUpdated):
        return {"kind": "story", "style": "story", "task": ev.task, "state": ev.state,
                "text": f"◉ {ev.summary or ev.task} — {ev.state}"}
    if isinstance(ev, E.EventTransition):
        return {"kind": "story", "style": "story", "to": ev.to_event, "title": ev.title,
                "text": f"— {ev.title} —"}
    if isinstance(ev, E.SessionEnd):
        return {"kind": "session_end", "text": ev.reason}
    if isinstance(ev, E.Menu):
        return {"kind": "menu", "text": ev.prompt, "options": list(ev.options)}
    if isinstance(ev, E.SystemMessage):
        return {"kind": "log", "cat": "system", "style": "system", "text": ev.text}
    if isinstance(ev, E.StateDelta):
        return {"kind": "log", "cat": "state", "style": "muted", "text": ev.summary,
                "changes": ev.changes}
    if isinstance(ev, E.CheckResolved):
        style = ("crit-success" if ev.band == "critical" else "crit-fail" if ev.band == "botch"
                 else "check-success" if ev.success else "check-fail")
        return {"kind": "log", "cat": "check", "style": style, "skill": ev.skill, "band": ev.band,
                "success": ev.success, "difficulty": ev.difficulty,
                "text": f"{_title(ev.skill)} check \u2014 {_BAND_LABEL.get(ev.band, ev.band)}"}
    if isinstance(ev, E.ItemGained):
        verb = "Lost" if ev.removed else "Found"
        return {"kind": "log", "cat": "item", "style": f"item rarity-{ev.rarity}", "rarity": ev.rarity,
                "name": ev.name, "text": f"{verb}: {ev.name}"}
    if isinstance(ev, E.Healed):
        amt = f" {ev.amount} HP" if ev.amount else (f" {ev.levels} levels" if ev.levels else "")
        src = f" ({ev.source})" if ev.source else ""
        return {"kind": "log", "cat": "heal", "style": "heal", "name": ev.name, "amount": ev.amount,
                "text": f"{ev.name} recovers{amt}{src}"}
    if isinstance(ev, E.AttackResolved):
        to_party = ev.defender in party
        if ev.crit and ev.hit:
            style = "crit-success" if ev.attacker in party else "crit-fail"
        elif ev.crit and not ev.hit:
            style = "crit-fail" if ev.attacker in party else "muted"
        elif ev.hit and to_party:
            style = "damage"
        elif ev.hit:
            style = "attack-hit"
        else:
            style = "attack-miss"
        verb = "crits" if (ev.crit and ev.hit) else ("hits" if ev.hit else "misses")
        text = f"{ev.attacker} {verb} {ev.defender}"
        if ev.hit and ev.damage:
            text += f" for {ev.damage}"
        if ev.defeated:
            text += f" \u2014 {ev.defender} falls"
        return {"kind": "log", "cat": "attack", "style": style, "attacker": ev.attacker,
                "defender": ev.defender, "hit": ev.hit, "crit": ev.crit, "damage": ev.damage,
                "defeated": ev.defeated, "to_party": to_party, "text": text}
    if isinstance(ev, E.CombatStarted):
        return {"kind": "log", "cat": "combat", "style": "combat",
                "text": "\u2694 Combat begins \u2014 " + ", ".join(ev.order), "order": ev.order}
    if isinstance(ev, E.CombatEnded):
        return {"kind": "log", "cat": "combat", "style": "combat",
                "text": f"Combat ends \u2014 {ev.victor} prevail", "victor": ev.victor}
    if isinstance(ev, E.TurnStarted):
        return {"kind": "log", "cat": "turn", "style": "muted", "text": f"\u2014 {ev.name}'s turn \u2014",
                "name": ev.name, "side": ev.side}
    if isinstance(ev, E.Moved):
        prov = " (provoking)" if ev.provoked else ""
        return {"kind": "log", "cat": "move", "style": "muted",
                "text": f"{ev.name} moves to {_title(ev.to_zone)}{prov}"}
    if isinstance(ev, E.Fled):
        return {"kind": "log", "cat": "flee", "style": "info", "text": f"{ev.name} flees the fight"}
    if isinstance(ev, E.Defended):
        return {"kind": "log", "cat": "defend", "style": "muted", "text": f"{ev.name} guards"}
    if isinstance(ev, E.MoraleBroke):
        return {"kind": "log", "cat": "morale", "style": "info", "text": f"{ev.name} {ev.outcome}"}
    if isinstance(ev, E.OrderIssued):
        tail = "" if ev.delivered else " (unheard)"
        tgt = f" \u2192 {ev.target}" if ev.target else ""
        return {"kind": "log", "cat": "order", "style": "muted",
                "text": f"{ev.by} orders {ev.to}: {ev.directive}{tgt}{tail}"}
    if isinstance(ev, E.SocialResolved):
        tail = "" if ev.delivered else " (unheard)"
        return {"kind": "log", "cat": "social", "style": "info",
                "text": f"{ev.by} {ev.mode}s {ev.target}: {ev.effect or ev.band}{tail}"}
    if isinstance(ev, E.CharacterCreated):
        return {"kind": "log", "cat": "system", "style": "system", "text": ev.summary or ev.name}
    if isinstance(ev, E.GenderShift):
        return {"kind": "log", "cat": "gender", "style": "info",
                "text": f"{ev.name}: gender {ev.before} → {ev.after}" +
                        (f" (settling {ev.dissonance_rests} rests)" if ev.dissonance_rests else "")}
    for fn in _addons.registered("web.event"):
        msg = fn(ev, party)
        if msg is not None:
            return msg
    text = getattr(ev, "text", None) or type(ev).__name__
    return {"kind": "log", "cat": "event", "style": "muted", "text": str(text)}


_ATTACK_WORDS = ("attack", "strike", "hit", "kill", "slay", "stab", "slash", "shoot", "swing",
                 "charge", "assault", "lunge", "fight", "engage", "cut down")
_FLEE_WORDS = ("flee", "run", "escape", "retreat from", "get out", "withdraw")
_DEFEND_WORDS = ("defend", "dodge", "guard", "block", "brace", "parry")
_MEND_WORDS = ("mend", "bandage", "patch")
_PASS_WORDS = ("pass", "wait", "hold", "do nothing", "ready")


def _find_name(text: str, names: list) -> str:
    t = text.lower()
    for n in names:
        if n and n.lower() in t:
            return n
    for n in names:
        first = n.split()[0].lower() if n else ""
        if first and first in t.split():
            return n
    return ""


class WebFakeClient(FakeLLMClient):

    def __init__(self, **kw):
        super().__init__(**kw)
        self.last_user = ""

    def complete(self, prompt, sampling, grammar=None):
        from engine.llm import Generation
        self.calls.append(type("_C", (), {"prompt": prompt, "sampling": sampling, "grammar": grammar}))
        if grammar is None:
            return Generation(self.default_text)
        user = (self.last_user or "").lower()
        if "COMBAT action" in prompt:
            return Generation(self._combat_json(prompt, user))
        return Generation(self._intent_json(user))

    def _intent_json(self, user: str) -> str:
        if any(w in user for w in _ATTACK_WORDS):
            return '{"intent": "combat_start", "detail": ""}'
        return '{"intent": "dialogue", "detail": ""}'

    def _combat_json(self, prompt: str, user: str) -> str:
        def lst(label):
            m = re.search(label + r":\s*(.+?)\.", prompt)
            return [s.strip() for s in m.group(1).split(",")] if m else []
        enemies, allies, zones = lst("Enemies"), lst("Allies"), lst("Adjacent zones")
        if any(w in user for w in _FLEE_WORDS):
            return '{"action": "flee"}'
        if any(w in user for w in _DEFEND_WORDS):
            return '{"action": "defend"}'
        if any(w in user for w in _MEND_WORDS):
            return '{"action": "mend"}'
        if any(w in user for w in _PASS_WORDS):
            return '{"action": "pass"}'
        if ("intimidate" in user or "threaten" in user) and enemies:
            return json.dumps({"action": "social", "mode": "intimidate",
                               "target": _find_name(user, enemies) or enemies[0]})
        if ("taunt" in user or "provoke" in user) and enemies:
            return json.dumps({"action": "social", "mode": "taunt",
                               "target": _find_name(user, enemies) or enemies[0]})
        if ("retreat" in user or "disengage" in user or "fall back" in user) and zones:
            return json.dumps({"action": "retreat", "zone": _find_name(user, zones) or zones[0]})
        if any(w in user for w in ("move", "go ", "advance", "approach", "climb")) and zones:
            return json.dumps({"action": "move", "zone": _find_name(user, zones) or zones[0]})
        if "order" in user and allies:
            directive = next((d for d in ("focus", "defend_me", "fall_back", "hold")
                              if d.replace("_", " ") in user or d in user), "hold")
            return json.dumps({"action": "order", "ally": _find_name(user, allies) or allies[0],
                               "directive": directive})
        if enemies:
            return json.dumps({"action": "attack", "target": _find_name(user, enemies) or enemies[0]})
        return '{"action": "pass"}'


_FAKE_TEXT = ("The torchlight wavers over old stone. The air is cold and close, and the quiet "
              "feels like it is listening. You take a breath and steady yourself.")


def make_client(connection: dict | None = None):
    from engine.llm import client_from_connection
    return client_from_connection(connection, fake=WebFakeClient(default_text=_FAKE_TEXT))


def apply_saved_sampling(client) -> bool:
    if not hasattr(client, "set_overrides"):
        return False
    from web.catalog import load_llama
    s = load_llama()
    client.set_overrides(
        temperature=s.get("temperature"), top_p=s.get("top_p"), max_tokens=s.get("max_tokens"),
        top_k=s.get("top_k"), min_p=s.get("min_p"), repeat_penalty=s.get("repeat_penalty"),
        frequency_penalty=s.get("frequency_penalty"), presence_penalty=s.get("presence_penalty"),
        seed=s.get("seed"))
    return True


def _saved_system_prompt() -> str:
    from web.catalog import load_llama
    return str(load_llama().get("system_prompt", "") or "")


class WebPresenter:
    def __init__(self, ws, q: "queue.Queue", party: set, client):
        self.ws = ws
        self.q = q
        self.party = party
        self.client = client

    def emit(self, event) -> None:
        msg = serialize_event(event, self.party)
        msg["type"] = "event"
        self.ws.send_text(json.dumps(msg))

    def read_action(self) -> str:
        try:
            self.ws.send_text(json.dumps({"type": "ready"}))
        except Exception:
            pass
        item = self.q.get()
        if item is _SENTINEL:
            raise EOFError
        if hasattr(self.client, "last_user"):
            self.client.last_user = item
        return item


class Session:
    def __init__(self, ws, *, ruleset_key, setting_key, story_key, rs, state, scene, companions,
                 connection=None):
        self.ws = ws
        self.ruleset_key = ruleset_key
        self.setting_key = setting_key
        self.story_key = story_key
        self.rs = rs
        self.state = state
        self.scene = scene
        self.companions = companions
        self.party_names = {state.pc.name} | {c.name for c in companions}
        self.queue: "queue.Queue" = queue.Queue()
        self.connection = connection or {"kind": "canned"}
        self.client = make_client(self.connection)
        apply_saved_sampling(self.client)
        self.presenter = WebPresenter(ws, self.queue, self.party_names, self.client)
        if scene is None and companions:
            state.flags["party_companions"] = companions
        self.engine = ExplorationEngine(client=self.client, presenter=self.presenter,
                                        state=state, ruleset=rs, scene=scene,
                                        narrator_override=_saved_system_prompt())
        adv = rs.build_adventure(story_key) if hasattr(rs, "build_adventure") else None
        if adv is not None:
            from engine.story import StoryController
            blob = state.flags.get("story")
            self.engine.story = (StoryController.hydrate(adv, self.engine, blob) if blob
                                 else StoryController.start(adv, self.engine))
        self.thread: threading.Thread | None = None

    def reconnect(self, connection: dict) -> None:
        self.connection = connection
        client = make_client(connection)
        apply_saved_sampling(client)
        self.client = client
        self.engine.client = client
        self.presenter.client = client
        self.engine.narrator_override = _saved_system_prompt()

    def journal(self) -> dict:
        return self.engine.story.journal() if self.engine.story is not None else {}

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        try:
            self.engine.run()
        except EOFError:
            pass
        except Exception as exc:
            try:
                self.ws.send_text(json.dumps({"type": "event", "kind": "log", "cat": "error",
                                              "style": "crit-fail", "text": f"[engine error] {exc}"}))
            except Exception:
                pass
        finally:
            try:
                self.ws.send_text(json.dumps({"type": "ended"}))
            except Exception:
                pass

    def submit(self, text: str) -> None:
        self.queue.put(text)

    def stop(self) -> None:
        self.queue.put(_SENTINEL)

    def party_views(self) -> list:
        views = [character_view(self.rs, self.state.pc, is_party_leader=True)]
        views += [character_view(self.rs, c) for c in self.companions]
        return views
