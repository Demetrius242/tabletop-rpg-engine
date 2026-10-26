from __future__ import annotations

from engine.dice import average_notation, dice_only, roll_notation
from engine.outcome import Band
from engine.turnmodel import (AttackEstimate, AttackResult, Budget, TurnContext,
                         TurnModel)

DEFEND_AC_BONUS = 2


class DnDTurnModel(TurnModel):
    def __init__(self, ruleset):
        self.rs = ruleset
        self.dice = ruleset.dice

    def initiative_order(self, combatants):
        rolled = []
        for c in combatants:
            dex = c.sheet.get("abilities", {}).get("dex", 10)
            init = self.dice.roll(20) + self.rs._ability_mod(dex)
            rolled.append((c, init, self.rs._ability_mod(dex)))
        rolled.sort(key=lambda t: (-t[1], -t[2], t[0].name))
        return [(c, init) for c, init, _ in rolled]

    def new_turn_budget(self, combatant) -> Budget:
        return Budget(actions=1, bonus=1, reactions=1, movement=1)

    @staticmethod
    def _attack_of(c) -> dict:
        attacks = c.sheet.get("attacks") or []
        if attacks:
            return attacks[0]
        return {"name": "strike", "bonus": 2, "damage": "1d4"}

    def resolve_attack(self, attacker, defender, *, defending=False,
                       situational_ac=0, situational_hit=0) -> AttackResult:
        atk = self._attack_of(attacker)
        bonus = int(atk.get("bonus", 0)) + situational_hit
        ac = (defender.sheet.get("ac", 10)
              + (DEFEND_AC_BONUS if defending else 0)
              + situational_ac)
        roll = self.dice.roll(20)
        total = roll + bonus
        raw = {"roll": roll, "bonus": bonus, "ac": ac, "total": total}

        if roll == 1:
            return AttackResult(attacker.name, defender.name, False, Band.BOTCH, 0, raw)
        crit = roll == 20
        if not (crit or total >= ac):
            return AttackResult(attacker.name, defender.name, False, Band.FAILURE, 0, raw)

        dmg = roll_notation(self.dice, atk["damage"])
        if crit:
            dmg += roll_notation(self.dice, dice_only(atk["damage"]))
            band = Band.CRITICAL
        elif total >= ac + 10:
            band = Band.EXCEPTIONAL
        else:
            band = Band.SUCCESS
        raw["damage"] = dmg
        return AttackResult(attacker.name, defender.name, True, band, dmg, raw)

    def estimate_attack(self, attacker, defender, *, situational_ac=0,
                        situational_hit=0) -> AttackEstimate:
        atk = self._attack_of(attacker)
        bonus = int(atk.get("bonus", 0)) + situational_hit
        ac = defender.sheet.get("ac", 10) + situational_ac
        hit_chance = min(0.95, max(0.05, (21 - (ac - bonus)) / 20))
        avg = average_notation(atk["damage"])
        hp = defender.sheet.get("hp", 1)
        could_drop = avg >= hp and hit_chance >= 0.4
        return AttackEstimate(hit_chance, avg, could_drop)

    def run_round(self, order, ctx: TurnContext) -> None:
        for c in order:
            if ctx.combat_over():
                return
            if not ctx.is_active(c):
                continue
            ctx.begin_turn(c)
            ctx.take_turn(c)
