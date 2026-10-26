from __future__ import annotations

from rulesets.dnd.settings.base import Location, WorldConcept

ADVENTURE = "out_of_the_abyss"

_UNDERDARK_NARRATION = (
    "Beneath the Sword Coast lies the Underdark: dark survival fantasy in endless caverns. The surface "
    "is a half-remembered dream; faerzress-purple stone, bioluminescent fungus, and distant water "
    "measure time. Drow slavers, duergar forges, mad kuo-toa prophets, and myconid groves are "
    "civilizations carved from horror. Escaped prisoners and unlikely allies steal every rest; every "
    "light is a beacon for worse things. Evoke claustrophobia, wonder, and moral corrosion -- kindness "
    "is precious because it is rare. Demons whisper from the depths. Hope is a torch you fear to raise."
)

_CONCEPTS = (
    WorldConcept("Faerzress",
                 "Wild magic bleeding from the stone; it fouls teleportation and feeds demon lords' "
                 "attention to those who linger too long in its glare."),
    WorldConcept("Drow cruelty",
                 "Menzoberranzan's children rule through Lolth's web -- priestesses, poison, and slavery "
                 "are prayer made policy."),
    WorldConcept("Escape and alliance",
                 "Prisoners of Velkynvelve and worse pits must trust monsters, madmen, and each other "
                 "to climb toward a surface that may not want them back."),
    WorldConcept("Demon lords stir",
                 "The Abyss reaches upward; cults, shards, and dreams of princes promise power at the "
                 "price of everything."),
    WorldConcept("Survival economy",
                 "Fungus, fish, and slave labor feed the dark; coin is rare, favors are currency, and "
                 "a loaf of sane bread is a treasure."),
)

_SIGHTS = (
    ("Velkynvelve",
     "A drow outpost hung on a chasm wall -- slave pens, spider silk bridges, and priestesses who "
     "call cruelty devotion."),
    ("Sloobludop",
     "A kuo-toa village on the Darklake where prophets declare gods into being and everyone smiles "
     "with too many teeth."),
    ("Gracklstugh",
     "The City of Blades -- duergar forges that never cool, smoke that tastes of iron, and kings "
     "who bargain in slaves and steel."),
    ("Menzoberranzan",
     "The spider capital -- a thousand spires of malice where matron mothers plot in whispers."),
    ("Blingdenstone",
     "A svirfneblin refuge of stone and silence, hidden behind illusions and grit."),
    ("The Wormwrithings",
     "Tunnels where purple worms have chewed passages the size of cathedrals."),
)

_LOCATIONS = {
    "velkynvelve_chasm": Location(
        "velkynvelve_chasm", "Velkynvelve Slave Pens", "dungeon",
        "A tiered cavern of iron cages and spider-silk walkways over a bottomless chasm; the air "
        "smells of sweat, fungus stew, and priestly incense.",
        "captive, watchful, cruel",
        hooks=("a quaggoth bellows in the pits", "a drow overseer counts heads at dusk",
               "a loose stone might reach the rope bridge"),
        adventure=ADVENTURE),
    "darklake_shore": Location(
        "darklake_shore", "The Darklake at Night", "harbor",
        "Black water lapping stone, boat-lanterns like drowning stars; something vast ripples far out.",
        "restless and murmuring",
        hooks=("kuo-toa skiffs offer passage -- at a price", "a duergar barge demands papers",
               "the water is not empty"),
        adventure=ADVENTURE),
    "gracklstugh_foundry": Location(
        "gracklstugh_foundry", "Gracklstugh Foundry Quarter", "street",
        "Avenues of soot and hammerfall; duergar guards watch every anvil, and the heat never fades.",
        "industrial, oppressive, watchful",
        hooks=("a writ of passage can be bought -- or stolen", "slaves haul ore under guard",
               "the Deepking's tax collectors take heads as well as coin"),
        adventure=ADVENTURE),
    "fungal_grove": Location(
        "fungal_grove", "A Myconid Fungal Grove", "forest",
        "Towering mushrooms and pale spore haze; telepathic welcome tastes like damp earth.",
        "hushed, alien, oddly peaceful",
        hooks=("spore servants offer guidance", "a patch of violet fungus sings",
               "something herd-large moves just out of sight"),
        adventure=ADVENTURE),
    "drow_patrol_tunnel": Location(
        "drow_patrol_tunnel", "A Drow Patrol Tunnel", "street",
        "A narrow passage with hidden murder-holes and phosphor moss; bootfalls echo a long way.",
        "tense and lethal",
        hooks=("a patrol is due in minutes", "a side crevice smells of escape",
               "crossbow bolts wait in the dark"),
        adventure=ADVENTURE),
    "sloobludop_plaza": Location(
        "sloobludop_plaza", "Sloobludop's Plaza of New Gods", "temple",
        "Mud and fish-gut idols; kuo-toa priests paint fresh divinity on wet stone each dawn.",
        "mad, humid, devout in the worst way",
        hooks=("a prophet names a party member god", "a blood sacrifice is scheduled at dusk",
               "Bloppblippolp's statue weeps slime"),
        adventure=ADVENTURE),
    "wormwrithing_tunnel": Location(
        "wormwrithing_tunnel", "The Wormwrithings", "ruin",
        "A tunnel wide enough for a castle, walls ribbed as if chewed; distant tremors never quite stop.",
        "vast and predatory",
        hooks=("a purple worm's passage is fresh", "a crevasse hides a camp",
               "something glitters in the rubble -- bait, perhaps"),
        adventure=ADVENTURE),
    "blingdenstone_gate": Location(
        "blingdenstone_gate", "Blingdenstone Outer Gate", "tower",
        "A illusion-shrouded stone arch; deep gnome guards read your face as much as your weapons.",
        "wary but not heartless",
        hooks=("asylum for fugitives -- if trusted", "a mind flayer threat is discussed in whispers",
               "a trader sells sober gear at inflated prices"),
        adventure=ADVENTURE),
    "underdark_camp": Location(
        "underdark_camp", "A Hidden Underdark Camp", "tavern",
        "A sheltered ledge, a cookfire of fungus caps, bedrolls and watch rotations -- home, for now.",
        "fragile warmth",
        hooks=("a companion confesses a secret", "scouts report drow movement",
               "the food tastes of fear and pepper"),
        adventure=ADVENTURE),
    "abyssal_rift": Location(
        "abyssal_rift", "An Abyssal Rift", "ruin",
        "Reality thins to violet madness; whispers offer power and the air tastes of copper.",
        "apocalyptic and seductive",
        hooks=("a demon shard pulses nearby", "visions of a throne beneath the lake",
               "faerzress flares and magic stutters"),
        adventure=ADVENTURE),
}
