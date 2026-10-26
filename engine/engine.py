from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from .classify import Classifier, Intent, IntentType
from .difficulty import CheckContext, DifficultyAssessor
from .events import (CheckResolved, Healed, HumanityShift, ItemGained, Narration, Presenter,
                     SessionEnd, StateDelta, SystemMessage)
from .llm import CREATIVE, LLMClient, PromptBuilder
from .morality import MoralClassifier
from . import narration
from .ruleset import Ruleset
from .scene import Scene
from .state import GameState, save_game

NARRATOR_SYSTEM = (
    "You are the narrator of a text RPG, writing in second person, present tense. "
    "Keep it to one or two vivid, concise paragraphs.\n"
    "Hard rules:\n"
    "- When a RESULT is given to you, narrate exactly that result; never change it "
    "or decide a different outcome.\n"
    "- Otherwise narrate only what follows from the player's action, and never "
    "invent consequences: no injuries, deaths, items gained or lost, or doors "
    "locking unless you are told they happened.\n"
    "- Refer to the player's condition only in the qualitative terms provided. "
    "Never mention numbers, statistics, dice, or hit points.\n"
    "- Items: a character may only use, wield, or give an item they actually carry "
    "(it appears in their inventory) -- the SOLE exception is an item just found in "
    "the current scene and named to you. Never invent, conjure, or hand out gear "
    "that has not been established.\n"
    "- Companions present are the player's established allies and followers: they "
    "already travel together by the player's side. Voice them in character "
    "(including any wariness or friction that fits them), but never have them ask "
    "to join the party, offer to travel together, or recruit the player -- that is "
    "already settled.\n"
    "- Do not speak for the player or put words in their mouth."
)

BAND_NARRATION = {
    "critical": "a stunning, critical success -- markedly better than hoped",
    "exceptional": "a clear, strong success",
    "success": "a success",
    "marginal": "a success, but only barely -- and it costs something",
    "failure": "a failure",
    "botch": "a fumbled failure that makes the situation worse",
}


