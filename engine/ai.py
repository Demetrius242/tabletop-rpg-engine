from __future__ import annotations

import random

from .turnmodel import Attack, Defend, Pass

KILL_BONUS = 100.0
FOCUS_WEIGHT = 8.0
PRIORITY_BONUS = 50.0
SELF_PRESERVE_HP = 0.25


def choose_action(fighter, opponents, allies, ruleset, turn_model, rng=None,
                  priority_target: str | None = None):
    rng = rng or random.Random()
    if not opponents:
        return Pass()

    intelligence = int(fighter.combatant.sheet.get("intelligence", 2))

    if (fighter.side == "party" and intelligence >= 3
            and ruleset.health_fraction(fighter.combatant) < SELF_PRESERVE_HP
            and rng.random() < 0.5):
        return Defend()

    scored = []
    for opp in opponents:
        est = turn_model.estimate_attack(fighter.combatant, opp.combatant)
        score = est.hit_chance * est.expected_damage
        if est.could_drop:
            score += KILL_BONUS
        score += (1.0 - ruleset.health_fraction(opp.combatant)) * FOCUS_WEIGHT
        if priority_target and opp.combatant.name == priority_target:
            score += PRIORITY_BONUS
        scored.append((score, opp))

    scored.sort(key=lambda t: -t[0])
    n = max(1, min(intelligence, len(scored)))
    top = scored[:n]
    weights = [max(0.01, s) for s, _ in top]
    chosen = rng.choices([o for _, o in top], weights=weights, k=1)[0]
    return Attack(chosen.combatant)
