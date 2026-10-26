from __future__ import annotations

from dataclasses import dataclass, field

from engine.outcome import Band
from rulesets.storyteller.core.storyteller_combat import band_for_net, roll_pool

_PROTECTIONS = {"true_faith", "warded", "sanctified", "blessed", "consecrated"}


@dataclass(frozen=True)
class Ritual:
    tradition: str
    level: int
    key: str
    name: str
    summary: str
    ingredients: tuple = ()
    scope: str = "self"
    token: str = ""
    target_kind: str = ""
    yes_cue: str = ""
    no_cue: str = ""


@dataclass
class RiteResult:
    ok: bool
    success: bool = False
    reason: str = ""
    missing: tuple = ()
    consumed: tuple = ()
    cue: str = ""
    band: object = None


_RITUALS = [
    Ritual("Thaumaturgy", 1, "wake_with_evenings_freshness", "Wake with Evening's Freshness",
           "Rouse from day-sleep at the first sign of danger.", ingredients=(),
           scope="self", token="wakeful",
           yes_cue="{a} sets the rite so the day's sleep will not hold them past danger."),
    Ritual("Thaumaturgy", 1, "deflection_of_wooden_doom", "Deflection of Wooden Doom",
           "Turn aside the next stake aimed at the heart.", ingredients=("splinter",),
           scope="self", token="stake_warded",
           yes_cue="a sliver of warded wood now guards {a}'s heart against the stake."),
    Ritual("Thaumaturgy", 2, "defense_of_the_sacred_haven", "Defense of the Sacred Haven",
           "Bar daylight from a chosen haven.", ingredients=("ash", "silver_dust"),
           scope="area", token="sun_shielded",
           yes_cue="sunlight will no longer cross the threshold of this place."),
    Ritual("Thaumaturgy", 2, "blood_walk", "Blood Walk",
           "Read a vampire's lineage and name from their blood.", ingredients=("vial_of_blood",),
           scope="target", token="",
           yes_cue="the blood gives up {t}'s sire, lineage, and true name to {a}."),
    Ritual("Thaumaturgy", 2, "ward_versus_ghouls", "Ward versus Ghouls",
           "Sear a sigil that ghouls cannot cross.", ingredients=("vial_of_blood", "salt"),
           scope="target", token="ghoul_warded", target_kind="ghoul",
           yes_cue="the sigil flares; {t} the ghoul recoils and cannot approach it."),
    Ritual("Thaumaturgy", 3, "incantation_of_the_shepherd", "Incantation of the Shepherd",
           "Sense the location of your mortal herd.", ingredients=("lock_of_hair",),
           scope="self", token="",
           yes_cue="{a} feels the scattered pull of every soul in their herd."),
    Ritual("Thaumaturgy", 4, "pavis_of_foul_presence", "Pavis of Foul Presence",
           "Turn a foe's own Presence back upon them.", ingredients=("mirror_shard",),
           scope="self", token="presence_ward",
           yes_cue="{a} is sheathed so that another's Presence will rebound on its caster."),

    Ritual("Necromancy", 1, "call_of_the_hungry_dead", "Call of the Hungry Dead",
           "Make a victim hear the ceaseless babble of the dead.", ingredients=("grave_dirt",),
           scope="target", token="haunted",
           yes_cue="the drowned voices of the dead crowd into {t}'s ears, drowning all else."),
    Ritual("Necromancy", 2, "eldritch_beacon", "Eldritch Beacon",
           "Light a lure that draws wraiths to a place.", ingredients=("black_candle",),
           scope="area", token="death_beacon",
           yes_cue="a cold beacon only the dead can see now burns here, and they come."),
    Ritual("Necromancy", 3, "ritual_of_the_unearthed_fetter", "Ritual of the Unearthed Fetter",
           "Find the object that anchors a ghost to the world.", ingredients=("bone", "black_candle"),
           scope="target", token="",
           yes_cue="the rite reveals the fetter that binds {t}'s ghost to the lands of the living."),
    Ritual("Necromancy", 4, "cadaverous_animation", "Cadaverous Animation",
           "Raise a corpse as a shambling servant.", ingredients=("corpse", "grave_dirt"),
           scope="area", token="risen_dead",
           yes_cue="the corpse shudders, rises, and turns its empty face toward {a} for orders."),
]

RITUALS = {r.key: r for r in _RITUALS}
RITUAL_LIST = tuple(_RITUALS)


def rituals_in(tradition: str) -> list:
    return [r for r in _RITUALS if r.tradition.lower() == tradition.lower()]


def _consume(actor, ingredients) -> tuple:
    inv = list(actor.sheet.get("inventory", []))
    for item in ingredients:
        if item in inv:
            inv.remove(item)
    actor.sheet["inventory"] = inv
    return tuple(ingredients)


def perform_ritual(rs, actor, key, target=None) -> RiteResult:
    rite = RITUALS.get(key)
    if rite is None:
        return RiteResult(False, reason="unknown_rite")
    if key not in set(actor.sheet.get("known_rituals", ())):
        return RiteResult(False, reason="not_known",
                          cue=f"{actor.name} has never learned the {rite.name}.")

    inv = list(actor.sheet.get("inventory", ()))
    missing = tuple(i for i in rite.ingredients if i not in inv)
    if missing:
        return RiteResult(False, reason="missing_ingredients", missing=missing,
                          cue=f"{actor.name} lacks what the rite demands: {', '.join(missing)}.")

    consumed = _consume(actor, rite.ingredients)

    pool = max(1, actor.sheet.get("attributes", {}).get("intelligence", 2)
               + actor.sheet.get("abilities", {}).get("occult", 0))
    s, o, net, _ = roll_pool(rs.dice, pool, min(9, rite.level + 3))
    band = band_for_net(s, o, net)
    if band is Band.BOTCH or net <= 0:
        return RiteResult(True, success=False, band=band, consumed=consumed,
                          cue=(rite.no_cue or f"the {rite.name} unravels; the materials are spent for nothing."))

    if target is not None:
        if (_PROTECTIONS & set(target.statuses)) or target.sheet.get("true_faith"):
            return RiteResult(True, success=False, reason="protected", band=band, consumed=consumed,
                              cue=f"the {rite.name} completes -- but {target.name} is shielded, and nothing takes hold.")
        if rite.target_kind and target.sheet.get("kind") != rite.target_kind:
            return RiteResult(True, success=False, reason="wrong_target", band=band, consumed=consumed,
                              cue=f"the {rite.name} finds no purchase on {target.name}.")

    if rite.token:
        if rite.scope == "self":
            actor.statuses.add(rite.token)
        elif rite.scope == "target" and target is not None:
            target.statuses.add(rite.token)
        elif rite.scope == "area":
            actor.sheet.setdefault("scene_effects", []).append(rite.token)
    a = actor.name
    t = target.name if target is not None else "the target"
    return RiteResult(True, success=True, band=band, consumed=consumed,
                      cue="RESULT: " + (rite.yes_cue or f"the {rite.name} takes hold").format(a=a, t=t) + ".")
