from __future__ import annotations

import copy
from dataclasses import dataclass

from engine.state import Combatant
from rulesets.dnd.settings.base import NPCCard

ADVENTURE = "out_of_the_abyss"


@dataclass(frozen=True)
class NPCDef:
    card: NPCCard
    sheet: dict


def _oota_card(key, name, role, race="human", **kw):
    return NPCCard(key, name, role, race, adventure=ADVENTURE, **kw)


def _sheet(*, str_=10, dex=10, con=10, int_=10, wis=10, cha=10,
           hp=11, ac=12, pb=2, level=2, klass="commoner", race="human", profs=(),
           attacks=None, creature_type="humanoid", alignment="", alignment_key="",
           gender="non_applicable", intelligence=10, speed=30, tags=(),
           mindless=False, comprehends_language=True) -> dict:
    t = list(tags)
    if ADVENTURE not in t:
        t.append(ADVENTURE)
    s = {
        "abilities": {"str": str_, "dex": dex, "con": con, "int": int_, "wis": wis, "cha": cha},
        "proficiencies": list(profs), "proficiency_bonus": pb,
        "hp": hp, "max_hp": hp, "ac": ac, "speed": speed,
        "level": level, "class": klass, "race": race,
        "attacks": list(attacks or [{"name": "fist", "bonus": 2, "damage": "1d4", "reach": "melee"}]),
        "intelligence": intelligence,
        "creature_type": creature_type, "comprehends_language": comprehends_language,
        "mindless": mindless,
        "alignment": alignment, "alignment_key": alignment_key,
        "gender": gender, "tags": t,
    }
    return s


def _drow_elite(**kw):
    base = dict(str_=13, dex=18, con=14, int_=12, wis=13, cha=11, hp=71, ac=18, pb=3,
                level=5, klass="warrior", race="drow", profs=["perception", "stealth"],
                attacks=[{"name": "shortsword", "bonus": 7, "damage": "2d6+4", "reach": "melee"},
                         {"name": "hand crossbow", "bonus": 7, "damage": "1d6+4", "reach": "ranged"}],
                creature_type="humanoid", alignment="Neutral Evil", alignment_key="ne",
                gender="female", intelligence=12, tags=["drow", ADVENTURE])
    base.update(kw)
    return _sheet(**base)

