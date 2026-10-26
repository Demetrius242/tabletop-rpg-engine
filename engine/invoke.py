from __future__ import annotations

import re

INVOKE_CUES = {"use", "invoke", "activate", "cast", "channel", "unleash",
               "manifest", "exert", "employ", "evoke", "trigger", "perform", "work"}

POWER_SHORTHANDS = {
    "feral_claws": ("claws", "talons"),
    "mist_form": ("mist",),
    "shape_of_the_beast": ("beast form", "war form", "wolf form", "bat form"),
    "eyes_of_the_beast": ("beast sight",),
    "unseen_presence": ("unseen",),
    "vanish": ("disappear",),
    "mask_of_a_thousand_faces": ("mask",),
    "dread_gaze": ("dread",),
    "forgetful_mind": ("forget",),
    "quell_the_beast": ("quell",),
    "drawing_out_the_beast": ("draw out the beast",),
    "arms_of_the_abyss": ("arms of the abyss", "tentacles"),
    "black_metamorphosis": ("black metamorphosis",),
    "tenebrous_form": ("shadow form",),
    "form_of_the_cobra": ("cobra form", "serpent form"),
    "horrid_form": ("war form",),
}


def normalize(text: str) -> str:
    return " " + re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", (text or "").lower())).strip() + " "


def _aliases(item, shorthands) -> set:
    al = {item.key, item.key.replace("_", " "), item.name.lower()}
    al.update(shorthands.get(item.key, ()))
    return {a for a in al if a}


def match_invocation(text, items, names=(), shorthands=None):
    shorthands = shorthands or {}
    if not items:
        return (None, "", False)
    norm = normalize(text)
    words = norm.split()
    has_cue = bool(set(words) & INVOKE_CUES) or {"discipline", "ritual", "rite"} & set(words)

    matched, multiword = None, False
    pairs = sorted(((a, it) for it in items for a in _aliases(it, shorthands)),
                   key=lambda x: -len(x[0]))
    for alias, item in pairs:
        if f" {alias} " in norm:
            matched, multiword = item, (" " in alias)
            break

    is_exact = norm.strip() in {a for it in items for a in _aliases(it, shorthands)}

    if matched is not None and (has_cue or is_exact or multiword):
        target = next((n for n in names if f" {n.lower()} " in norm), "")
        return (matched, target, True)

    explicit = (bool({"discipline", "power", "ritual", "rite"} & set(words))
                or (bool(words) and words[0] in INVOKE_CUES and len(words) <= 4))
    return (None, "", explicit)