@dataclass
class ExplorationEngine:
    client: LLMClient
    presenter: Presenter
    state: GameState
    ruleset: Ruleset
    builder: PromptBuilder = field(default_factory=PromptBuilder)
    classifier: Classifier | None = None
    assessor: DifficultyAssessor = field(default_factory=DifficultyAssessor)
    save_path: str = "savegame.json"
    scene: Scene | None = None
    story: object | None = None
    narrator_override: str = ""
    running: bool = field(default=False, init=False)

    def __post_init__(self):
        if self.classifier is None:
            self.classifier = Classifier.for_ruleset(self.ruleset)
        self._moral_classifier: MoralClassifier | None = None
        self._last_check = None

    def run(self) -> None:
        self.running = True
        if self.story is not None:
            self.story.on_start()
        self._narrate_scene()
        while self.running:
            try:
                user = self.presenter.read_action()
            except (EOFError, KeyboardInterrupt):
                self._end("You set the story aside.")
                break
            if not user.strip():
                continue
            special = self.ruleset.try_special_action(self.state.pc, user)
            if special is not None:
                self._handle_special(special)
                continue
            if self._try_use_item(user):
                continue
            if self.scene is not None and self._scene_action(user):
                continue
            intent = self.classifier.classify(self.client, self.builder, user)
            self._route(intent, user)

    def _handle_special(self, special) -> None:
        if special.event is not None:
            self.presenter.emit(special.event)
        if special.kind == "help":
            self.presenter.emit(SystemMessage(special.message))
            return
        if special.cue:
            self._narrate(f"[{special.cue} Narrate the moment vividly in second person, "
                          f"in the fiction.]", as_player=False)
        if (self.running and special.moral_text
                and self.ruleset.morality() is not None):
            self._moral_check(special.moral_text)

    def _route(self, intent: Intent, user: str) -> None:
        self._last_check = None
        if intent.type is IntentType.OOC_COMMAND:
            self._handle_ooc(user)
        elif intent.type is IntentType.CHECK_ACTION:
            self._resolve_check(intent, user)
        elif intent.type is IntentType.COMBAT_START:
            self._start_combat(user)
        elif intent.type is IntentType.TRIVIAL_ACTION:
            self._apply_trivial(intent)
            self._narrate(user)
        else:
            register = self.ruleset.register_for_text(user, self.state.pc) or None
            self._narrate(user, mode="dialogue", register_key=register)
        if (self.running and intent.type is not IntentType.OOC_COMMAND
                and self.ruleset.morality() is not None):
            self._moral_check(user)
        if self.running and self.story is not None and intent.type is not IntentType.OOC_COMMAND:
            tag = self.story.classify_tag(user)
            self.story.on_action(user, intent, self._last_check, tag)

    def _moral_check(self, user: str) -> None:
        morality = self.ruleset.morality()
        if morality is None:
            return
        if self._moral_classifier is None:
            self._moral_classifier = MoralClassifier(morality)
        severity = self._moral_classifier.severity(self.client, self.builder, user)
        result = self.ruleset.degeneration_check(self.state.pc, severity)
        if not result.get("checked"):
            return
        self.presenter.emit(HumanityShift(
            name=self.state.pc.name, before=result["before"], after=result["after"],
            lost=result["lost"], derangement=result.get("derangement", False),
            trait=result.get("trait", morality.name)))
        if result["lost"]:
            worse = " Something deeper fractures." if result.get("derangement") else ""
            block = (f"{self._state_view()}\n\n[An act of cruelty tests what remains of "
                     f"your {morality.name}. RESULT: it erodes -- a little more of the "
                     f"person you were slips into the dark.{worse} Narrate that inner "
                     f"moment briefly, in second person, with no numbers.]")
        else:
            block = (f"{self._state_view()}\n\n[An act of cruelty tests your "
                     f"{morality.name}. RESULT: remorse holds and the line stays, for "
                     f"now. Narrate that inner moment briefly, in second person, with "
                     f"no numbers.]")
        self._emit_narration(list(self.state.recent()), block)

    def _start_combat(self, user: str) -> None:
        if self.scene is not None and not self.state.flags.get("present_enemies"):
            handoff = self.scene.to_combat(self.state.pc)
            if not handoff["enemies"]:
                self._narrate(user)
                return
            self.state.flags["present_enemies"] = handoff["enemies"]
            self.state.flags["party_companions"] = handoff["companions"]
            self.state.flags["combat_arena"] = handoff["arena"]
            if handoff["surprise"]:
                self.state.flags["surprise"] = handoff["surprise"]
        enemies = list(self.state.flags.get("present_enemies") or [])
        if not enemies:
            self._narrate(user)
            return
        self._differentiate_enemies(enemies)
        from .combat import CombatController
        companions = list(self.state.flags.get("party_companions") or [])
        arena = self.state.flags.get("combat_arena")
        controller = CombatController(
            self.client, self.presenter, self.state, self.ruleset,
            enemies=enemies, companions=companions, arena=arena, builder=self.builder,
            story=self.story,
            narrator_override=self.narrator_override)
        victor = controller.run()
        self.state.flags.pop("present_enemies", None)
        self.state.flags.pop("combat_arena", None)
        self.state.flags.pop("surprise", None)
        self.state.flags.pop("enemy_group_note", None)
        if self.scene is not None:
            self._prune_scene_after_combat()
        if self.story is not None:
            self.story.on_combat_end(victor)
        if victor == "enemies" or self.ruleset.is_defeated(self.state.pc):
            self._end("You have fallen.")

    def _prune_scene_after_combat(self) -> None:
        for key in [k for k, p in self.scene.presences.items()
                    if p.kind == "enemy" and p.combatant is not None
                    and self.ruleset.is_defeated(p.combatant)]:
            del self.scene.presences[key]

    def _differentiate_enemies(self, enemies) -> None:
        groups: dict = defaultdict(list)
        for e in enemies:
            key = re.sub(r"\s*#?\d+$", "", getattr(e, "name", "")).strip().lower() or "foe"
            groups[key].append(e)
        seed_base = sum(ord(c) for c in (self.state.location or "x"))
        notes = []
        for i, (key, members) in enumerate(groups.items()):
            if len(members) < 2:
                continue
            rows = narration.differentiate(members, seed=seed_base + i)
            for e, row in zip(members, rows):
                e.sheet["distinct_look"] = row["appearance"]
                e.sheet["distinct_manner"] = row["manner"]
            notes.append(narration.group_brief(members, role=f"{key}s", seed=seed_base + i))
        if notes:
            self.state.flags["enemy_group_note"] = "\n\n".join(notes)
        else:
            self.state.flags.pop("enemy_group_note", None)

    def _resolve_check(self, intent: Intent, user: str) -> None:
        actor = self.state.pc
        ctx = self._check_context(actor, intent, user)
        band, reasons = self.assessor.assess(intent.skill, ctx)
        difficulty = self.ruleset.difficulty_for_band(band)
        outcome = self.ruleset.resolve_check(actor, intent.skill, difficulty)
        self._last_check = outcome
        raw = dict(outcome.raw)
        raw["difficulty_reasons"] = reasons
        self.presenter.emit(CheckResolved(
            skill=intent.skill, band=outcome.band.value,
            success=outcome.success, difficulty=band.value, raw=raw))
        cue = BAND_NARRATION.get(outcome.band.value, "a result")
        block = (
            f"{self._state_view()}\n\n"
            f"Player attempts ({intent.skill}): {user}\n"
            f"Approach: {intent.approach or 'unspecified'}\n"
            f"RESULT (this happened -- narrate it, do not change it): {cue}."
        )
        history = list(self.state.recent())
        self.state.record("player", user)
        register = self.ruleset.narration_register(
            intent.skill, actor, approach=f"{intent.approach} {user}") or None
        self._emit_narration(history, block, register_key=register)

    def _check_context(self, actor, intent: Intent, user: str) -> CheckContext:
        scene = dict(self.state.flags.get("scene", {}))
        if self.scene is not None:
            scene.update(self.scene.check_factors())
        return CheckContext(
            approach=f"{intent.approach} {user}".strip(),
            actor_statuses=frozenset(actor.statuses),
            skill_tags=frozenset(self.ruleset.skill_tags(intent.skill)),
            impairment_delta=self.ruleset.situational_difficulty_delta(actor, intent.skill),
            lighting=scene.get("lighting"),
            footing=scene.get("footing"),
            target_alertness=scene.get("target_alertness"),
            has_proper_tools=scene.get("has_proper_tools"),
            time_pressure=bool(scene.get("time_pressure", False)),
        )

    def _apply_trivial(self, intent: Intent) -> None:
        note = intent.detail or "an action"
        self.state.flags.setdefault("recent_actions", []).append(note)
        self.presenter.emit(StateDelta(summary=f"noted: {note}",
                                       changes={"recent_action": note}))

    def _handle_ooc(self, user: str) -> None:
        cmd = user.strip().lower()
        if any(w in cmd for w in ("quit", "exit", "stop")):
            self._end("You set the story aside.")
        elif "save" in cmd:
            save_game(self.state, self.save_path)
            self.presenter.emit(SystemMessage(f"Game saved to {self.save_path}."))
        elif "help" in cmd:
            self.presenter.emit(SystemMessage(
                "Commands: look, status, rest, save, quit. "
                "Otherwise, just say or do something."))
        elif any(w in cmd for w in ("status", "condition", "health")):
            pc = self.state.pc
            self.presenter.emit(SystemMessage(
                f"{pc.name} is {self.ruleset.health_descriptor(pc)}."))
        elif any(w in cmd for w in ("rest", "sleep", "camp")):
            ctx = self.ruleset.rest_context(self.state.location)
            attempts = self.state.flags.get("rest_attempts", 0)
            res = self.ruleset.rest_attempt(
                self.state.pc, in_settlement=ctx.get("in_settlement", False),
                at_inn=ctx.get("at_inn", False), attempts=attempts)
            self.presenter.emit(SystemMessage(res.get("message") or "You rest a while."))
            outcome = res.get("outcome")
            if outcome in ("rested", "arrested"):
                self.state.flags["rest_attempts"] = 0
                self.state.flags["imprisoned"] = (outcome == "arrested")
                if outcome == "rested" and self.story is not None:
                    self.story.on_long_rest()
            else:
                self.state.flags["rest_attempts"] = attempts + 1
        elif any(w in cmd for w in ("look", "where", "scene")):
            self._narrate_scene()
        else:
            self.presenter.emit(SystemMessage("Unknown command. Try 'help'."))

    _MOVE_VERBS = ("go", "move", "enter", "head", "walk", "proceed", "advance", "approach", "climb")
    _SEARCH_VERBS = ("search", "investigate", "scan", "scour", "rummage")
    _TAKE_VERBS = ("take", "grab", "loot", "collect", "retrieve", "pocket", "pick up", "steal")
    _OPEN_VERBS = ("open", "unlock", "force", "pry", "bash")
    _SENSE_VERBS = ("detect", "sense", "scry", "reveal", "locate")

    def _strip_filler(self, text: str) -> str:
        t = text.strip()
        changed = True
        while changed:
            changed = False
            for f in ("at ", "to ", "into ", "toward ", "towards ", "through ", "over ",
                      "the ", "a ", "an ", "in ", "on ", "up ", "out "):
                if t.startswith(f):
                    t = t[len(f):].strip()
                    changed = True
        return t.strip()

    def _scene_action(self, user: str) -> bool:
        s = self.scene
        cmd = user.strip().lower()
        words = cmd.split()
        if not words:
            return False
        verb, rest = words[0], self._strip_filler(cmd[len(words[0]):])

        if verb in ("look", "examine", "inspect", "survey") and (
                not rest or rest in ("around", "here", "room", "scene", "surroundings")):
            self._narrate_scene()
            return True
        if verb in ("examine", "inspect") and rest:
            obj = s.feature(rest) or s.presence(rest)
            if obj is None:
                self.presenter.emit(SystemMessage("You don't see that here."))
                return True
            desc = getattr(obj, "description", "") or getattr(obj, "note", "") or obj.name
            self._narrate(f"You examine {obj.name}.", as_player=True)
            return True

        if verb in self._MOVE_VERBS and rest:
            res = s.move_pc(rest)
            if res["ok"]:
                self.presenter.emit(StateDelta(summary=f"moved to {res['zone']}",
                                               changes={"zone": res["zone"]}))
                self.state.location = s.here().name
                if self.story is not None:
                    self.story.on_move(res["zone"])
                self._narrate_scene()
            else:
                self.presenter.emit(SystemMessage(res["message"]))
            return True

        if verb in self._SEARCH_VERBS:
            outcome = self._scene_check("investigation")
            found = s.search(outcome.band.value)
            if found["found_anything"]:
                names = [f.name for f in found["features"]] + [p.name for p in found["presences"]]
                self._narrate(f"[Your search turns up: {', '.join(names)}. Narrate the discovery.]",
                              as_player=False)
            else:
                self._narrate("[The search turns up nothing new here. Narrate the careful but "
                              "fruitless look around.]", as_player=False)
            return True

        if (verb in self._TAKE_VERBS or cmd.startswith("pick up")) and rest not in ("lock", ""):
            target = rest[3:].strip() if rest.startswith("up ") else rest
            stealing = verb == "steal"
            f = s.feature(target)
            if f is None:
                self.presenter.emit(SystemMessage("There's nothing like that to take here."))
                return True
            if stealing or any(p.disposition != "friendly" and not p.hidden
                               for p in s.presences_in()):
                outcome = self._scene_check("sleight_of_hand", approach="quietly, unseen")
                if not outcome.success:
                    s.raise_alarm("suspicious")
                    self._narrate("[You're spotted reaching for it -- eyes turn your way, suspicion "
                                  "rising. Narrate getting caught in the act.]", as_player=False)
                    return True
            res = s.take(target)
            if res["ok"]:
                for key in res["items"]:
                    self.ruleset.grant_item(self.state.pc, key)
                    info = self.ruleset.item_info(key)
                    self.presenter.emit(ItemGained(
                        owner=self.state.pc.name, key=key,
                        name=info.name if info else key,
                        rarity=getattr(info, "rarity", "common") if info else "common"))
                got = ", ".join(self.ruleset.item_info(k).name if self.ruleset.item_info(k) else k
                                for k in res["items"]) or "nothing of value"
                self._narrate(f"[You take from {res['feature']}: {got}. Narrate it.]", as_player=False)
            else:
                self.presenter.emit(SystemMessage(res["message"]))
            return True

        if verb in self._OPEN_VERBS and rest:
            f = s.feature(rest)
            if f is None:
                self.presenter.emit(SystemMessage("You don't see that here."))
                return True
            if not f.locked:
                self._narrate(f"You open {f.name}.", as_player=True)
                return True
            forcing = verb in ("force", "bash", "pry")
            skill = "athletics" if forcing else "thieves_tools"
            outcome = self._scene_check(skill, approach=("forcing it" if forcing else "picking the lock"))
            if outcome.success:
                s.unlock(rest)
                self._narrate(f"[{f.name} gives way and opens. Narrate it.]", as_player=False)
            else:
                self._narrate(f"[{f.name} holds fast -- it won't open this way. Narrate the failed "
                              f"attempt.]", as_player=False)
            return True

        if verb in self._SENSE_VERBS or "detect" in words or "sense" in words:
            sensed = s.reveal_enemies()
            if sensed:
                where = "; ".join(f"{d['name']} in {d['zone_name']}" for d in sensed)
                self._narrate(f"[Your senses reach out and find: {where}. Narrate the vision/feeling "
                              f"of sensing them, without seeing them physically.]", as_player=False)
            else:
                self._narrate("[You reach out with your senses and feel no hostile presence nearby. "
                              "Narrate the calm.]", as_player=False)
            return True

        return False

    def _try_use_item(self, user: str) -> bool:
        cmd = user.strip().lower()
        words = cmd.split()
        if not words or words[0] not in ("use", "drink", "quaff", "consume", "apply"):
            return False
        if not hasattr(self.ruleset, "use_item"):
            return False
        ref = self._strip_filler(cmd[len(words[0]):])
        inv = self.state.pc.sheet.get("inventory", [])
        key = None
        for k in inv:
            info = self.ruleset.item_info(k) if hasattr(self.ruleset, "item_info") else None
            name = info.name.lower() if info else k.replace("_", " ")
            if ref == k or (ref and (ref in name or name in ref)):
                key = k
                break
        if key is None:
            self.presenter.emit(SystemMessage("You aren't carrying that."))
            return True
        res = self.ruleset.use_item(self.state.pc, key)
        if res.get("ok") and res.get("kind") == "heal":
            self.presenter.emit(Healed(name=self.state.pc.name, amount=res.get("healed", 0),
                                       source=res.get("item_name", "")))
            self._narrate(f"[{res['message']} Narrate the relief, briefly.]", as_player=False)
        else:
            self.presenter.emit(SystemMessage(res.get("message") or "Nothing happens."))
        return True

    def _scene_check(self, skill: str, approach: str = ""):
        actor = self.state.pc
        base = dict(self.state.flags.get("scene", {}))
        if self.scene is not None:
            base.update(self.scene.check_factors())
        ctx = CheckContext(
            approach=approach,
            actor_statuses=frozenset(actor.statuses),
            skill_tags=frozenset(self.ruleset.skill_tags(skill)),
            impairment_delta=self.ruleset.situational_difficulty_delta(actor, skill),
            lighting=base.get("lighting"), footing=base.get("footing"),
            target_alertness=base.get("target_alertness"),
            has_proper_tools=base.get("has_proper_tools"),
            time_pressure=bool(base.get("time_pressure", False)),
        )
        band, reasons = self.assessor.assess(skill, ctx)
        difficulty = self.ruleset.difficulty_for_band(band)
        outcome = self.ruleset.resolve_check(actor, skill, difficulty)
        raw = dict(outcome.raw)
        raw["difficulty_reasons"] = reasons
        self.presenter.emit(CheckResolved(skill=skill, band=outcome.band.value,
                                          success=outcome.success, difficulty=band.value, raw=raw))
        return outcome

    def _narrate_scene(self) -> None:
        if self.scene is not None:
            z = self.scene.here()
            where = z.name if z is not None else self.state.location
            self._narrate(f"You take in your surroundings: {where}.", as_player=False)
        else:
            self._narrate(f"You are in {self.state.location}.", as_player=False)

    def _narrate(self, text_in: str, as_player: bool = True, mode: str = "exploration",
                 register_key: str | None = None) -> None:
        history = list(self.state.recent())
        if as_player:
            self.state.record("player", text_in)
        block = (f"{self._state_view()}\n\nPlayer: {text_in}"
                 if as_player else f"{self._state_view()}\n\n{text_in}")
        self._emit_narration(history, block, mode=mode, register_key=register_key)

    def _emit_narration(self, history, block: str, mode: str = "exploration",
                        register_key: str | None = None) -> None:
        if self.scene is not None:
            block = self.scene.brief() + "\n\n" + block
            if mode == "dialogue":
                voices = self._npc_voices()
                if voices:
                    block = block + "\n\n" + voices
        prompt = self.builder.build(system=self._narrator_system(mode, register_key), history=history,
                                    user=block)
        text = self.client.complete(
            prompt, CREATIVE.with_stops(self.builder.stops)).text.strip()
        self.state.record("narrator", text)
        self.presenter.emit(Narration(text))

    def _npc_voices(self) -> str:
        if self.scene is None:
            return ""
        briefs = []
        for p in self.scene.presences_in():
            if getattr(p, "kind", "") == "npc" and getattr(p, "card", None) is not None:
                briefs.append(narration.speaking_brief(p.card))
        return "\n\n".join(briefs)

    def _narrator_system(self, mode: str = "exploration", register_key: str | None = None) -> str:
        brief = self.ruleset.narrator_briefing(self.state.pc) if self.state.pc else ""
        if self.narrator_override:
            return "\n\n".join(p for p in (self.narrator_override, brief) if p)
        style = narration.style_block(
            genre_key=narration.genre_for_tone(self.ruleset.narration_tone()),
            mode_key=mode, register_key=register_key)
        return "\n\n".join(p for p in (NARRATOR_SYSTEM, style, brief) if p)

    def _state_view(self) -> str:
        pc = self.state.pc
        carried = self.ruleset.inventory_names(pc)
        carry = f" Carrying: {', '.join(carried[:12])}." if carried else ""
        return (f"[Scene: {self.state.location}. "
                f"{pc.name} is {self.ruleset.health_descriptor(pc)}.{carry}]")

    def _end(self, reason: str) -> None:
        self.running = False
        self.presenter.emit(SessionEnd(reason))
