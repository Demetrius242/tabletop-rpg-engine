from __future__ import annotations

import json
import random
from dataclasses import dataclass

from . import ai
from .classify import _first_json_object
from . import narration
from .invoke import POWER_SHORTHANDS, match_invocation
from .events import (AttackResolved, BloodSpent, CelerityActivated, CombatEnded,
                     CombatStarted, Defended, Fled, Frenzied, Healed, Menu, Moved,
                     MoraleBroke, Narration, OrderIssued, PowerUsed, Presenter,
                     SocialResolved, SystemMessage, TurnStarted)
from .llm import CREATIVE, DETERMINISTIC, LLMClient, PromptBuilder
from .outcome import StaticDifficulty
from .ruleset import Ruleset
from .state import Combatant, GameState
from .turnmodel import Attack, Defend, Pass
from .zones import COVER_AC, Arena

COMBAT_NARRATOR_SYSTEM = (
    "You are the narrator of a fight in a text RPG. Narrate ONLY the single beat "
    "you are given, in one or two tight, vivid sentences, present tense. Use second "
    "person when the player acts or is the target.\n"
    "Hard rules:\n"
    "- Narrate exactly the result given (hit/miss/critical, who moves, who breaks) "
    "and the target's new condition; never change it, and never add deaths or wounds "
    "you weren't told about.\n"
    "- Refer to condition only in the qualitative words provided. Never mention "
    "numbers, dice, hit points, AC, initiative, or zone mechanics."
)

DIRECTIVES = ("focus", "defend_me", "fall_back", "hold")
SOCIAL_MODES = ("intimidate", "taunt")
INTIMIDATE_LOSS = {"critical": 100, "exceptional": 70, "success": 40,
                   "marginal": 20, "failure": 0, "botch": -10}
ALLY_DOWN_MORALE = 15


@dataclass
class Fighter:
    combatant: Combatant
    side: str
    initiative: int = 0
    reaction_available: bool = True
    defending: bool = False
    zone: str = ""
    fled: bool = False
    broken: bool = False
    directive: str = ""
    directive_target: str = ""
    taunted_by: str | None = None
    surprised: bool = False
    declared: object = None

    @property
    def name(self) -> str:
        return self.combatant.name


@dataclass(frozen=True)
class CombatIntent:
    action: str = "pass"
    target: str = ""
    zone: str = ""
    ally: str = ""
    directive: str = ""
    mode: str = ""
    power: str = ""


def _lit(s: str) -> str:
    return '"\\"' + s + '\\""'


def _alt(names) -> str:
    return " | ".join(_lit(n) for n in names)


def _combat_grammar(enemies, allies, zones) -> str:
    rules, objs = [], []

    def shape(tag, body):
        objs.append(tag)
        rules.append(f"{tag} ::= {body}")

    a = _lit("action")
    shape("attack_a", f'"{{" ws {a} ws ":" ws {_lit("attack")} ws "," ws {_lit("target")} ws ":" ws enemy ws "}}"')
    shape("defend_a", f'"{{" ws {a} ws ":" ws {_lit("defend")} ws "}}"')
    shape("flee_a", f'"{{" ws {a} ws ":" ws {_lit("flee")} ws "}}"')
    shape("pass_a", f'"{{" ws {a} ws ":" ws {_lit("pass")} ws "}}"')
    shape("mend_a", f'"{{" ws {a} ws ":" ws {_lit("mend")} ws "}}"')
    shape("social_a", f'"{{" ws {a} ws ":" ws {_lit("social")} ws "," ws {_lit("mode")} ws ":" ws mode ws "," ws {_lit("target")} ws ":" ws enemy ws "}}"')
    rules.append(f"mode ::= {_alt(SOCIAL_MODES)}")
    if zones:
        shape("move_a", f'"{{" ws {a} ws ":" ws {_lit("move")} ws "," ws {_lit("zone")} ws ":" ws zone ws "}}"')
        shape("retreat_a", f'"{{" ws {a} ws ":" ws {_lit("retreat")} ws "," ws {_lit("zone")} ws ":" ws zone ws "}}"')
        rules.append(f"zone ::= {_alt(zones)}")
    if allies:
        shape("order_a", f'"{{" ws {a} ws ":" ws {_lit("order")} ws "," ws {_lit("ally")} ws ":" ws ally ws "," ws {_lit("directive")} ws ":" ws directive ( ws "," ws {_lit("target")} ws ":" ws enemy )? ws "}}"')
        rules.append(f"directive ::= {_alt(DIRECTIVES)}")
        rules.append(f"ally ::= {_alt(allies)}")
    rules.append(f"enemy ::= {_alt(enemies)}")
    rules.append(r"ws ::= [ \t\n]*")
    root = "root ::= ws ( " + " | ".join(objs) + " ) ws"
    return root + "\n" + "\n".join(rules) + "\n"


