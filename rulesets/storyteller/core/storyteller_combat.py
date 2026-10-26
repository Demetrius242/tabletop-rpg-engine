from __future__ import annotations

from engine.outcome import Band
from engine.turnmodel import (AttackEstimate, AttackResult, Budget, TurnContext,
                         TurnModel)


def roll_pool(dice, pool: int, target: int):
    rolls = [dice.roll(10) for _ in range(max(0, pool))]
    successes = sum(1 for r in rolls if r >= target)
    ones = sum(1 for r in rolls if r == 1)
    return successes, ones, successes - ones, rolls


def band_for_net(successes: int, ones: int, net: int) -> Band:
    if successes == 0 and ones > 0:
        return Band.BOTCH
    if net <= 0:
        return Band.FAILURE
    if net == 1:
        return Band.MARGINAL
    if net <= 4:
        return Band.SUCCESS
    return Band.EXCEPTIONAL


_DEFAULT_ATTACK = {"name": "strike", "attribute": "dexterity",
                   "skill": "brawl", "damage_rating": 1}


class StorytellerTurnModel(TurnModel):
    def __init__(self, ruleset):
        self.rs = ruleset
        self.dice = ruleset.dice

    def initiative_order(self, combatants):
        rolled = []
        for c in combatants:
            attrs = c.sheet.get("attributes", {})
            init = (self.dice.roll(10) + attrs.get("dexterity", 2)
                    + attrs.get("wits", 2) + c.sheet.get("initiative_bonus", 0))
            rolled.append((c, init, attrs.get("wits", 2)))
        rolled.sort(key=lambda t: (-t[1], -t[2], t[0].name))
        return [(c, init) for c, init, _ in rolled]

    def new_turn_budget(self, combatant) -> Budget:
        return Budget(actions=1, bonus=1, reactions=1, movement=1)

    def _pool(self, attacker) -> tuple[int, dict]:
        atk = attacker.sheet.get("attack", _DEFAULT_ATTACK)
        attr = attacker.sheet.get("attributes", {}).get(atk["attribute"], 2)
        skill = attacker.sheet.get("abilities", {}).get(atk["skill"], 0)
        pool = max(1, attr + skill - self.rs.wound_dice_penalty(attacker))
        return pool, atk

    def resolve_attack(self, attacker, defender, *, defending=False,
                       situational_ac=0, situational_hit=0) -> AttackResult:
        if "mist" in defender.statuses:
            return AttackResult(attacker.name, defender.name, False, Band.FAILURE, 0,
                                {"pool": 0, "target": 0, "mist": True})
        pool, atk = self._pool(attacker)
        target = 6 + (1 if defending else 0)
        if "hidden" in defender.statuses:
            target += 2
        if "majesty" in defender.statuses:
            target += 3
        if {"blinded", "confused"} & attacker.statuses:
            target += 2
        successes, ones, net, _ = roll_pool(self.dice, pool, target)
        band = band_for_net(successes, ones, net)
        raw = {"pool": pool, "target": target, "successes": successes,
               "ones": ones, "net": net}
        if band is Band.BOTCH or net <= 0:
            return AttackResult(attacker.name, defender.name, False, band, 0, raw)
        potence = self.rs.discipline_rating(attacker, "Potence")
        claw_forms = {"claws", "beast_form", "shadow", "bonecraft"}
        claws = 3 if "warform" in attacker.statuses else (2 if claw_forms & attacker.statuses else 0)
        soak = defender.sheet.get("soak", 0)
        if {"armored", "warform"} & defender.statuses:
            soak += 2
        levels = max(0, net + atk.get("damage_rating", 1) + potence + claws - soak)
        raw.update(soak=soak, potence=potence, claws=claws, levels=levels)
        return AttackResult(attacker.name, defender.name, True, band, levels, raw)

    def estimate_attack(self, attacker, defender, *, situational_ac=0,
                        situational_hit=0) -> AttackEstimate:
        pool, atk = self._pool(attacker)
        target = 6
        p = (10 - target + 1) / 10
        exp_net = max(0.0, pool * (p - 0.1))
        hit_chance = min(0.95, max(0.05, 1 - (1 - p) ** pool))
        soak = defender.sheet.get("soak", 0)
        potence = self.rs.discipline_rating(attacker, "Potence")
        exp_levels = max(0.0, exp_net + atk.get("damage_rating", 1) + potence - soak)
        remaining = defender.sheet.get("health_max", 7) - defender.sheet.get("health_taken", 0)
        could_drop = exp_levels >= remaining and hit_chance >= 0.4
        return AttackEstimate(hit_chance, exp_levels, could_drop)

    def run_round(self, order, ctx: TurnContext) -> None:
        ctx.begin_round()
        for c in reversed(order):
            if ctx.is_active(c):
                ctx.declare(c)
        for c in order:
            if ctx.combat_over():
                return
            if ctx.is_active(c):
                ctx.announce_turn(c)
                ctx.resolve(c)
