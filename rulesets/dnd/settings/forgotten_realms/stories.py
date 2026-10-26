from __future__ import annotations

from rulesets.dnd.settings.forgotten_realms.oota_story import build_oota_ch1

ADVENTURES = {
    "oota_ch1": build_oota_ch1,
}


def build(key: str):
    factory = ADVENTURES.get((key or "").lower())
    return factory() if factory else None


def list_adventures() -> list:
    return [
        {"key": "oota_ch1", "name": "Out of the Abyss -- Escape from Velkynvelve",
         "blurb": ("Break the drow slave pens of Velkynvelve, flee into the Underdark, and reach "
                   "Sloobludop or Gracklstugh. A Chapter 1 vertical slice. Party: Sarith (ranger), "
                   "Ront (barbarian), Pog (rogue).")},
    ]