def _combat_system(enemies, allies, zones) -> str:
    lines = [
        "You are resolving the player's COMBAT action. Reply with ONLY a JSON "
        "object, no prose. Choose one action:",
        '- attack: {"action":"attack","target":<enemy>}',
        '- defend: {"action":"defend"}',
        '- flee:   {"action":"flee"}  (head for an exit)',
        '- pass:   {"action":"pass"}',
        '- mend:   {"action":"mend"}  (spend blood to heal a wound, if you can)',
        '- social: {"action":"social","mode":"intimidate"|"taunt","target":<enemy>}',
    ]
    if zones:
        lines.append('- move:    {"action":"move","zone":<adjacent zone>}')
        lines.append('- retreat: {"action":"retreat","zone":<adjacent zone>}  (move without provoking)')
    if allies:
        lines.append('- order:   {"action":"order","ally":<ally>,"directive":"focus"|"defend_me"|"fall_back"|"hold","target":<enemy, only for focus>}')
    lines.append("Enemies: " + ", ".join(enemies) + ".")
    if allies:
        lines.append("Allies: " + ", ".join(allies) + ".")
    if zones:
        lines.append("Adjacent zones: " + ", ".join(zones) + ".")
    return "\n".join(lines)


def _parse_combat(raw: str) -> CombatIntent:
    try:
        obj = json.loads(_first_json_object(raw))
        action = str(obj["action"])
    except (ValueError, KeyError):
        return CombatIntent("pass")
    return CombatIntent(
        action=action,
        target=str(obj.get("target", "")),
        zone=str(obj.get("zone", "")),
        ally=str(obj.get("ally", "")),
        directive=str(obj.get("directive", "")),
        mode=str(obj.get("mode", "")),
        power=str(obj.get("name", "")),
    )


def _match_choice(raw: str, labels: list) -> int | None:
    s = (raw or "").strip().lower()
    if not s or s in ("none", "no", "skip", "nothing", "do nothing",
                      "pass", str(len(labels) + 1)):
        return None
    if s.isdigit():
        i = int(s) - 1
        return i if 0 <= i < len(labels) else None
    for i, label in enumerate(labels):
        ll = label.lower()
        if s == ll or ll.startswith(s):
            return i
    for i, label in enumerate(labels):
        if any(tok and tok in label.lower() for tok in s.split()):
            return i
    return None


def parse_power_invocation(text, powers, enemy_names=()):
    if not powers:
        return None
    item, target, explicit = match_invocation(text, powers, enemy_names, POWER_SHORTHANDS)
    if item is not None:
        return CombatIntent(action="power", power=item.key, target=target)
    if explicit:
        return CombatIntent(action="power", power="")
    return None