NPCS: dict[str, NPCDef] = {
    "ilvara_mizzrym": NPCDef(
        card=_oota_card(
            "ilvara_mizzrym", "Ilvara Mizzrym", "drow priestess of Lolth", "drow",
            description="A tall, imperious priestess in spider-silk vestments, silver hair in a high braid, "
                        "eyes like chips of violet ice.",
            demeanor="Serene cruelty; every kindness is a test, every punishment a prayer.",
            voice="Soft, musical, and utterly without mercy; pronounces surface names like insults.",
            mannerisms="Traces Lolth's web in the air while speaking; never raises her voice to shout.",
            dialogue_examples=(
                "Kneel, little moth. Not because I own you -- though I do, down to your breath -- "
                "but because Lolth demands humility, and I enjoy teaching it.",
                "The yochlol was... displeased with my report. Someone will pay for that disappointment. "
                "I have not yet decided whom, which is half the pleasure.",
                "Escape? How charming. The chasm is deep, the dark is patient, and my memory is deeper "
                "than both. Run if you must. I do love a chase.",
                "You may keep your life another day. Consider it a loan with unpleasant interest, "
                "and pray I am in a merciful mood when it comes due.",
                "Jorlan, break something loud for me -- a bone, a spirit, I hardly care. I wish to "
                "hear whether hope still squeaks in this pit.",
            ),
            secret="Summons a yochlol to report to Menzoberranzan; fears demotion more than death.",
            hook="Offers a devil's bargain: serve as bait for escaped slaves and live a week longer."),
        sheet=_sheet(str_=10, dex=14, con=12, int_=13, wis=17, cha=16, hp=71, ac=16,
                     pb=3, level=8, klass="cleric", race="drow",
                     profs=["religion", "insight", "intimidation", "perception"],
                     attacks=[{"name": "scourge", "bonus": 5, "damage": "1d8+2", "reach": "melee"},
                              {"name": "poison ray", "bonus": 7, "damage": "3d6", "reach": "ranged"}],
                     alignment="Neutral Evil", alignment_key="ne", gender="female", intelligence=14,
                     tags=["drow", "divine"])),

    "shoor_vandree": NPCDef(
        card=_oota_card(
            "shoor_vandree", "Shoor Vandree", "drow mage of Velkynvelve", "drow",
            description="A gaunt drow wizard with ink-stained fingers and a spider brooch that moves when bored.",
            demeanor="Intellectual, vain, easily bored by violence he did not cause.",
            voice="Dry and precise; quotes Menzoberranzan court gossip to unsettle listeners.",
            mannerisms="Adjusts invisible cuffs; smiles only when someone else is in pain.",
            dialogue_examples=(
                "Fire is crude, smoke and shouting. I prefer solutions that leave survivors to "
                "describe them in whispers for the rest of their shortened lives.",
                "Ilvara thinks piety wins wars. I think geometry does -- angles, pressure, the elegant "
                "line between alive and useful. We tolerate each other. Barely.",
                "You have the look of a spell component about you. Don't take it personally; "
                "everything is, eventually.",
                "I memorized your heartbeat when you entered my sight. It is faster now. Good. "
                "Fear makes such a readable rhythm.",
                "If you wish to live past supper, be more interesting than the last slave who bored "
                "me. He is currently decorating the fungus garden.",
            ),
            secret="Keeps a sending stone to a rival House wizard; would sell Ilvara for advancement.",
            hook="Might trade a spell scroll for a surface trinket or a secret about a fellow prisoner."),
        sheet=_sheet(str_=9, dex=14, con=12, int_=18, wis=12, cha=14, hp=45, ac=15, pb=3,
                     level=7, klass="wizard", race="drow", profs=["arcana", "deception"],
                     attacks=[{"name": "staff", "bonus": 4, "damage": "1d6+1", "reach": "melee"},
                              {"name": "chill touch", "bonus": 7, "damage": "2d8", "reach": "ranged"}],
                     alignment="Neutral Evil", alignment_key="ne", gender="male", intelligence=18,
                     tags=["drow", "arcane"])),

    "jorlan_duskryn": NPCDef(
        card=_oota_card(
            "jorlan_duskryn", "Jorlan Duskryn", "drow weapons master", "drow",
            description="A scarred drow warrior in mithral-trimmed armor, one ear notched, movements lazy-deadly.",
            demeanor="Professional violence; contemptuous of weakness, oddly fair in a duel.",
            voice="Flat and tired, like a man who has killed too many friends to count strangers.",
            mannerisms="Tests edge balance with a thumb; stands as if leaning on invisible walls.",
            dialogue_examples=(
                "Run, if you like. I'll even give you a head start -- I enjoy the chase more than "
                "the catch, and the catch more than the sermon afterward.",
                "Ilvara wants you broken for Lolth's amusement. I want you to try something stupid "
                "so I have an excuse to hurt you properly. We both win.",
                "That was almost competent. Almost is how most people die down here -- one breath "
                "short of clever, one inch short of fast enough.",
                "I was handsome, before the acid. Don't stare at the scar; it's still an insult, "
                "and I'm still faster than your guilt.",
                "Drop the weapon. Or keep it. I genuinely don't care; the outcome amuses me either "
                "way, and I've had a dull afternoon.",
            ),
            secret="Was Asha's lover; Ilvara maimed him to punish her. He obeys but simmers.",
            hook="If humiliated or offered glory, might look away at the wrong moment during escape."),
        sheet=_drow_elite(str_=15, dex=18, hp=71, gender="male",
                          attacks=[{"name": "rapier", "bonus": 7, "damage": "2d6+4", "reach": "melee"},
                                   {"name": "hand crossbow", "bonus": 7, "damage": "1d6+4", "reach": "ranged"}])),

    "asha_vandree": NPCDef(
        card=_oota_card(
            "asha_vandree", "Asha Vandree", "drow priestess acolyte", "drow",
            description="A young priestess with haunted eyes, spider tattoos fresh on her cheeks.",
            demeanor="Pious on the surface, terrified underneath; craves approval.",
            voice="High and careful; repeats Lolth's titles when nervous.",
            mannerisms="Clutches holy symbol until knuckles pale; flinches at Jorlan's voice.",
            dialogue_examples=(
                "The Spider Queen sees all. She sees you trembling. She sees... me trembling too. "
                "She sees everything, and She is never merciful.",
                "I am not permitted to help you -- Her law is clear. I am also not permitted to stop "
                "you, if you were clever enough. Do you understand what I am not saying?",
                "Jorlan was... we were... it doesn't matter now. Nothing matters but Her web, and "
                "the price of a single torn strand.",
                "Please don't make me choose between you and my skin. I have run out of choices I "
                "can survive, and you are standing in the last one.",
                "If you escape, tell the surface I tried to be kind. No one will believe you -- but "
                "say it anyway. I need one true thing to have existed here.",
            ),
            secret="Helped a slave once and was whipped; wants out but fears Lolth more than chains.",
            hook="Might leave a gate unlatched if the party appeals to her buried conscience."),
        sheet=_sheet(str_=10, dex=14, con=12, int_=11, wis=15, cha=14, hp=27, ac=13,
                     pb=2, level=2, klass="cleric", race="drow", profs=["religion", "medicine"],
                     attacks=[{"name": "mace", "bonus": 4, "damage": "1d6+2", "reach": "melee"}],
                     alignment="Neutral Evil", alignment_key="ne", gender="female", intelligence=11,
                     tags=["drow", "divine"])),

    "drow_slave_handler": NPCDef(
        card=_oota_card(
            "drow_slave_handler", "Drow Slave Handler", "overseer", "drow",
            description="A whip-scarred drow in leather harness, keys at hip, boredom in his eyes.",
            demeanor="Cruel, efficient, superstitious about escape omens.",
            voice="Barking orders; laughs when prisoners stumble.",
            mannerisms="Counts heads twice; snaps fingers for quaggoth backup.",
            dialogue_examples=(
                "Line up, rats. Chains tight, backs straight. Smile if you want -- it annoys the "
                "priestess when you still look hopeful, and that amuses me.",
                "The chasm takes the slow. I take the slow first, personally, then the chasm gets "
                "whatever's left. Don't be slow.",
                "Another surface rat thinks the dark is softer than my whip. Educate them, boys -- "
                "loudly. I want the echo to learn too.",
                "Quaggoth! The big one in the corner -- yes, that prince with the bone crown -- is "
                "giving me ideas, and none of them are gentle.",
                "Food in five minutes. Misery now. Priorities, surface scum. Learn them or I'll "
                "teach you with less talking.",
            ),
            secret="Skims slave rations to sell on the side.",
            hook="Can be bribed with surface coin or intimidated into looking the wrong way."),
        sheet=_sheet(str_=12, dex=14, con=13, int_=10, wis=11, cha=10, hp=32, ac=15, pb=2,
                     level=3, klass="fighter", race="drow", profs=["intimidation", "athletics"],
                     attacks=[{"name": "whip", "bonus": 4, "damage": "1d4+2", "reach": "melee"},
                              {"name": "shortsword", "bonus": 4, "damage": "1d6+2", "reach": "melee"}],
                     alignment="Lawful Evil", alignment_key="le", gender="male", intelligence=10,
                     tags=["drow"])),

    "buppido": NPCDef(
        card=_oota_card(
            "buppido", "Buppido", "derro cultist (prisoner)", "derro",
            description="A white-haired derro with a fixed, beatific smile and eyes that never blink together.",
            demeanor="Cheerful, helpful, utterly insane; hears Diirinka constantly.",
            voice="Whispering reverence; calls everyone 'initiate' or 'sacrifice' interchangeably.",
            mannerisms="Hums tuneless prayers; draws spiral maps on any available surface.",
            dialogue_examples=(
                "Diirinka says the path is downward. Downward is holy. Downward is home. Downward "
                "is where the screaming stops being a problem and becomes a hymn.",
                "I'll guard the food tonight. Trust me -- everyone always trusts Buppido. That's "
                "the miracle, and also why the count keeps coming up short.",
                "The pretty lady with the whip is a saint. No -- wait -- a mistake. One of those. "
                "Diirinka laughs when I confuse them. I like when He laughs.",
                "We should split up in the tunnels. Diirinka loves when we split up. So much "
                "learning in the dark, alone, with sharp things!",
                "I won't hurt anyone who doesn't need hurting. Diirinka will tell me who needs it. "
                "He always does, eventually, in the pretty whispery voice.",
            ),
            secret="Murdered two fellow prisoners already; believes it was divine will.",
            hook="Useful guide through madness -- until he decides the party is an offering."),
        sheet=_sheet(str_=11, dex=14, con=12, int_=10, wis=5, cha=8, hp=22, ac=13, pb=2,
                     level=3, klass="cleric", race="derro", creature_type="humanoid",
                     profs=["stealth", "deception"], attacks=[{"name": "hooked knife", "bonus": 4,
                     "damage": "1d4+2", "reach": "melee"}],
                     alignment="Chaotic Evil", alignment_key="ce", gender="male", intelligence=6,
                     tags=["monstrous"])),

    "jimjar": NPCDef(
        card=_oota_card(
            "jimjar", "Jimjar", "svirfneblin gambler", "deep gnome",
            description="A wiry deep gnome in a too-fine vest, dice always clicking in his pocket.",
            demeanor="Charming, nosy, cowardly until cornered; loves secrets as currency.",
            voice="Quick patter; turns every sentence into a wager.",
            mannerisms="Flips a coin that isn't there; counts your belongings while complimenting them.",
            dialogue_examples=(
                "Two silver says you can't name the last person Ilvara smiled at without flinching. "
                "No takers? Wise -- I'd have taken your coin and your dignity.",
                "Information's free, friend -- the first sentence, like a taste of wine. After that "
                "we negotiate like civilized fugitives, which is to say quickly and with lies.",
                "I'm not following you through the fungus fields. I'm coincidentally going the same "
                "direction at the same speed while counting your purse. Different thing entirely.",
                "Never bet against a drow with a holy symbol and a headache. Learned that expensive "
                "in Menzoberranzan, paid in teeth, and I don't forget tuition.",
                "You need a guide who knows which mushrooms bite. I need not to die before breakfast. "
                "Symmetry. Beautiful. Let's ruin it with haggling.",
            ),
            secret="Owes money to half the Underdark; his luck is partly stolen magic.",
            hook="Will scout, cheat, and bargain for the party if kept alive and paid."),
        sheet=_sheet(str_=8, dex=15, con=12, int_=13, wis=10, cha=14, hp=14, ac=13, pb=2,
                     level=1, klass="wizard", race="deep gnome", profs=["sleight_of_hand", "deception"],
                     attacks=[{"name": "dagger", "bonus": 4, "damage": "1d4+2", "reach": "melee"}],
                     alignment="Chaotic Neutral", alignment_key="cn", gender="male", intelligence=13,
                     tags=["gnome"])),

    "eldeth_feldrun": NPCDef(
        card=_oota_card(
            "eldeth_feldrun", "Eldeth Feldrun", "shield dwarf fighter", "dwarf",
            description="A stocky dwarf woman with a broken nose and a clan braid still fiercely oiled.",
            demeanor="Stubborn, honorable, furious at captivity; hates drow with craftsman precision.",
            voice="Gravel and iron; short sentences that land like hammer blows.",
            mannerisms="Tests every doorframe for height; rolls shoulders before a fight.",
            dialogue_examples=(
                "My clan's anvil is above us, hammering somewhere under real sky. I intend to hear "
                "it again before I die -- and I don't plan on dying in a drow's kennel.",
                "I'll take the one with the whip. You take the one with the smile. When this turns "
                "ugly, and it will, don't hesitate. Hesitation's how chains get heavier.",
                "Don't thank me yet. Thank me when we're drinking ale that tastes like sun and "
                "laughing too loud in a tavern that isn't trying to eat us.",
                "I don't leave people in cages. Not even the ones I don't like. Stone remembers "
                "cowards, and so do I.",
                "Stone endures. So do I. So will you, if you stop whimpering and start moving your "
                "feet like they belong to someone with pride.",
            ),
            secret="Carries a clan signet hidden in her boot; fears it marks her for ransom.",
            hook="A steadfast melee ally if respected; will charge at slavers without orders."),
        sheet=_sheet(str_=16, dex=12, con=15, int_=10, wis=11, cha=10, hp=13, ac=16, pb=2,
                     level=1, klass="fighter", race="dwarf", profs=["athletics", "intimidation"],
                     attacks=[{"name": "battleaxe", "bonus": 5, "damage": "1d8+3", "reach": "melee"}],
                     alignment="Lawful Good", alignment_key="lg", gender="female", intelligence=10,
                     tags=["dwarf"])),

    "prince_derendil": NPCDef(
        card=_oota_card(
            "prince_derendil", "Prince Derendil", "quaggoth 'prince'", "quaggoth",
            description="A massive quaggoth in tattered finery, crown of bone and fungus, eyes oddly gentle.",
            demeanor="Courteous madness; believes he is a surface prince under enchantment.",
            voice="Formal, archaic, heartbreakingly sincere.",
            mannerisms="Bows despite his chains; apologizes to furniture he bumps.",
            dialogue_examples=(
                "Good morrow, honored guests. Forgive my attendants -- the court has fallen on "
                "difficult customs of late, and the servants have grown so very hairy.",
                "I shall reclaim my kingdom once this curse lifts, and you shall have titles -- "
                "Duke of the Morning, Baron of the Brave Stair. All of you. I am generous.",
                "The lady priestess is a wicked enchantress who binds noble blood with chains. I "
                "shall not harm a woman, even her -- princes have codes, though my knuckles disagree.",
                "My chamber is smaller than I recall, and the tapestries are also mushrooms. "
                "Intriguing taste in décor. I shall compliment the steward. If I find him.",
                "If I roar, it is only because princes must be heard above the rabble. Do not be "
                "afraid -- I am your protector, and protectors are sometimes loud.",
            ),
            secret="Is a quaggoth thonot; if disabused of his delusion he may become a raging beast.",
            hook="Immensely strong ally while his delusion holds; moral dilemma if truth is revealed."),
        sheet=_sheet(str_=17, dex=12, con=16, int_=6, wis=10, cha=8, hp=45, ac=13, pb=2,
                     level=3, klass="barbarian", race="quaggoth", creature_type="monstrosity",
                     profs=["athletics"], attacks=[{"name": "claws", "bonus": 5, "damage": "2d6+3",
                     "reach": "melee"}],
                     alignment="Neutral Good", alignment_key="ng", gender="male", intelligence=6,
                     tags=["monstrous", "beast"])),

    "sarit_kzekarit": NPCDef(
        card=_oota_card(
            "sarit_kzekarit", "Sarith Kzekarit", "drow ranger (prisoner)", "drow",
            description="A lean drow with travel scars and a spider-brand burned away from his cheek.",
            demeanor="Quiet, watchful, guilt-ridden; knows the Underdark routes.",
            voice="Low and sparse; chooses words like arrows.",
            mannerisms="Always faces the exit; fingers a absent holy symbol.",
            dialogue_examples=(
                "I guided caravans for House Kzekarit through passages they'd rather forget. Now I "
                "guide guilt through narrower tunnels. Same map. Different cargo.",
                "Don't trust drow. That includes me -- especially me. I know what my people do when "
                "they're certain no one with a soul is watching.",
                "The fungus ahead is edible if you cook it. The water after it is not, no matter "
                "how thirsty you are. Remember that order or remember nothing at all.",
                "I failed someone I loved when obedience seemed safer than courage. I won't fail "
                "strangers the same way. It's all I have left that still feels like a person.",
                "If we reach Blingdenstone, I may stay. Some stains don't wash in sunlight, and "
                "some men shouldn't bring their shadow home to kin.",
            ),
            secret="Exiled for sparing a surface prisoner; Ilvara means to make an example of him.",
            hook="Best wilderness guide in the party; torn between revenge and redemption."),
        sheet=_sheet(str_=11, dex=16, con=12, int_=12, wis=15, cha=10, hp=22, ac=14, pb=2,
                     level=3, klass="ranger", race="drow", profs=["survival", "stealth", "perception"],
                     attacks=[{"name": "scimitar", "bonus": 5, "damage": "1d6+3", "reach": "melee"},
                              {"name": "longbow", "bonus": 5, "damage": "1d8+3", "reach": "ranged"}],
                     alignment="Neutral Good", alignment_key="ng", gender="male", intelligence=12,
                     tags=["drow", "hunter"])),

    "shuushar": NPCDef(
        card=_oota_card(
            "shuushar", "Shuushar the Awakened", "kuo-toa monk", "kuo-toa",
            description="A serene kuo-toa in monk's wraps, eyes milky, hands folded as if in endless prayer.",
            demeanor="Calm to the point of unsettling; speaks in koans.",
            voice="Slow, wet, peaceful; long pauses between words.",
            mannerisms="Never startles; breathes audibly before answering.",
            dialogue_examples=(
                "The lake is a mirror. The mirror is a mouth. We choose what we feed it -- fear, "
                "or stillness. Stillness is harder. Try anyway.",
                "Violence is a wave that thinks it owns the shore. I am a stone. The wave passes. "
                "The stone remains, wet and unmoved.",
                "Your fear is a fish darting in dark water. I will not eat it. You need not either. "
                "Let it swim past your ribs and leave.",
                "Bloppblippolp is a name men gave the water when they needed a god to blame. The "
                "water does not care what you call it. Paddle anyway.",
                "I will paddle. You will breathe -- in for four strokes, out for four. Together we "
                "cross, and the lake will not own us today.",
            ),
            secret="Achieved enlightenment after witnessing his people's madness; may be the sanest person alive.",
            hook="Paddles the Darklake; mediates between party and mad kuo-toa."),
        sheet=_sheet(str_=12, dex=14, con=13, int_=11, wis=16, cha=10, hp=18, ac=14, pb=2,
                     level=2, klass="monk", race="kuo-toa", creature_type="humanoid",
                     profs=["insight", "religion"], attacks=[{"name": "unarmed", "bonus": 4,
                     "damage": "1d6+2", "reach": "melee"}],
                     alignment="Lawful Neutral", alignment_key="ln", gender="male", intelligence=11,
                     tags=["monstrous"])),

    "stool": NPCDef(
        card=_oota_card(
            "stool", "Stool", "myconid juvenile", "myconid",
            description="A small mushroom-person with wide spore-puff eyes, trembling when afraid.",
            demeanor="Shy, loyal, telepathically 'tastes' of damp hope.",
            voice="Telepathic impressions: gratitude, fear, wonder -- few words.",
            mannerisms="Hides behind taller companions; releases calming spores when hugged.",
            dialogue_examples=(
                "(warm bread, soft moss) Friend... here? Safe? Stool... afraid. Stay close?",
                "(rain on stone, distant drip) Follow. Grove waits. Help grow. Spores... gentle.",
                "(honey, then iron, then fear) Bad ones coming. Boots. Whips. Quiet -- quiet -- "
                "like roots under snow.",
                "(sun through clouds, remembered light) You saved Stool. Remember. Good. Warm "
                "in chest. Like spore-hug.",
                "(soil and tears, mycelial hum) Not alone. Never alone. Colony feels you. Stool "
                "feels you. We grow together or not at all.",
            ),
            secret="Carries a royal spore that could unite a myconid colony -- or poison one.",
            hook="Guides to a fungal grove sanctuary; emotional heart of the prisoner group."),
        sheet=_sheet(str_=8, dex=10, con=12, int_=10, wis=13, cha=7, hp=7, ac=10, pb=2,
                     level=0, klass="commoner", race="myconid", creature_type="plant",
                     profs=[], attacks=[{"name": "fist", "bonus": 2, "damage": "1d4", "reach": "melee"}],
                     gender="non_applicable", intelligence=10, mindless=False,
                     tags=["plant", "beast"])),

    "topsy": NPCDef(
        card=_oota_card(
            "topsy", "Topsy", "wererat (prisoner)", "wererat",
            description="A halfling-sized wererat with quick eyes and quicker fingers, ears always twitching.",
            demeanor="Nervous, protective of Turvy, sharper than she pretends.",
            voice="High and fast; lies poorly but steals well.",
            mannerisms="Chews a fingernail; counts exits in every room.",
            dialogue_examples=(
                "We're not monsters. We're survivors who happen to be monsters at night -- there's "
                "a difference, if you're the one still talking in the morning.",
                "Turvy and I stick together. Split us and you'll learn how fast rats bite when "
                "their nest is kicked. Ask the last guard who tried.",
                "The drow don't look down. That's how we move through Velkynvelve. That's how you "
                "move too, if you're smart and small and good at not smelling like hope.",
                "I didn't steal your food. I relocated it for safekeeping in my belly. You're "
                "welcome. ...Fine, I'll share if you stop looking at me like that.",
                "Full moon's bad. New moon's worse. Don't ask why -- you won't like the answer, "
                "and I won't like giving it with my mouth doing what mouths do.",
            ),
            secret="Infected with lycanthropy recently; fears turning on Turvy.",
            hook="Scout and lockpicker; knows Velkynvelve's rat tunnels."),
        sheet=_sheet(str_=10, dex=16, con=12, int_=11, wis=10, cha=11, hp=9, ac=13, pb=2,
                     level=1, klass="rogue", race="wererat", profs=["stealth", "sleight_of_hand"],
                     attacks=[{"name": "dagger", "bonus": 5, "damage": "1d4+3", "reach": "melee"}],
                     alignment="Chaotic Neutral", alignment_key="cn", gender="female", intelligence=11,
                     tags=["beast", "criminal"])),

    "turvy": NPCDef(
        card=_oota_card(
            "turvy", "Turvy", "wererat (prisoner)", "wererat",
            description="Topsy's quieter twin, broader, with a scar across his muzzle-form nose.",
            demeanor="Loyal, blunt, ready to fight if Topsy is threatened.",
            voice="Gruff whispers; repeats Topsy's plans with more confidence.",
            mannerisms="Stands slightly in front of Topsy; cracks knuckles.",
            dialogue_examples=(
                "Topsy talks. I hit. Good arrangement -- keeps us alive, keeps idiots quiet.",
                "They put us in a cage and called it order. We put them in the ground and called "
                "it Tuesday. Fair trade.",
                "Don't touch her. I'll say it once, with my hand on a blade, and you can decide "
                "how deaf you want to be.",
                "Rats know where the guards don't look -- the crawlspaces, the drip lines, the "
                "shame-holes. Follow or don't. Your funeral either way.",
                "Moon comes soon. We leave then, or we lock the door from outside and let them "
                "wonder why the dark got so personal.",
            ),
            secret="Has already killed a guard during a partial transformation.",
            hook="Muscle and tunnel fighter; will die for Topsy."),
        sheet=_sheet(str_=12, dex=14, con=13, int_=9, wis=10, cha=8, hp=11, ac=13, pb=2,
                     level=1, klass="fighter", race="wererat", profs=["athletics", "stealth"],
                     attacks=[{"name": "shortsword", "bonus": 4, "damage": "1d6+2", "reach": "melee"}],
                     alignment="Chaotic Neutral", alignment_key="cn", gender="male", intelligence=9,
                     tags=["beast", "criminal"])),

    "ront": NPCDef(
        card=_oota_card(
            "ront", "Ront", "orc prisoner", "orc",
            description="A hulking orc with a split lip and a permanent scowl, fists like ham hocks, "
                        "eyes always measuring who to blame.",
            demeanor="Bully-brave, cowardly alone; loud to hide fear.",
            voice="Barking Common with orcish curses; boasts, then whimpers when Ilvara is mentioned.",
            mannerisms="Cracks knuckles before threats; flinches at drow women's voices.",
            dialogue_examples=(
                "Ront strongest here! ...Among prisoners. Among most prisoners. Shut up.",
                "You want Ront smash guard? Maybe. Maybe Ront smash you instead. Depends on food.",
                "Ilvara comes, you get behind Ront. No -- get in front. Ront meant get behind Ront.",
                "They took my tooth. Fine. Ront takes their knee next time. You'll see.",
                "Don't trust drow. Don't trust derro. Trust Ront little bit. Little bit is generous.",
            ),
            secret="Will sell out the party for extra rations if frightened badly enough.",
            hook="Muscle if bullied into line; liability if morale breaks."),
        sheet=_sheet(str_=16, dex=10, con=14, int_=7, wis=9, cha=8, hp=15, ac=13, pb=2,
                     level=1, klass="barbarian", race="half_orc", profs=["intimidation", "athletics"],
                     attacks=[{"name": "fist", "bonus": 5, "damage": "1d4+3", "reach": "melee"}],
                     alignment="Chaotic Neutral", alignment_key="cn", gender="male", intelligence=7,
                     tags=["orc"])),

    "pog": NPCDef(
        card=_oota_card(
            "pog", "Pog", "kobold prisoner", "kobold",
            description="A scrawny kobold wrapped in stolen rags, tail tucked, eyes too bright in the dark.",
            demeanor="Craven, eager to please, survives by being overlooked.",
            voice="High, fast, pleading; calls stronger prisoners 'boss'.",
            mannerisms="Hugs walls; offers 'shiny' pebbles as tribute.",
            dialogue_examples=(
                "Pog not trouble! Pog good scout! Pog fit in small places bosses cannot!",
                "Boss want Pog distract guard? Pog can cough very loud. Very convincing cough.",
                "Drow step on Pog twice. Pog remember. Pog remember quietly.",
                "Food scrap? Pog loyal forever. Forever is maybe three days. Still loyal!",
                "Pog found loose stone near bridge. Pog tell you for meat. Fair trade, yes?",
            ),
            secret="Stole a guard's key chip and swallowed it; terrified of surgery.",
            hook="Tunnel scout and distraction; loyal only while fed and unthreatened."),
        sheet=_sheet(str_=7, dex=14, con=10, int_=8, wis=10, cha=8, hp=5, ac=12, pb=2,
                     level=0, klass="commoner", race="halfling", creature_type="humanoid",
                     profs=["stealth"], attacks=[{"name": "knife", "bonus": 4, "damage": "1d4+2", "reach": "melee"}],
                     alignment="Neutral", alignment_key="tn", gender="male", intelligence=8,
                     tags=["beast", "criminal"])),

    "rumpadump": NPCDef(
        card=_oota_card(
            "rumpadump", "Rumpadump", "myconid adult", "myconid",
            description="A tall mushroom-person with a crown of spore-puff caps, movements slow and grave.",
            demeanor="Patient, communal, speaks in spore-images more than words.",
            voice="Telepathic impressions: stone, rain, patience, warning.",
            mannerisms="Releases calming spores when the party argues; tilts toward light sources.",
            dialogue_examples=(
                "(damp stone, slow heartbeat) Colony... remembers. Surface... far. We go together.",
                "(warm broth, shared bowl) Hunger shared is hunger halved. Rumpadump offers spores. Calm.",
                "(iron, whip-crack) Bad ones near bridge. Wait. Breathe. Move when echo fades.",
                "(sun-memory, grief) Stool is young. Young need protection. You protect, Rumpadump guides.",
                "(mycelial hum, resolve) Faerzress hurts. Pain not permanent. Roots endure longer than chains.",
            ),
            secret="Knows a path to a sovereign myconid circle that could shelter dozens.",
            hook="Steady guide through fungal wilds; moral center of the myconid pair with Stool."),
        sheet=_sheet(str_=10, dex=10, con=14, int_=11, wis=14, cha=9, hp=16, ac=11, pb=2,
                     level=2, klass="druid", race="myconid", creature_type="plant",
                     profs=["nature", "insight"], attacks=[{"name": "fist", "bonus": 2, "damage": "1d6", "reach": "melee"}],
                     gender="non_applicable", intelligence=11, tags=["plant", "beast"])),

    "zilith": NPCDef(
        card=_oota_card(
            "zilith", "Zilith", "drow prisoner (disgraced noble)", "drow",
            description="A proud drow woman with house insignia gouged from her armor, jaw set in defiance.",
            demeanor="Arrogant, wounded pride, dangerous if offered revenge.",
            voice="Cutting Undercommon; treats surface folk as furniture until they surprise her.",
            mannerisms="Won't kneel even when beaten; spits when Ilvara's name is praised.",
            dialogue_examples=(
                "House Xorlarrin will hear of this. You will carry my message, or you will carry nothing.",
                "I am not your ally. I am a temporary coincidence of chains. Do not forget the difference.",
                "Ilvara enjoys sermons. Give her silence instead. Silence wounds priestesses best.",
                "You expect gratitude? How provincial. Expect usefulness. I am very useful when motivated.",
                "Free me at Blingdenstone and I vanish. Pursue me and you learn why drow do not beg twice.",
            ),
            secret="Would reunite with a rival house to destroy Ilvara, then turn on the party.",
            hook="Political leverage and Underdark intel if freed; betrayal risk if trusted."),
        sheet=_sheet(str_=11, dex=15, con=12, int_=13, wis=12, cha=14, hp=20, ac=14,
                     pb=2, level=3, klass="rogue", race="drow", profs=["deception", "stealth", "perception"],
                     attacks=[{"name": "shortsword", "bonus": 5, "damage": "1d6+3", "reach": "melee"}],
                     alignment="Neutral Evil", alignment_key="ne", gender="female", intelligence=13,
                     tags=["drow", "noble"])),

    "blurg": NPCDef(
        card=_oota_card(
            "blurg", "Blurg", "orog bodyguard", "orog",
            description="A seven-foot orog with filed teeth and a surprisingly delicate way of handling coin.",
            demeanor="Professional, literal-minded, fond of strong drink.",
            voice="Deep and simple; misunderstands metaphors charmingly.",
            mannerisms="Sits carefully on weak furniture; polishes his tusks.",
            dialogue_examples=(
                "Blurg guard boat. You pay silver. Blurg not kill passengers. Good deal. Blurg "
                "likes good deals almost as much as lunch.",
                "Little wizard talk too much, wave hands, scare fish. Blurg like him anyway. Funny "
                "little man. Good tipper when scared.",
                "Duergar king angry about something. Politics. Blurg not care. Blurg care about "
                "lunch, and lunch is not politics.",
                "You run fast on shore. Blurg run faster. But Blurg not run today. Today is "
                "contract day. Contract say stand here and look big.",
                "Fish-people crazy, shout at water, electrocute friends. Blurg say so. Blurg still "
                "paddle. Water is water. Coin is coin.",
            ),
            secret="Saving coin to buy freedom from a duergar debt contract.",
            hook="Hireling muscle on the Darklake; switches sides for food and gold."),
        sheet=_sheet(str_=18, dex=12, con=16, int_=9, wis=10, cha=7, hp=30, ac=14, pb=2,
                     level=3, klass="fighter", race="orog", profs=["athletics", "intimidation"],
                     attacks=[{"name": "greatclub", "bonus": 6, "damage": "2d8+4", "reach": "melee"}],
                     alignment="Neutral", alignment_key="tn", gender="male", intelligence=9,
                     tags=["monstrous"])),

    "y_shopkeeper": NPCDef(
        card=_oota_card(
            "y_shopkeeper", "Y", "deep gnome trader", "deep gnome",
            description="A svirfneblin in smoked goggles, cart piled with salvage and suspiciously clean bandages.",
            demeanor="Wary, fair within limits, hates mind flayers with quiet fire.",
            voice="Clipped Undercommon; trades in facts and flint.",
            mannerisms="Never shows both hands empty; taps stone twice before speaking.",
            dialogue_examples=(
                "Coin first, always. Questions cost extra. Answers cost more, and the good ones "
                "cost more than you've got unless you're lying about your purse.",
                "I sell rope, picks, bandages, and silence. Which do you need most? Don't say "
                "silence unless you can afford all three.",
                "Illithids took my brother's mind in a passage I'll never go back to. I take their "
                "silver when I can, and I sleep lighter when I do.",
                "Velkynvelve goods are cheap because blood is cheap down here. You still buying, "
                "or are you only here to feel righteous about it?",
                "Trust is a luxury for people with spare lives. I sell necessities -- flint, wire, "
                "the truth about which tunnels echo wrong.",
            ),
            secret="Runs messages for Blingdenstone's elders.",
            hook="Sells survival gear at Gracklstugh's edge; knows safe routes."),
        sheet=_sheet(str_=10, dex=14, con=12, int_=13, wis=14, cha=10, hp=16, ac=14, pb=2,
                     level=2, klass="merchant", race="deep gnome", profs=["insight", "investigation"],
                     attacks=[{"name": "light crossbow", "bonus": 4, "damage": "1d8+2", "reach": "ranged"}],
                     alignment="Neutral Good", alignment_key="ng", gender="non_applicable", intelligence=13,
                     tags=["gnome"])),

    "drow_patrol_guard": NPCDef(
        card=_oota_card(
            "drow_patrol_guard", "Drow Patrol Guard", "drow soldier", "drow",
            description="A standard drow house guard in piwafwi cloak, hand crossbow ready.",
            demeanor="Alert, disciplined, casually cruel.",
            voice="Undercommon clipped commands.",
            mannerisms="Hand signals to partners; poison vials at belt.",
            dialogue_examples=(
                "Halt. Weapons down, hands open. Die quietly and the Spider Queen may not notice "
                "your soul.",
                "The priestess wants live ones for the pens. Try running -- I need the exercise, "
                "and the chasm needs the entertainment.",
                "Surface filth in our tunnels again. How tedious. Kneel or bleed; either way you "
                "leave your dignity here.",
                "Crossbows ready. Poisoned. Don't make me waste good bolts on something this "
                "disappointing.",
            ),
            secret="", hook="Standard patrol encounter."),
        sheet=_sheet(str_=11, dex=14, con=12, int_=11, wis=12, cha=10, hp=16, ac=15, pb=2,
                     level=2, klass="fighter", race="drow", profs=["perception", "stealth"],
                     attacks=[{"name": "shortsword", "bonus": 4, "damage": "1d6+2", "reach": "melee"},
                              {"name": "hand crossbow", "bonus": 4, "damage": "1d6+2", "reach": "ranged"}],
                     alignment="Neutral Evil", alignment_key="ne", gender="female", intelligence=11,
                     tags=["drow"])),

    "duergar_guard": NPCDef(
        card=_oota_card(
            "duergar_guard", "Duergar Guard", "duergar soldier", "duergar",
            description="A grey dwarf in spiked plate, beard braided with iron rings.",
            demeanor="Sullen, xenophobic, proud of craft and king.",
            voice="Growled Undercommon; repeats 'Deepking' like a threat.",
            mannerisms="Spits near surface-dwellers' boots; arms never uncrossed.",
            dialogue_examples=(
                "Papers or heads. Your choice, surface scum -- the Deepking's clerks love a neat "
                "ledger either way.",
                "The forge takes all kinds. Mostly slaves, some merchants, and fools who thought "
                "grey stone meant grey morals.",
                "Deepking's law. Not mine -- I just wear his iron and eat his bread -- but I'll "
                "enforce it on your skull if you linger.",
                "Move along before I find a reason. I enjoy reasons. The captain enjoys paperwork "
                "less than I enjoy picking.",
            ),
            secret="", hook="Gate guard in Gracklstugh."),
        sheet=_sheet(str_=14, dex=11, con=14, int_=11, wis=10, cha=9, hp=26, ac=16, pb=2,
                     level=2, klass="fighter", race="duergar", profs=["athletics"],
                     attacks=[{"name": "war pick", "bonus": 4, "damage": "1d8+2", "reach": "melee"},
                              {"name": "javelin", "bonus": 3, "damage": "1d6+2", "reach": "ranged"}],
                     alignment="Lawful Evil", alignment_key="le", gender="male", intelligence=10,
                     tags=["dwarf"])),

    "hook_horror_hunter": NPCDef(
        card=_oota_card(
            "hook_horror_hunter", "Hook Horror", "predator", "hook horror",
            description="A bipedal chitin nightmare with hooked claws, clicking as it hunts.",
            demeanor="Hungry, patient, territorial.",
            voice="Clicking and scraping.",
            mannerisms="Taps hooks on stone to echolocate.",
            dialogue_examples=(
                "*(click-click-click -- echolocating, measuring your heartbeat's distance)*",
                "*(scraping hooks on stone, a sound like butcher's cleavers testing bone)*",
                "*(a patient hunter's pause, then a single dry click that means closer)*",
            ),
            secret="", hook="Wilderness encounter."),
        sheet=_sheet(str_=17, dex=11, con=16, int_=6, wis=10, cha=7, hp=75, ac=15, pb=2,
                     level=3, klass="monstrosity", race="hook horror", creature_type="monstrosity",
                     profs=[], attacks=[{"name": "hooks", "bonus": 5, "damage": "2d6+3", "reach": "melee"}],
                     gender="non_applicable", intelligence=3, comprehends_language=False,
                     tags=["monstrous", "beast"])),

    "kuo_toa_whip": NPCDef(
        card=_oota_card(
            "kuo_toa_whip", "Kuo-toa Whip", "kuo-toa priest", "kuo-toa",
            description="A fish-bellied kuo-toa in shell armor, eyes bulging with divine fervor.",
            demeanor="Fanatic, unpredictable, eager to electrocute nonbelievers.",
            voice="Gurgling sermons; invents god-names mid-sentence.",
            mannerisms="Spasms when 'inspired'; points at random party members as chosen.",
            dialogue_examples=(
                "Bloppblippolp sees you! Maybe! Worship while unsure -- doubt makes the devotion "
                "sweeter, yes, yes!",
                "New god! Old god! Fish god! All gods hungry! Feed them with praise or feed them "
                "with screams -- Bloppblippolp is flexible!",
                "Sacrifice is love. Love is wet. Wet is holy. Step into the shallows and let the "
                "lake decide if you are offering or chosen!",
            ),
            secret="", hook="Sloobludop encounter."),
        sheet=_sheet(str_=14, dex=10, con=14, int_=12, wis=14, cha=11, hp=33, ac=11, pb=2,
                     level=2, klass="cleric", race="kuo-toa", creature_type="humanoid",
                     profs=["religion"], attacks=[{"name": "mace", "bonus": 4, "damage": "1d6+2", "reach": "melee"},
                              {"name": "sacred flame", "bonus": 4, "damage": "1d8", "reach": "ranged"}],
                     alignment="Chaotic Evil", alignment_key="ce", gender="male", intelligence=10,
                     tags=["monstrous"])),

    "underdark_bandit": NPCDef(
        card=_oota_card(
            "underdark_bandit", "Underdark Bandit", "raider", "human",
            description="A scarred surface exile in patchwork armor, fungus-stained cloak.",
            demeanor="Desperate, greedy, cruel when confident.",
            voice="Surface Common gone rough; laughs too loud.",
            mannerisms="Sniffs food before speaking; fingers a notched blade.",
            dialogue_examples=(
                "Coin or guts. Your choice -- I'm flexible, and the fungus doesn't care which "
                "leaves a stain.",
                "Used to rob caravans up top where the sun still pretends to matter. Down here, "
                "you're the caravan, and I've got debts older than your hope.",
                "Don't look at me like I'm worse than the drow. I'm just hungrier, and hunger "
                "doesn't polish its boots before it cuts you.",
                "Hand over the pack slow. Smile while you do it. Makes it easier for both of us "
                "when I decide whether you walk away.",
            ),
            secret="Former Zhentarim; fled after botching a job.",
            hook="Ambush on a tunnel road; might flee if bloodied."),
        sheet=_sheet(str_=13, dex=12, con=12, int_=10, wis=10, cha=10, hp=11, ac=12, pb=2,
                     level=1, klass="bandit", race="human", profs=["intimidation", "stealth"],
                     attacks=[{"name": "scimitar", "bonus": 3, "damage": "1d6+1", "reach": "melee"},
                              {"name": "light crossbow", "bonus": 3, "damage": "1d8+1", "reach": "ranged"}],
                     alignment="Chaotic Evil", alignment_key="ce", gender="male", intelligence=10,
                     tags=["criminal", "outlaw"])),
}

CARDS: dict[str, NPCCard] = {k: v.card for k, v in NPCS.items()}


def npc_keys() -> list:
    return list(NPCS)


def npc_card(key: str) -> NPCCard | None:
    d = NPCS.get(key)
    return d.card if d is not None else None


def npc_sheet(key: str) -> dict | None:
    d = NPCS.get(key)
    return copy.deepcopy(d.sheet) if d is not None else None


def build_npc(key: str) -> Combatant | None:
    d = NPCS.get(key)
    if d is None:
        return None
    sheet = copy.deepcopy(d.sheet)
    sheet["card"] = d.card
    return Combatant(name=d.card.name, is_pc=False, sheet=sheet)
