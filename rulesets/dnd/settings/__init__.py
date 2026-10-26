from rulesets.dnd.settings.base import Location, NPCCard, Setting, WorldConcept
from rulesets.dnd.settings.forgotten_realms import FORGOTTEN_REALMS

SETTINGS = {FORGOTTEN_REALMS.key: FORGOTTEN_REALMS}
DEFAULT = FORGOTTEN_REALMS.key
ORDER = (FORGOTTEN_REALMS.key,)


def get(key):
    return SETTINGS.get((key or "").lower())


__all__ = ["Setting", "Location", "NPCCard", "WorldConcept",
           "SETTINGS", "DEFAULT", "ORDER", "get", "FORGOTTEN_REALMS"]