class CombatController:
    def __init__(self, client: LLMClient, presenter: Presenter, state: GameState,
                 ruleset: Ruleset, *, enemies, companions=(), arena: Arena | None = None,
                 builder=None, rng=None, surprise=None, story=None, narrator_override=""):
        self.client = client
        self.presenter = presenter
        self.state = state
        self.ruleset = ruleset
        self.tm = ruleset.turn_model()
        self.builder = builder or PromptBuilder()
        self.rng = rng or random.Random()
        self.surprise = surprise
        self.story = story
        self.narrator_override = narrator_override or ""
        self._round_no = 0
        self.fighters = (
            [Fighter(state.pc, "party")]
            + [Fighter(c, "party") for c in companions]
            + [Fighter(e, "enemies") for e in enemies]
        )
        self._uniquify_names()
        self.by_name = {f.name.lower(): f for f in self.fighters}
        self.arena = arena or Arena.single([f.name for f in self.fighters])
        for f in self.fighters:
            f.zone = self.arena.placements.get(f.name, next(iter(self.arena.zones)))
        self.order: list[Fighter] = []
        self._pc_fled = False

    def _uniquify_names(self) -> None:
        seen: dict[str, int] = {}
        for f in self.fighters:
            key = f.name.lower()
            if key in seen:
                seen[key] += 1
                f.combatant.name = f"{f.combatant.name} {seen[key]}"
            else:
                seen[key] = 1

    def _living(self, side: str) -> list[Fighter]:
        return [f for f in self.fighters if f.side == side
                and not f.fled and not self.ruleset.is_defeated(f.combatant)]

    def _pc_fighter(self) -> Fighter | None:
        for f in self.fighters:
            if f.combatant.is_pc:
                return f
        return None

    def combat_over(self) -> bool:
        return (self._pc_fled or not self._living("party") or not self._living("enemies"))

    def _victor(self) -> str:
        if self._pc_fled:
            return "fled"
        return "party" if self._living("party") else "enemies"

    def run(self, max_rounds: int = 200) -> str:
        self._roll_initiative()
        self._determine_surprise()
        self.presenter.emit(CombatStarted(
            order=[f.name for f in self.order],
            sides={f.name: f.side for f in self.order}))
        self._rant_on_start()
        self._narrate("[A fight breaks out.]")
        if self.surprised_names():
            caught = ", ".join(self.surprised_names())
            self._narrate(f"[Surprise! {caught} are caught unawares and lose their first turn. Narrate the ambush.]")
        rounds = 0
        while not self.combat_over() and rounds < max_rounds:
            self._round_no = rounds + 1
            self.tm.run_round([f.combatant for f in self.order], _Ctx(self))
            if self._round_no == 1:
                for f in self.fighters:
                    f.surprised = False
            if self.story is not None and not self.combat_over():
                self.story.on_combat_round()
            rounds += 1
        victor = self._victor()
        survivors = [f.name for f in self._living("enemies" if victor == "enemies" else "party")]
        self.presenter.emit(CombatEnded(victor=victor, survivors=survivors))
        verdict = {"party": "You stand victorious.", "enemies": "You have fallen.",
                   "fled": "You have escaped the fight."}[victor]
        self._narrate(f"[The fight is over. RESULT: {verdict} Narrate the aftermath.]")
        return victor

    def surprised_names(self) -> list[str]:
        return [f.name for f in self.fighters if f.surprised]

    def _determine_surprise(self) -> None:
        def all_hidden(side):
            living = self._living(side)
            return bool(living) and all(
                ({"hidden", "stealthed", "unseen"} & set(getattr(f.combatant, "statuses", set())))
                for f in living)
        def any_alert(side):
            return any("alert" in set(getattr(f.combatant, "statuses", set())) for f in self._living(side))

        victim = None
        if self.surprise in ("party", "enemies"):
            victim = self.surprise
        elif all_hidden("party") and not all_hidden("enemies") and not any_alert("enemies"):
            victim = "enemies"
        elif all_hidden("enemies") and not all_hidden("party") and not any_alert("party"):
            victim = "party"
        if victim:
            for f in self.fighters:
                if f.side == victim:
                    f.surprised = True

    def _roll_initiative(self) -> None:
        order = []
        for combatant, init in self.tm.initiative_order([f.combatant for f in self.fighters]):
            f = self.by_name[combatant.name.lower()]
            f.initiative = init
            order.append(f)
        self.order = order

    def is_active(self, combatant: Combatant) -> bool:
        f = self.by_name[combatant.name.lower()]
        return not f.fled and not self.ruleset.is_defeated(combatant)

    def begin_turn(self, combatant: Combatant) -> None:
        f = self.by_name[combatant.name.lower()]
        f.reaction_available = True
        f.defending = False
        self.presenter.emit(TurnStarted(name=f.name, side=f.side))

    def take_turn(self, combatant: Combatant) -> None:
        f = self.by_name[combatant.name.lower()]
        if f.fled or self.ruleset.is_defeated(combatant):
            return
        if f.surprised:
            self._narrate(f"[{f.name} is caught by surprise and cannot act this round.]")
        else:
            budget = self.tm.new_turn_budget(combatant)
            if combatant.is_pc:
                self._pc_turn(f, budget)
            else:
                self._ai_turn(f, budget)
        if self.story is not None:
            self.story.on_combat_turn(combatant.name)

    def _reach_of(self, f: Fighter) -> str:
        attacks = f.combatant.sheet.get("attacks") or [{}]
        return attacks[0].get("reach", "melee")

    def _in_reach(self, attacker: Fighter, defender: Fighter) -> bool:
        if self._reach_of(attacker) == "ranged":
            return True
        return attacker.zone == defender.zone

    def _reachable_enemies(self, f: Fighter) -> list[Fighter]:
        foes = self._living("enemies" if f.side == "party" else "party")
        return [e for e in foes if self._in_reach(f, e)]

    def _situational(self, attacker: Fighter, defender: Fighter):
        ac = hit = 0
        if self._reach_of(attacker) == "ranged" and attacker.zone != defender.zone:
            ac += COVER_AC.get(self.arena.zones[defender.zone].cover, 0)
        if self.arena.zones[attacker.zone].elevation > self.arena.zones[defender.zone].elevation:
            hit += 2
        return ac, hit

    def _melee_threats(self, mover: Fighter, zone: str):
        foes = self._living("enemies" if mover.side == "party" else "party")
        return [e for e in foes if e.zone == zone
                and self._reach_of(e) == "melee" and e.reaction_available]

    def _move(self, f: Fighter, dest: str, budget, *, provoke: bool) -> None:
        src = f.zone
        if dest == src or dest not in self.arena.zones:
            return
        if provoke:
            for e in self._melee_threats(f, src):
                if self.ruleset.is_defeated(f.combatant):
                    break
                e.reaction_available = False
                self._do_attack(e, f, opportunity=True)
            if self.ruleset.is_defeated(f.combatant):
                return
        f.zone = dest
        if budget is not None and budget.can("movement"):
            budget.spend("movement")
        self.presenter.emit(Moved(f.name, src, dest, provoke))

    def _step_toward_nearest_enemy(self, f: Fighter):
        foe_zones = {e.zone for e in self._living("enemies" if f.side == "party" else "party")}
        for z in self.arena.bfs(f.zone):
            if z in foe_zones and z != f.zone:
                return self.arena.step_toward(f.zone, z)
        return None

    def _step_toward_nearest_exit(self, f: Fighter):
        for z in self.arena.bfs(f.zone):
            if self.arena.zones[z].is_exit and z != f.zone:
                return self.arena.step_toward(f.zone, z)
        return None

    def _do_attack(self, attacker: Fighter, defender: Fighter, *, opportunity=False) -> None:
        sac, shit = self._situational(attacker, defender)
        res = self.tm.resolve_attack(
            attacker.combatant, defender.combatant, defending=defender.defending,
            situational_ac=sac, situational_hit=shit)
        if res.hit and res.damage:
            self.ruleset.apply_damage(defender.combatant, res.damage)
        defeated = self.ruleset.is_defeated(defender.combatant)
        cond = self.ruleset.health_descriptor(defender.combatant)
        raw = dict(res.raw)
        if opportunity:
            raw["opportunity"] = True
        self.presenter.emit(AttackResolved(
            attacker=attacker.name, defender=defender.name, hit=res.hit,
            crit=(res.band.value == "critical"), band=res.band.value, damage=res.damage,
            defender_condition="defeated" if defeated else cond,
            defeated=defeated, raw=raw))
        if self._is_salient(attacker, defender, res, defeated):
            self._narrate_attack(attacker, defender, res, defeated, cond, opportunity=opportunity)
        if defeated:
            self._on_defeat(defender)

    def _on_defeat(self, victim: Fighter) -> None:
        if victim.side == "enemies":
            for e in self._living("enemies"):
                self._dent_morale(e, ALLY_DOWN_MORALE)

    def _dent_morale(self, f: Fighter, amount: int) -> None:
        sheet = f.combatant.sheet
        sheet["morale"] = sheet.get("morale", 100) - amount
        if sheet["morale"] <= sheet.get("morale_threshold", 30):
            f.broken = True

    def _pc_turn(self, f: Fighter, budget) -> None:
        intent = self._pc_declare(f)
        enemies = self._living("enemies")
        allies = [a for a in self._living("party") if a is not f]
        self._perform_pc(f, intent, budget, enemies, allies)

    def _pc_declare(self, f: Fighter) -> "CombatIntent":
        enemies = self._living("enemies")
        allies = [a for a in self._living("party") if a is not f]
        zones = sorted(self.arena.neighbors(f.zone))
        powers = self.ruleset.available_combat_powers(f.combatant)
        names = [e.name for e in enemies]
        self.presenter.emit(SystemMessage(self._pc_prompt(f, enemies, allies, zones, powers)))
        raw = self.presenter.read_action()
        intent = parse_power_invocation(raw, powers, names)
        if intent is not None and not intent.power:
            self.presenter.emit(SystemMessage(self._power_help(powers)))
            raw = self.presenter.read_action()
            intent = parse_power_invocation(raw, powers, names)
        if intent is not None and intent.power:
            return intent
        return self._classify(raw, names, [a.name for a in allies], zones)

    def _power_help(self, powers) -> str:
        listed = ", ".join(f"{p.key} ({p.name})" for p in powers) or "none right now"
        return ("You reach for a Discipline but don't have that power. You can invoke: "
                f"{listed}. Type 'use <power>' (e.g. 'use {powers[0].key}') -- or take a "
                "normal action instead.") if powers else \
               "You have no Disciplines to invoke right now."

    def _pc_prompt(self, f, enemies, allies, zones, powers=()) -> str:
        bits = [f"Your turn (in {f.zone}). Enemies: {', '.join(e.name for e in enemies)}."]
        if zones:
            bits.append(f"Move to: {', '.join(zones)}.")
        if allies:
            bits.append(f"Allies: {', '.join(a.name for a in allies)}.")
        bits.append("(attack <name> / move <zone> / retreat <zone> / defend / mend / "
                    "flee / intimidate <name> / taunt <name> / order <ally> <directive>)")
        if powers:
            bits.append("Disciplines -- type 'use <power>': "
                        + ", ".join(p.key for p in powers) + ".")
        return " ".join(bits)

    def _classify(self, text, enemies, allies, zones) -> CombatIntent:
        prompt = self.builder.build(
            system=_combat_system(enemies, allies, zones), history=None, user=text)
        sampling = DETERMINISTIC.with_stops(self.builder.stops)
        raw = self.client.complete(
            prompt, sampling, grammar=_combat_grammar(enemies, allies, zones)).text
        return _parse_combat(raw)

    def begin_round(self) -> None:
        for f in self.fighters:
            f.defending = False
            f.reaction_available = True

    def declare(self, combatant: Combatant) -> None:
        f = self.by_name[combatant.name.lower()]
        if f.fled or self.ruleset.is_defeated(combatant):
            f.declared = None
            return
        self._pre_turn(f)
        forced = self.ruleset.forced_action(combatant)
        if forced:
            f.declared = ("forced", forced)
        elif combatant.is_pc:
            f.declared = ("pc", self._pc_declare(f))
        elif f.broken:
            f.declared = ("rout", None)
        elif (pkey := self.ruleset.ai_combat_power(combatant)):
            f.declared = ("ai_power", pkey)
        else:
            reachable = self._reachable_enemies(f)
            action = ai.choose_action(
                f, reachable, self._living(f.side), self.ruleset, self.tm, self.rng,
                priority_target=self._priority_target(f))
            f.declared = ("ai", action)

    def _pre_turn(self, f: Fighter) -> None:
        if self.ruleset.forced_action(f.combatant):
            return
        if f.combatant.is_pc:
            choices = self.ruleset.pre_turn_choices(f.combatant)
            if choices:
                labels = [label for _, label in choices]
                self.presenter.emit(Menu("Reflexive (before you act):",
                                         labels + ["Do nothing"]))
                idx = _match_choice(self.presenter.read_action(), labels)
                if idx is not None:
                    self._apply_pre_turn(f, choices[idx][0])
        else:
            self.ruleset.ai_pre_turn(f.combatant)
            if f.combatant.sheet.get("_celerity_active"):
                extra = self.ruleset.actions_this_turn(f.combatant) - 1
                self.presenter.emit(CelerityActivated(f.name, extra))
        if self.ruleset.check_frenzy(f.combatant):
            self.presenter.emit(Frenzied(f.name))

    def _apply_pre_turn(self, f: Fighter, key: str) -> None:
        note = self.ruleset.apply_pre_turn(f.combatant, key)
        if not note:
            return
        if f.combatant.sheet.get("_celerity_active"):
            extra = self.ruleset.actions_this_turn(f.combatant) - 1
            self.presenter.emit(CelerityActivated(f.name, extra))
        else:
            self.presenter.emit(SystemMessage(note))

    def announce_turn(self, combatant: Combatant) -> None:
        f = self.by_name[combatant.name.lower()]
        self.presenter.emit(TurnStarted(name=f.name, side=f.side))

    def resolve(self, combatant: Combatant) -> None:
        f = self.by_name[combatant.name.lower()]
        declared, f.declared = f.declared, None
        if f.fled or self.ruleset.is_defeated(combatant) or not declared:
            self.ruleset.end_turn(combatant)
        else:
            kind, payload = declared
            actions = max(1, self.ruleset.actions_this_turn(combatant))
            for i in range(actions):
                if self.combat_over() or self.ruleset.is_defeated(combatant) or f.fled:
                    break
                budget = self.tm.new_turn_budget(combatant)
                if i == 0:
                    self._resolve_one(f, kind, payload, budget)
                else:
                    self._resolve_extra(f, budget)
            f.taunted_by = None
            self.ruleset.end_turn(combatant)
        if self.story is not None:
            self.story.on_combat_turn(combatant.name)

    def _resolve_one(self, f, kind, payload, budget) -> None:
        if kind == "pc":
            enemies = self._living("enemies")
            allies = [a for a in self._living("party") if a is not f]
            self._perform_pc(f, payload, budget, enemies, allies)
        elif kind == "forced":
            self._forced(f, payload, budget)
        elif kind == "ai_power":
            self._use_power(f, payload, "", self._living("enemies"))
        elif kind == "rout":
            self._rout(f, budget)
        else:
            self._perform_ai(f, payload)

    def _resolve_extra(self, f, budget) -> None:
        forced = self.ruleset.forced_action(f.combatant)
        if forced == "attack":
            self._forced_attack(f)
        elif forced:
            return
        elif f.combatant.is_pc:
            self.presenter.emit(SystemMessage("Extra action (Celerity):"))
            enemies = self._living("enemies")
            allies = [a for a in self._living("party") if a is not f]
            self._perform_pc(f, self._pc_declare(f), budget, enemies, allies)
        else:
            reachable = self._reachable_enemies(f)
            if reachable:
                action = ai.choose_action(
                    f, reachable, self._living(f.side), self.ruleset, self.tm, self.rng,
                    priority_target=self._priority_target(f))
                self._perform_ai(f, action)

    def _forced(self, f: Fighter, what: str, budget) -> None:
        if what == "attack":
            self._forced_attack(f)
        elif what == "flee":
            self._flee(f, budget)

    def _forced_attack(self, f: Fighter) -> None:
        foes = self._reachable_enemies(f) or self._living(
            "enemies" if f.side == "party" else "party")
        if foes:
            self._do_attack(f, foes[0])

    def _perform_pc(self, f, intent, budget, enemies, allies) -> None:
        a = intent.action
        if a == "attack":
            self._pc_attack(f, intent.target, budget, enemies)
        elif a == "move":
            self._pc_move(f, intent.zone, budget, provoke=True)
        elif a == "retreat":
            self._pc_move(f, intent.zone, budget, provoke=False)
            if budget.can("actions"):
                budget.spend("actions")
        elif a == "flee":
            self._flee(f, budget)
        elif a == "social":
            self._social(f, intent.target, intent.mode, enemies)
        elif a == "order":
            self._issue_order(f, intent.ally, intent.directive, intent.target, allies, enemies)
        elif a == "defend":
            f.defending = True
            self.presenter.emit(Defended(f.name))
            self._narrate(f"[{f.name} takes a defensive stance. RESULT: braced and "
                          f"harder to hit. Narrate briefly.]")
        elif a == "mend":
            did, levels = self.ruleset.combat_heal(f.combatant)
            if did:
                self.presenter.emit(Healed(f.name, levels))
                self._narrate(f"[{f.name} pulls on the blood to close wounds. RESULT: "
                              f"mended {levels} wound level(s). Narrate briefly.]")
            else:
                self._narrate(f"[{f.name} reaches for power to heal but nothing comes. "
                              f"RESULT: no effect. Narrate very briefly.]")
        elif a == "power":
            self._use_power(f, intent.power, intent.target, enemies)

    def _use_power(self, f: Fighter, key: str, target_name: str, enemies) -> None:
        catalog = {p.key: p for p in self.ruleset.available_combat_powers(f.combatant)}
        power = catalog.get((key or "").strip().lower())
        if power is None:
            for p in catalog.values():
                if (key or "").lower() in (p.key, p.name.lower()):
                    power = p
                    break
        if power is None:
            self._narrate(f"[{f.name} grasps for a power they don't have. "
                          f"RESULT: nothing happens. Narrate very briefly.]")
            return
        target = None
        if power.target == "other":
            target = self.by_name.get((target_name or "").lower())
            if (target is None or target.fled
                    or self.ruleset.is_defeated(target.combatant)):
                living = self._living("enemies" if f.side == "party" else "party")
                target = living[0] if living else None
        allies = [a.combatant for a in self._living(f.side) if a is not f]
        result = self.ruleset.use_discipline(
            f.combatant, power.discipline, power.key,
            target.combatant if target else None, allies=allies)
        self.presenter.emit(PowerUsed(
            name=f.name, power=getattr(result, "power", power.name) or power.name,
            discipline=power.discipline, target=(target.name if target else ""),
            success=getattr(result, "success", False), ok=getattr(result, "ok", False),
            reason=getattr(result, "reason", "")))
        cue = getattr(result, "cue", "")
        if cue:
            self._narrate(f"[{f.name} uses {power.name}. {cue} Narrate briefly.]")
        elif not getattr(result, "ok", False):
            self._narrate(f"[{f.name} tries to invoke {power.name} and fails. "
                          f"RESULT: nothing happens. Narrate very briefly.]")

    def _pc_attack(self, f, target_name, budget, enemies) -> None:
        target = self.by_name.get((target_name or "").lower())
        if target is None or target.side != "enemies" \
                or self.ruleset.is_defeated(target.combatant) or target.fled:
            target = enemies[0] if enemies else None
        if target is None:
            return
        if not self._in_reach(f, target):
            dest = self.arena.step_toward(f.zone, target.zone)
            if dest:
                self._move(f, dest, budget, provoke=True)
            if self.ruleset.is_defeated(f.combatant):
                return
        if self._in_reach(f, target):
            self._do_attack(f, target)
        else:
            self._narrate(f"[{f.name} presses toward {target.name} but can't reach them "
                          f"this turn. Narrate the advance.]")

    def _pc_move(self, f, zone, budget, *, provoke) -> None:
        dest = zone if zone in self.arena.neighbors(f.zone) else None
        if dest is None:
            self._narrate(f"[{f.name} looks for an opening but holds position.]")
            return
        self._move(f, dest, budget, provoke=provoke)

    def _flee(self, f, budget) -> None:
        if not self.arena.exits():
            self._narrate(f"[{f.name} casts about for a way out -- there is none.]")
            return
        if self.arena.zones[f.zone].is_exit:
            self._escape(f)
            return
        dest = self._step_toward_nearest_exit(f)
        if dest:
            self._move(f, dest, budget, provoke=True)
            if not self.ruleset.is_defeated(f.combatant) and self.arena.zones[f.zone].is_exit:
                self._escape(f)
            elif not self.ruleset.is_defeated(f.combatant):
                self._narrate(f"[{f.name} breaks for the exit. Narrate the dash.]")

    def _escape(self, f) -> None:
        f.fled = True
        self.presenter.emit(Fled(f.name))
        if f.combatant.is_pc:
            self._pc_fled = True
        self._narrate(f"[{f.name} breaks away and escapes the fight. Narrate it.]")

    def _issue_order(self, pc, ally_name, directive, target, allies, enemies) -> None:
        ally = self.by_name.get((ally_name or "").lower())
        directive = directive if directive in DIRECTIVES else "hold"
        if ally is None or ally.side != "party" or ally is pc \
                or self.ruleset.is_defeated(ally.combatant) or ally.fled:
            self.presenter.emit(OrderIssued(by=pc.name, to=ally_name or "?",
                                            directive=directive, delivered=False))
            self._narrate(f"[{pc.name} barks an order, but no ally can answer it.]")
            return
        if not self.ruleset.can_receive_communication(ally.combatant, "verbal"):
            self.presenter.emit(OrderIssued(by=pc.name, to=ally.name,
                                            directive=directive, delivered=False))
            self._narrate(f"[{pc.name} orders {ally.name}, but it cannot heed the command.]")
            return
        ally.directive = directive
        ally.directive_target = target if directive == "focus" else ""
        self.presenter.emit(OrderIssued(by=pc.name, to=ally.name, directive=directive,
                                        target=ally.directive_target, delivered=True))
        tgt = f" on {ally.directive_target}" if ally.directive_target else ""
        self._narrate(f"[{pc.name} orders {ally.name}: {directive}{tgt}. Narrate the shout.]")

    def _social(self, pc, enemy_name, mode, enemies) -> None:
        target = self.by_name.get((enemy_name or "").lower())
        if target is None or target.side != "enemies" \
                or self.ruleset.is_defeated(target.combatant) or target.fled:
            target = enemies[0] if enemies else None
        if target is None:
            return
        mode = mode if mode in SOCIAL_MODES else "intimidate"
        if not self.ruleset.can_receive_communication(target.combatant, "verbal"):
            self.presenter.emit(SocialResolved(by=pc.name, target=target.name,
                                               mode=mode, delivered=False))
            self._narrate(f"[{pc.name} tries to {mode} {target.name}, but the words "
                          f"don't reach it. RESULT: no effect. Narrate.]")
            return
        skill = "intimidation" if mode == "intimidate" else "deception"
        difficulty = self.ruleset.social_difficulty(target.combatant, mode)
        outcome = self.ruleset.resolve_check(pc.combatant, skill, difficulty)
        effect = self._apply_social(pc, mode, target, outcome.band.value)
        self.presenter.emit(SocialResolved(by=pc.name, target=target.name, mode=mode,
                                           band=outcome.band.value, delivered=True, effect=effect))
        self._narrate_social(pc, target, mode, effect)

    def _apply_social(self, pc, mode, target, band) -> str:
        success = band in ("marginal", "success", "exceptional", "critical")
        if mode == "taunt":
            if success:
                target.taunted_by = pc.name
                return "taunted"
            return "none"
        loss = INTIMIDATE_LOSS.get(band, 0)
        sheet = target.combatant.sheet
        sheet["morale"] = sheet.get("morale", 100) - loss
        if loss > 0 and sheet["morale"] <= sheet.get("morale_threshold", 30):
            target.broken = True
            return "breaking"
        return "shaken" if loss > 0 else "none"

    def _ai_turn(self, f: Fighter, budget) -> None:
        if f.broken:
            self._rout(f, budget)
            return
        reachable = self._reachable_enemies(f)
        if not reachable:
            dest = self._ai_destination(f)
            if dest:
                self._move(f, dest, budget, provoke=True)
            if self.ruleset.is_defeated(f.combatant) or f.fled:
                return
            reachable = self._reachable_enemies(f)
        if reachable and budget.can("actions"):
            action = ai.choose_action(
                f, reachable, self._living(f.side), self.ruleset, self.tm, self.rng,
                priority_target=self._priority_target(f))
            self._perform_ai(f, action)
        elif self._should_defend(f):
            f.defending = True
            self.presenter.emit(Defended(f.name))
        f.taunted_by = None

    def _perform_ai(self, f, action) -> None:
        if isinstance(action, Attack):
            target = self.by_name[action.target.name.lower()]
            if self.ruleset.is_defeated(target.combatant) or target.fled:
                fresh = self._reachable_enemies(f)
                if not fresh:
                    return
                target = fresh[0]
            self._do_attack(f, target)
        elif isinstance(action, Defend):
            f.defending = True
            self.presenter.emit(Defended(f.name))

    def _ai_destination(self, f: Fighter):
        directive = f.directive
        if directive == "hold":
            return None
        if directive == "fall_back":
            return self._step_toward_nearest_exit(f)
        if directive == "defend_me":
            pc = self._pc_fighter()
            if pc and not self.ruleset.is_defeated(pc.combatant):
                return self.arena.step_toward(f.zone, pc.zone)
            return None
        return self._step_toward_nearest_enemy(f)

    def _priority_target(self, f: Fighter):
        if f.taunted_by:
            t = self.by_name.get(f.taunted_by.lower())
            if t and not self.ruleset.is_defeated(t.combatant):
                return t.name
        if f.directive == "focus" and f.directive_target:
            t = self.by_name.get(f.directive_target.lower())
            if t and not self.ruleset.is_defeated(t.combatant):
                return t.name
        return None

    def _should_defend(self, f: Fighter) -> bool:
        return (int(f.combatant.sheet.get("intelligence", 2)) >= 3
                and self.ruleset.health_fraction(f.combatant) < 0.25)

    def _rout(self, f: Fighter, budget) -> None:
        if not self.arena.exits() or self.arena.zones[f.zone].is_exit:
            outcome = "surrendered" if not self.arena.exits() else "routed"
            f.fled = True
            self.presenter.emit(MoraleBroke(f.name, outcome))
            self.presenter.emit(Fled(f.name))
            verb = ("throws down its weapon" if outcome == "surrendered"
                    else "breaks and flees")
            self._narrate(f"[{f.name}, its nerve gone, {verb}. RESULT: out of the fight. Narrate.]")
            return
        dest = self._step_toward_nearest_exit(f)
        if dest:
            self._move(f, dest, budget, provoke=True)
            if not self.ruleset.is_defeated(f.combatant) and self.arena.zones[f.zone].is_exit:
                f.fled = True
                self.presenter.emit(MoraleBroke(f.name, "routed"))
                self.presenter.emit(Fled(f.name))
                self._narrate(f"[{f.name} routs through the exit. RESULT: gone. Narrate.]")

    def _is_salient(self, attacker, defender, res, defeated) -> bool:
        return (attacker.combatant.is_pc or defender.combatant.is_pc
                or defeated or res.band.value in ("critical", "botch"))

    def _narrate_attack(self, attacker, defender, res, defeated, cond, *, opportunity=False) -> None:
        band = res.band.value
        if band == "botch":
            cue = "a clumsy miss that leaves the attacker off-balance"
        elif not res.hit:
            cue = "a miss"
        elif band == "critical":
            cue = "a devastating critical hit"
        elif band == "exceptional":
            cue = "a solid, heavy hit"
        else:
            cue = "a hit"
        state = "is knocked out of the fight" if defeated else f"is now {cond}"
        oa = "an opportunity strike as they pull away: " if opportunity else ""
        voice = attacker.combatant.sheet.get("voice")
        bark = (f" {attacker.name} may add a short shouted line in character ({voice})."
                if voice else "")
        self._narrate(
            f"[Combat. {oa}{attacker.name} ({attacker.side}) attacks "
            f"{defender.name} ({defender.side}).\n"
            f"RESULT (narrate exactly, do not change): {cue}; {defender.name} {state}.{bark}]")

    def _narrate_social(self, pc, target, mode, effect) -> None:
        desc = {
            "taunted": f"{target.name} is goaded into fixating on {pc.name}",
            "breaking": f"{target.name}'s nerve cracks -- it's on the edge of flight",
            "shaken": f"{target.name} is rattled but holds",
            "none": f"{target.name} is unmoved",
        }[effect]
        self._narrate(f"[Combat. {pc.name} tries to {mode} {target.name}. "
                      f"RESULT (narrate exactly): {desc}.]")

    def _rant_on_start(self) -> None:
        for f in self._living("enemies"):
            persona = f.combatant.sheet.get("persona")
            intro = persona.get("intro") if isinstance(persona, dict) else None
            if intro:
                self._narrate(f"[{f.name} addresses the party before blows land. "
                              f"Deliver this line in character: {intro}]")
                return

    def _narrate(self, block: str) -> None:
        prompt = self.builder.build(
            system=self._combat_narrator_system(), history=None, user=block)
        text = self.client.complete(
            prompt, CREATIVE.with_stops(self.builder.stops)).text.strip()
        self.presenter.emit(Narration(text))

    def _combat_narrator_system(self) -> str:
        if not hasattr(self, "_brief_cache"):
            pc = getattr(self.state, "pc", None)
            brief = self.ruleset.narrator_briefing(pc) if pc is not None else ""
            flags = getattr(self.state, "flags", {}) or {}
            note = flags.get("enemy_group_note", "")
            if self.narrator_override:
                self._brief_cache = "\n\n".join(p for p in (self.narrator_override, note, brief) if p)
            else:
                tone = self.ruleset.narration_tone() if hasattr(self.ruleset, "narration_tone") else ""
                overlay = flags.get("narration_register")
                style = narration.style_block(genre_key=narration.genre_for_tone(tone),
                                              mode_key="combat", register_key=overlay)
                self._brief_cache = "\n\n".join(p for p in (COMBAT_NARRATOR_SYSTEM, style, note, brief) if p)
        return self._brief_cache


class _Ctx:

    def __init__(self, controller: CombatController):
        self.c = controller

    def is_active(self, combatant) -> bool:
        return self.c.is_active(combatant)

    def combat_over(self) -> bool:
        return self.c.combat_over()

    def begin_turn(self, combatant) -> None:
        self.c.begin_turn(combatant)

    def take_turn(self, combatant) -> None:
        self.c.take_turn(combatant)

    def begin_round(self) -> None:
        self.c.begin_round()

    def declare(self, combatant) -> None:
        self.c.declare(combatant)

    def announce_turn(self, combatant) -> None:
        self.c.announce_turn(combatant)

    def resolve(self, combatant) -> None:
        self.c.resolve(combatant)
