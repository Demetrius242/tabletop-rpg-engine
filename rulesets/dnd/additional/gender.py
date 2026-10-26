from __future__ import annotations

from engine.events import GenderShift

GENDERS = ("male", "female", "androgynous", "non_applicable")
MENTAL = frozenset({"int", "wis", "cha"})
DISSONANCE_RESTS = 2


def init(sheet: dict, gender: str = "androgynous") -> dict:
    sheet.setdefault("gender_initial", gender)
    sheet.setdefault("gender_current", gender)
    sheet.setdefault("gender_dissonance", 0)
    return sheet


def has(sheet: dict) -> bool:
    return "gender_current" in sheet


def dissonant(sheet: dict) -> bool:
    return int(sheet.get("gender_dissonance", 0)) > 0


def set_gender(actor, new_gender: str, *, dissonance_rests: int = DISSONANCE_RESTS,
               presenter=None) -> dict:
    sheet = actor.sheet
    if new_gender not in GENDERS:
        return {"ok": False, "message": f"unknown gender {new_gender!r}"}
    before = sheet.get("gender_current", "androgynous")
    sheet["gender_current"] = new_gender
    changed = new_gender != before
    if changed:
        sheet["gender_dissonance"] = max(int(sheet.get("gender_dissonance", 0)), dissonance_rests)
    if presenter is not None and changed:
        presenter.emit(GenderShift(actor.name, before, new_gender,
                                   dissonance_rests=sheet["gender_dissonance"]))
    return {"ok": True, "before": before, "after": new_gender, "changed": changed,
            "dissonance_rests": sheet.get("gender_dissonance", 0)}


def settle(sheet: dict) -> dict:
    if sheet.get("gender_dissonance", 0) > 0:
        sheet["gender_dissonance"] = max(0, sheet["gender_dissonance"] - 1)
        return {"gender_dissonance": sheet["gender_dissonance"]}
    return {}
