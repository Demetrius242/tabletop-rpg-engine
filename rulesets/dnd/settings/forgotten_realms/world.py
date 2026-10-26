from __future__ import annotations

from rulesets.dnd.settings.base import Location, NPCCard, WorldConcept

from rulesets.dnd.settings.forgotten_realms.underdark_world import (
    _CONCEPTS as _UNDERDARK_CONCEPTS,
    _LOCATIONS as _UNDERDARK_LOCATIONS,
    _SIGHTS as _UNDERDARK_SIGHTS,
    _UNDERDARK_NARRATION,
)

_NARRATION_ANGLE = (
    "Heroic high fantasy with a frontier edge. Magic is real and wondrous but uncommon enough that "
    "ordinary folk fear and revere it; the gods are present and their priests work small miracles. "
    "The Sword Coast is a chain of proud, cosmopolitan city-states strung along a dangerous "
    "wilderness of forests, moors, and monster-haunted ruins. Adventurers are known but not trusted "
    "-- coin, faith, and steel rule, and a friendly tavern can sit a day's ride from a dragon's "
    "lair. Evoke wonder and peril, warmth and grit; lean toward hope and consequence, not grimdark "
    "nihilism. Keep the everyday textured (mud, lamplight, sea-salt, temple bells) so the marvelous "
    "lands harder.\n\n"
    + _UNDERDARK_NARRATION
)

_CONCEPTS = (
    WorldConcept("The Weave and Mystra",
                 "All arcane magic flows through the Weave, the goddess Mystra's gift; wizards study "
                 "it, sorcerers are born to it, and to abuse it is to court ruin."),
    WorldConcept("The Gods are present",
                 "Faerun's many gods take an active hand. Tymora (luck), Sune (beauty and love), "
                 "Tempus (war), Lathander (dawn and renewal), Helm (guardians), and shadowed Shar "
                 "and tyrant Bane are all worshipped openly; clerics and paladins channel real divine power."),
    WorldConcept("The Sword Coast",
                 "A frontier of independent cities -- Waterdeep, Baldur's Gate, Neverwinter -- linked "
                 "by the Trade Way and the sea, ringed by wild country where law thins to nothing."),
    WorldConcept("The factions",
                 "Shadow wars run beneath daily life: the Harpers (secret do-gooders), the Lords' "
                 "Alliance (the cities' pact), the Emerald Enclave (wardens of the wild), the Order "
                 "of the Gauntlet (militant faithful), and the mercenary, ruthless Zhentarim."),
    WorldConcept("Adventurers and peril",
                 "Sellswords and sages take Charters to delve ruins and break cults; monsters, "
                 "drow from the Underdark, and dragons are rare but real, and a single quest can "
                 "tip a town's fate."),
    WorldConcept("A cosmopolitan world",
                 "Humans, elves, dwarves, halflings, tieflings, dragonborn and more share the cities "
                 "with little remark; prejudice exists but trade and necessity blur old lines."),
) + _UNDERDARK_CONCEPTS

_SIGHTS = (
    ("Waterdeep, City of Splendors",
     "The grandest city of the North -- a hundred thousand souls under masked Lords, its wards "
     "rising from teeming Dock Ward to gilded Sea Ward."),
    ("Baldur's Gate",
     "A walled merchant metropolis on the river Chionthar, rich, crowded, and ruled by its Patriars "
     "and the watchful Flaming Fist."),
    ("Neverwinter",
     "The Jewel of the North, rebuilding in the shadow of Mount Hotenow's old eruption."),
    ("Candlekeep",
     "A cliff-top fortress-library where entry is bought with a book found nowhere on its shelves."),
    ("The High Forest",
     "One of the last great primeval woods, ancient, fey-touched, and deep beyond mapping."),
    ("The Underdark",
     "The endless lightless caverns beneath Faerun, home to drow, mind flayers, and worse."),
) + _UNDERDARK_SIGHTS

_LOCATIONS = {
    "waterdeep_night_street": Location(
        "waterdeep_night_street", "A Waterdhavian Street at Night", "street",
        "Lamplight pools on wet cobbles between shuttered shopfronts; somewhere a tavern's warmth "
        "leaks song and lantern-glow, and the City Watch's boots ring two streets over.",
        "tense and watchful, but alive",
        hooks=("a cutpurse marks the party", "a Watch patrol asks pointed questions",
               "a cloaked figure beckons from an alley mouth")),
    "high_forest_deep": Location(
        "high_forest_deep", "Deep in the High Forest", "forest",
        "Ancient trees close overhead until the daylight is green and far away; moss swallows every "
        "sound but your own breath, and the path you were sure of has quietly gone.",
        "hushed and ancient, faintly watching",
        hooks=("fey lights lead off the trail", "an old standing stone hums with the Weave",
               "something large has passed this way recently")),
    "lonely_tower": Location(
        "lonely_tower", "A Lonely Tower on the Moors", "tower",
        "A single spire of weathered stone stands against a bruised sky, its one high window lit; "
        "the wind carries the smell of cold rain and the faint tang of spent magic.",
        "isolated and uncanny",
        hooks=("the door is unbarred and should not be", "wards shimmer at the threshold",
               "a voice answers before you knock")),
    "roadside_tavern": Location(
        "roadside_tavern", "A Trade Way Roadhouse", "tavern",
        "A low timbered inn at a crossroads, fire snapping, ale and stew and the steam of travelers "
        "drying out; talk runs low and every newcomer is weighed at the door.",
        "warm, crowded, and quietly guarded",
        hooks=("a caravan master is hiring guards", "a drunk knows more than he should",
               "two factions eye each other across the room")),
    "harbor_at_dusk": Location(
        "harbor_at_dusk", "A Sword Coast Harbor at Dusk", "harbor",
        "Gulls wheel over a forest of masts as the sun bleeds into the Sea of Swords; nets and "
        "crates and the reek of tar and fish, and sailors' lanterns kindling one by one.",
        "salt-worn and restless",
        hooks=("a ship makes ready to leave on the tide", "a body is pulled from the water",
               "a smuggler offers fast, quiet passage")),
    "ruined_keep": Location(
        "ruined_keep", "A Monster-Haunted Ruin", "ruin",
        "Broken walls and a collapsed gatehouse swallowed by ivy and time; old soot stains the "
        "stones, and something has made a lair in the dark beneath the keep.",
        "desolate and dangerous",
        hooks=("fresh tracks cross the old courtyard", "a cult-mark is daubed on a wall",
               "treasure glints just past where the floor gives way")),
    "temple_of_tymora": Location(
        "temple_of_tymora", "A Temple of Tymora", "temple",
        "A bright, busy shrine to Lady Luck, coins underfoot for fortune, sweet incense and the soft "
        "ring of a prayer-bell; the faithful come to gamble a blessing before the road.",
        "hopeful and a little reckless",
        hooks=("a priest needs a relic recovered", "a desperate gambler prays too hard",
               "a healing is offered -- for a favor")),
}
_LOCATIONS = {**_LOCATIONS, **_UNDERDARK_LOCATIONS}

from .npcs import CARDS as _NPCS
