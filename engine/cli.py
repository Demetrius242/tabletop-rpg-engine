from __future__ import annotations

import textwrap

from .events import (AttackResolved, BloodSpent, CelerityActivated, CharacterCreated,
                     CombatEnded, CombatStarted, Defended, Event, EventTransition, Fled, Frenzied,
                     Healed, HumanityShift, Menu, Moved, MoraleBroke, Narration,
                     OrderIssued, PowerUsed, RiteCast, SessionEnd, SocialResolved,
                     StateDelta, StoryBeat, SystemMessage, TaskUpdated, TurnStarted)


class CliPresenter:
    def __init__(self, width: int = 88, show_state_deltas: bool = False):
        self.width = width
        self.show_state_deltas = show_state_deltas

    def emit(self, event: Event) -> None:
        if isinstance(event, Narration):
            print("\n" + self._wrap(event.text) + "\n")
        elif isinstance(event, SystemMessage):
            print(f"  \u00b7 {event.text}")
        elif isinstance(event, Menu):
            print("  " + event.prompt)
            for i, opt in enumerate(event.options, 1):
                print(f"    {i}. {opt}")
        elif isinstance(event, CombatStarted):
            print(f"\n\u2694  Combat! Initiative: {', '.join(event.order)}")
        elif isinstance(event, TurnStarted):
            print(f"  \u2014 {event.name}'s turn \u2014")
        elif isinstance(event, AttackResolved):
            if self.show_state_deltas:
                tag = "OA " if event.raw.get("opportunity") else ""
                verb = "crit!" if event.crit else ("hit" if event.hit else "miss")
                print(f"    [{tag}{event.attacker} -> {event.defender}: {verb} "
                      f"{event.damage} dmg; {event.defender_condition}]")
        elif isinstance(event, Moved):
            if self.show_state_deltas:
                prov = " (provoked!)" if event.provoked else ""
                print(f"    [{event.name}: {event.from_zone} -> {event.to_zone}{prov}]")
        elif isinstance(event, Defended):
            if self.show_state_deltas:
                print(f"    [{event.name} defends]")
        elif isinstance(event, OrderIssued):
            if not event.delivered:
                print(f"  \u00b7 {event.by}'s order to {event.to} doesn't get through.")
            elif self.show_state_deltas:
                tgt = f" {event.target}" if event.target else ""
                print(f"    [{event.by} orders {event.to}: {event.directive}{tgt}]")
        elif isinstance(event, SocialResolved):
            if not event.delivered:
                print(f"  \u00b7 {event.by}'s words don't reach {event.target}.")
            elif self.show_state_deltas:
                print(f"    [{event.by} {event.mode} {event.target}: "
                      f"{event.band} -> {event.effect}]")
        elif isinstance(event, MoraleBroke):
            print(f"  \u00b7 {event.name} {event.outcome}!")
        elif isinstance(event, Fled):
            print(f"  \u00b7 {event.name} escapes the fight.")
        elif isinstance(event, CombatEnded):
            who = {"party": "You prevail", "enemies": "You are defeated",
                   "fled": "You escape"}.get(event.victor, event.victor)
            print(f"\n\u2694  {who}.")
        elif isinstance(event, CharacterCreated):
            print(f"\n\u2726  {event.name} is ready. {event.summary}\n")
        elif isinstance(event, CelerityActivated):
            plural = "s" if event.extra_actions != 1 else ""
            print(f"    \u00bb {event.name} blurs \u2014 {event.extra_actions} extra "
                  f"action{plural} this turn.")
        elif isinstance(event, Frenzied):
            print(f"    \u203c {event.name} loses control \u2014 the Beast takes over!")
        elif isinstance(event, PowerUsed):
            if not event.ok:
                why = {"insufficient_dots": "not learned deeply enough",
                       "not_enough_blood": "not enough blood",
                       "blood_too_strong": "the blood is too strong",
                       "no_eye_contact": "no eye contact",
                       "target_unreachable": "the mind is closed",
                       "no_line_of_sight": "no clear line",
                       "cannot_hear": "they cannot hear you",
                       "no_target": "no target",
                       "target_down": "the target is down"}.get(event.reason, "it won't come")
                print(f"    \u00b7 {event.name}'s {event.power} fails \u2014 {why}.")
            elif event.success:
                tgt = f" on {event.target}" if event.target else ""
                print(f"    \u272a {event.name} invokes {event.power}{tgt}.")
            else:
                print(f"    \u00b7 {event.name}'s {event.power} is resisted.")
        elif isinstance(event, RiteCast):
            if not event.ok:
                if event.reason == "missing_ingredients":
                    miss = ", ".join(event.missing) or "materials"
                    print(f"    \u00b7 {event.name} cannot perform {event.rite} \u2014 missing: {miss}.")
                elif event.reason == "not_known":
                    print(f"    \u00b7 {event.name} has not learned {event.rite}.")
                else:
                    print(f"    \u00b7 {event.name} cannot perform {event.rite}.")
            elif event.success:
                tgt = f" on {event.target}" if event.target else ""
                print(f"    \u2756 {event.name} performs {event.rite}{tgt}.")
            elif event.reason == "protected":
                print(f"    \u00b7 {event.name} performs {event.rite}, but {event.target} is shielded \u2014 no effect.")
            else:
                print(f"    \u00b7 {event.name}'s {event.rite} fails to take.")
        elif isinstance(event, Healed):
            if event.levels:
                print(f"    + {event.name} knits flesh, mending {event.levels} level(s).")
        elif isinstance(event, BloodSpent):
            note = f" ({event.purpose})" if event.purpose else ""
            print(f"    \u00b7 {event.name} spends {event.amount} blood{note}; "
                  f"{event.remaining} left.")
        elif isinstance(event, HumanityShift):
            if event.lost:
                tail = " A derangement takes root." if event.derangement else ""
                print(f"    \u2620 {event.name}'s {event.trait} slips to "
                      f"{event.after}.{tail}")
            else:
                print(f"    \u00b7 {event.name} feels the weight, but {event.trait} holds.")
        elif isinstance(event, StateDelta):
            if self.show_state_deltas:
                print(f"  ~ {event.summary}")
        elif isinstance(event, StoryBeat):
            print(self._wrap(event.text))
        elif isinstance(event, EventTransition):
            print(f"\n=== {event.title} ===")
        elif isinstance(event, TaskUpdated):
            print(f"  \u25c9 {event.summary or event.task} \u2014 {event.state}")
        elif isinstance(event, SessionEnd):
            print(f"\n\u2014 {event.reason} \u2014")

    def read_action(self) -> str:
        return input("> ")

    def _wrap(self, text: str) -> str:
        out = []
        for para in text.split("\n"):
            out.append(textwrap.fill(para, width=self.width) if para.strip() else "")
        return "\n".join(out)
