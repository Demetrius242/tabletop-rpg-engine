from __future__ import annotations

from dataclasses import dataclass, field

from .events import CharacterCreated, Menu, SystemMessage
from .state import Combatant


@dataclass(frozen=True)
class Option:
    key: str
    label: str
    detail: str = ""


@dataclass(frozen=True)
class Step:
    key: str
    prompt: str
    kind: str
    options: tuple = ()
    pool: tuple = ()
    slots: tuple = ()
    count: int = 0
    dynamic: bool = False


def _resolve(raw: str, labels) -> int | None:
    raw = raw.strip()
    if raw.isdigit():
        i = int(raw) - 1
        if 0 <= i < len(labels):
            return i
    low = raw.lower()
    for i, lab in enumerate(labels):
        if lab.lower() == low:
            return i
    hits = [i for i, lab in enumerate(labels) if lab.lower().startswith(low)] if low else []
    return hits[0] if len(hits) == 1 else None


def _resolve_many(raw: str, labels, need: int):
    for parts in ([p for p in raw.split(",")], raw.split()):
        toks = [p.strip() for p in parts if p.strip()]
        if len(toks) != need:
            continue
        idxs = [_resolve(t, labels) for t in toks]
        if all(i is not None for i in idxs) and len(set(idxs)) == need:
            return idxs
    return None


def _pick_value(raw: str, vals) -> int | None:
    raw = raw.strip()
    if raw in vals:
        return vals.index(raw)
    if raw.isdigit():
        i = int(raw) - 1
        if 0 <= i < len(vals):
            return i
    return None


class CharacterCreator:

    def __init__(self, presenter, ruleset):
        self.presenter = presenter
        self.ruleset = ruleset

    def run(self) -> Combatant:
        self.presenter.emit(SystemMessage("Let's make your character."))
        selections: dict = {}
        for step in self.ruleset.creation_spec():
            selections[step.key] = self._step(step, selections)
        pc = self.ruleset.build_pc(selections)
        self._summary(pc)
        return pc

    def _options_for(self, step: Step, selections: dict) -> tuple:
        if step.dynamic:
            dyn = self.ruleset.options_for(step.key, selections)
            if dyn:
                return tuple(dyn)
        return step.options

    def _step(self, step: Step, selections: dict):
        if step.kind == "text":
            return self._text(step)
        if step.kind == "choose_one":
            return self._choose_one(step, selections)
        if step.kind == "choose_many":
            return self._choose_many(step, selections)
        if step.kind == "assign":
            return self._assign(step)
        raise ValueError(f"unknown creation step kind: {step.kind!r}")

    def _text(self, step: Step) -> str:
        while True:
            self.presenter.emit(SystemMessage(step.prompt))
            raw = self.presenter.read_action().strip()
            if raw:
                return raw
            self.presenter.emit(SystemMessage("Please enter a value."))

    def _choose_one(self, step: Step, selections: dict) -> str:
        options = self._options_for(step, selections)
        labels = [o.label for o in options]
        menu = [f"{o.label} -- {o.detail}" if o.detail else o.label for o in options]
        while True:
            self.presenter.emit(Menu(step.prompt, menu))
            i = _resolve(self.presenter.read_action(), labels)
            if i is not None:
                return options[i].key
            self.presenter.emit(SystemMessage("Pick one of the listed options (number or name)."))

    def _choose_many(self, step: Step, selections: dict) -> list:
        options = self._options_for(step, selections)
        labels = [o.label for o in options]
        menu = [f"{o.label} -- {o.detail}" if o.detail else o.label for o in options]
        need = step.count or self.ruleset.count_for(step.key, selections) or 1
        while True:
            self.presenter.emit(Menu(f"{step.prompt} (choose {need})", menu))
            picks = _resolve_many(self.presenter.read_action(), labels, need)
            if picks is not None:
                return [options[i].key for i in picks]
            self.presenter.emit(SystemMessage(
                f"Choose exactly {need}, comma- or space-separated (numbers or names), no repeats."))

    def _assign(self, step: Step) -> dict:
        remaining = list(step.pool)
        result: dict = {}
        for slot in step.slots:
            while True:
                vals = [str(v) for v in remaining]
                self.presenter.emit(Menu(f"{step.prompt} -> {slot.label}", vals))
                i = _pick_value(self.presenter.read_action(), vals)
                if i is not None:
                    result[slot.key] = remaining.pop(i)
                    break
                self.presenter.emit(SystemMessage("Choose one of the remaining values."))
        return result

    def _summary(self, pc: Combatant) -> None:
        s = pc.sheet
        ab = s.get("abilities", {})
        scores = ", ".join(f"{k.upper()} {v}" for k, v in ab.items())
        bits = [b for b in (s.get("ancestry", ""), s.get("class", "")) if b]
        line = (f"{' '.join(bits)} | HP {s.get('max_hp', '?')}, AC {s.get('ac', '?')}"
                f" | {scores}")
        self.presenter.emit(CharacterCreated(name=pc.name, summary=line))
