from rulesets.dnd.settings.base import Setting
from rulesets.dnd.settings.forgotten_realms.tradesmen import TRADESMEN
from rulesets.dnd.settings.forgotten_realms.world import (
    _CONCEPTS, _LOCATIONS, _NARRATION_ANGLE, _NPCS, _SIGHTS)

FORGOTTEN_REALMS = Setting(
    key="forgotten_realms",
    name="The Forgotten Realms (Sword Coast & Underdark)",
    tone="heroic high fantasy with frontier grit; dark survival in the Underdark",
    narration_angle=_NARRATION_ANGLE,
    concepts=_CONCEPTS,
    sights=_SIGHTS,
    locations=_LOCATIONS,
    npcs=_NPCS,
    tradesmen=TRADESMEN,
)

__all__ = ["FORGOTTEN_REALMS"]
