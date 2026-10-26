from __future__ import annotations

from rulesets.dnd.settings.base import NPCCard, Tradesman

TRADESMEN = {
    "old_wenna": Tradesman(
        "old_wenna", "Old Wenna", "Greenest (a Sword Coast village)", "sword_coast",
        tier="village", categories=("gear", "potion", "tool"), max_rarity="common",
        stock_size=5, markup=1.0, sell_rate=0.4, restock_interval=4,
        card=NPCCard("old_wenna", "Old Wenna", "village herb-wife", "human",
                     description="A stooped, bright-eyed old woman in a patched shawl, hands stained green.",
                     demeanor="Kindly, gossipy, a little deaf when it suits her.",
                     voice="Slow and folksy; calls you 'dearie' and asks after your mother.",
                     secret="Her 'simple tonics' include one genuinely potent remedy she won't sell to just anyone.",
                     hook="Frets about something in the old well at the edge of the fields.")),
    "garrick_cobble": Tradesman(
        "garrick_cobble", "Garrick Cobble", "the Trade Way (a roadside tinker)", "sword_coast",
        tier="village", categories=("gear", "tool", "ammunition"), max_rarity="common",
        stock_size=5, markup=1.1, sell_rate=0.4, restock_interval=3,
        card=NPCCard("garrick_cobble", "Garrick Cobble", "travelling tinker", "halfling",
                     description="A cheerful halfling with a cart that clatters like a kitchen falling downstairs.",
                     demeanor="Talkative, generous with rumor, sharp on a price.",
                     voice="Quick and chipper; everything is 'a bargain, friend, a steal!'",
                     secret="Fences the odd 'found' item and knows which roads the bandits favor.",
                     hook="Will trade road-news for an escort to the next town.")),

    "brannor_stonehand": Tradesman(
        "brannor_stonehand", "Brannor Stonehand", "Daggerford (a town smithy)", "sword_coast",
        tier="town", categories=("weapon", "armor", "shield"), max_rarity="uncommon",
        stock_size=6, markup=1.0, sell_rate=0.5, restock_interval=4,
        card=NPCCard("brannor_stonehand", "Brannor Stonehand", "town blacksmith", "dwarf",
                     description="A barrel-chested dwarf with a singed beard and forearms like ham hocks.",
                     demeanor="Gruff, honest, proud of his work.",
                     voice="Blunt and clipped; lets the steel do the talking.",
                     mannerisms="Tests every edge with a thumb; never stops working while he talks.",
                     dialogue_examples=(
                         "Daggerford pays its debts, and so will you -- I didn't hammer this steel for "
                         "philosophy, I hammered it for coin and the folk who swing it honest.",
                         "That'll hold an edge through three battles, maybe four if you're not a fool with "
                         "it. Mind you live long enough to need a fourth.",
                         "Hmf. Coin's coin. Don't haggle me like I'm some Waterdeep fop in silk -- I know "
                         "what ore costs and what blood's worth, and neither's negotiable.",
                         "You want pretty? Buy a mirror. You want true? Feel the balance in the tang. "
                         "That's the whole sermon.",
                         "Kobolds took the east vein again. Bring me ore from that hole and I'll shave "
                         "your price till you blush. Fair's fair.",
                     ),
                     secret="Keeps one masterwork blade he'll only sell to someone who'll use it rightly.",
                     hook="Needs ore from a mine the kobolds have reclaimed.")),
    "sister_yelena": Tradesman(
        "sister_yelena", "Sister Yelena", "Triboar (a temple stall)", "sword_coast",
        tier="town", categories=("potion", "scroll", "gear"), max_rarity="uncommon",
        stock_size=5, markup=1.1, sell_rate=0.5, restock_interval=5,
        card=NPCCard("sister_yelena", "Sister Yelena", "temple provisioner", "human",
                     description="A composed acolyte in travel-worn vestments, ledger always to hand.",
                     demeanor="Serene, frugal, quietly shrewd.",
                     voice="Measured and gentle; frames every sale as a blessing.",
                     mannerisms="Touches a small holy symbol before naming a price; folds her hands when she's done.",
                     dialogue_examples=(
                         "Tymora smiles on the prepared, dear traveler. A healing draught, perhaps, "
                         "before the road teaches you humility the harder way?",
                         "The temple asks only a fair price -- and that you spend what you buy on life, "
                         "not on cruelty. The Lady notices the difference.",
                         "Go gently, and go soon. The road north has not been kind of late, and I've "
                         "buried two parishioners who thought luck would substitute for sense.",
                         "This balm is consecrated, not merely mixed. That means it costs more and works "
                         "more -- Tymora has standards.",
                         "If you've coin to spare, the shelter fund could use it. If not, take the "
                         "blessing anyway. We don't turn away the hungry here.",
                     ),
                     secret="Diverts a tithe of profits to shelter refugees the town would turn away.",
                     hook="Seeks a scroll stolen from the temple vault.")),

    "jessa_quickfingers": Tradesman(
        "jessa_quickfingers", "Jessa Quickfingers", "Waterdeep, Trades Ward", "waterdeep",
        tier="city", categories=(), max_rarity="rare", stock_size=8, rarity_bias=1.15,
        markup=1.15, sell_rate=0.5, restock_interval=3,
        card=NPCCard("jessa_quickfingers", "Jessa Quickfingers", "general goods dealer", "tiefling",
                     description="A striking tiefling in fine merchant's silks, horns capped with silver, smile easy.",
                     demeanor="Charismatic, theatrical, never quite gives you a straight 'no'.",
                     voice="Warm, quick, peppered with flattery and well-timed confidences.",
                     secret="Runs information as briskly as goods, and owes a favor to a Masked Lord.",
                     hook="Will discount handsomely for a delicate errand she can't be seen running.")),
    "old_embric": Tradesman(
        "old_embric", "Old Embric", "Baldur's Gate, the Wide", "baldurs_gate",
        tier="city", categories=("weapon", "armor", "shield"), max_rarity="rare", stock_size=7,
        rarity_bias=1.1, markup=1.1, sell_rate=0.5, restock_interval=4,
        card=NPCCard("old_embric", "Old Embric", "master weaponsmith", "human",
                     description="A scarred veteran-turned-smith, one eye milky, grip still iron.",
                     demeanor="Taciturn, exacting, warms to a fellow soldier.",
                     voice="Low and spare; sizes up your wrists before your coin.",
                     secret="Forged blades for a mercenary company he now wishes he hadn't.",
                     hook="Wants a cursed sword he made tracked down and brought back.")),
    "madame_vashti": Tradesman(
        "madame_vashti", "Madame Vashti", "Neverwinter, the Chasm market", "neverwinter",
        tier="city", categories=("wondrous", "ring", "potion", "wand"), max_rarity="rare",
        stock_size=7, rarity_bias=1.2, markup=1.2, sell_rate=0.45, restock_interval=4,
        card=NPCCard("madame_vashti", "Madame Vashti", "curio dealer", "half-elf",
                     description="An elegant half-elf draped in scarves and rings, eyes that price everything.",
                     demeanor="Mysterious, flirtatious, faintly ominous.",
                     voice="Silky and knowing; speaks of items as if they have feelings.",
                     secret="Some of her curios are stolen grave-goods, and one of them wants to go home.",
                     hook="Pays well for oddments recovered from the city's old ruined quarter.")),
    "halgrim_pawn": Tradesman(
        "halgrim_pawn", "Halgrim", "Waterdeep, Dock Ward", "waterdeep",
        tier="city", categories=("gear", "weapon", "wondrous", "tool"), max_rarity="uncommon",
        stock_size=6, markup=0.95, sell_rate=0.6, restock_interval=2,
        card=NPCCard("halgrim_pawn", "Halgrim", "dock-ward pawnbroker", "human",
                     description="A heavyset man behind a barred counter, abacus worn smooth.",
                     demeanor="Brisk, incurious by policy, pays the best rates on the docks.",
                     voice="Flat and fast; 'buyin' or sellin', I ain't got all day.'",
                     secret="Knows exactly what came off which ship, and sells that knowledge too.",
                     hook="Will pay a finder's fee for a strongbox that 'fell off' a galley.")),

    "quillan_myr": Tradesman(
        "quillan_myr", "Quillan Myr", "a warded tower on the moors", "waterdeep",
        tier="elite", categories=("staff", "wand", "wondrous", "scroll", "ring"),
        max_rarity="legendary", min_rarity="rare", stock_size=5, rarity_bias=2.0,
        markup=1.4, sell_rate=0.55, restock_interval=8,
        card=NPCCard("quillan_myr", "Quillan Myr", "reclusive archmage", "human",
                     description="A gaunt, ageless wizard with ink-dark eyes and a voice like turning pages.",
                     demeanor="Distant, precise, impatient with the mundane.",
                     voice="Dry and exacting; tests your intelligence before your purse.",
                     secret="Buys rare items partly to keep certain of them out of worse hands.",
                     hook="Will trade a marvel for a page torn from a book in Candlekeep.")),
    "lady_of_the_grove": Tradesman(
        "lady_of_the_grove", "The Lady of the Grove", "a glade deep in the High Forest", "high_forest",
        tier="elite", categories=("wondrous", "staff", "potion", "ring"), max_rarity="very_rare",
        min_rarity="rare", stock_size=4, rarity_bias=1.8, markup=1.0, sell_rate=0.5,
        restock_interval=10,
        card=NPCCard("lady_of_the_grove", "The Lady of the Grove", "fey trader", "fey",
                     description="A tall, green-eyed lady who is almost, but not quite, an elf; the light bends toward her.",
                     demeanor="Gracious, riddling, and bound by old courtesies.",
                     voice="Musical and oblique; never quite says what she means, never lies.",
                     secret="Her prices are paid in memories and favors as often as coin.",
                     hook="Will deal only with those who first do right by the wood.")),
    "shyntra_drow": Tradesman(
        "shyntra_drow", "Shyntra Auvryndar", "a hidden bazaar in the Underdark", "underdark",
        tier="elite", categories=("weapon", "wondrous", "ring", "potion"), max_rarity="very_rare",
        min_rarity="rare", stock_size=5, rarity_bias=1.7, markup=1.5, sell_rate=0.4,
        restock_interval=9,
        card=NPCCard("shyntra_drow", "Shyntra Auvryndar", "drow trade-mistress", "drow",
                     description="A coolly beautiful dark elf in spider-silk, surrounded by silent guards.",
                     demeanor="Imperious, gracious in the way of a blade laid on velvet.",
                     voice="Soft, exact, every courtesy a faint threat.",
                     secret="Plays three Houses against one another and sells to all of them.",
                     hook="Offers fine, dangerous wares -- at a price that is rarely only gold.")),
    "xanthros": Tradesman(
        "xanthros", "Xanthros the Collector", "a brimstone-stinking vault below the city", "baldurs_gate",
        tier="elite", categories=("weapon", "wondrous", "ring", "rod", "staff"),
        max_rarity="legendary", min_rarity="rare", stock_size=5, rarity_bias=2.4,
        markup=1.8, sell_rate=0.35, restock_interval=12,
        card=NPCCard("xanthros", "Xanthros the Collector", "cambion merchant", "fiend",
                     description="A horned, beautiful, terrible figure of ash and gold, wings folded like a cloak.",
                     demeanor="Exquisitely courteous, infinitely patient, utterly without mercy.",
                     voice="Velvet and embers; every offer a contract, every contract a snare.",
                     secret="Deals in souls and bargains as readily as relics; the gold price is never the real one.",
                     hook="Will sell you something extraordinary -- and you will spend a long time learning the cost.")),
    "embered_mara": Tradesman(
        "embered_mara", "Mara of the Ash Road", "a caravan in the wild between cities", "sword_coast",
        tier="town", categories=("potion", "scroll", "wondrous", "gear"), max_rarity="rare",
        min_rarity="uncommon", stock_size=6, rarity_bias=1.3, markup=1.25, sell_rate=0.5,
        restock_interval=5,
        card=NPCCard("embered_mara", "Mara of the Ash Road", "wandering caravan trader", "human",
                     description="A weathered, watchful woman whose wagons have crossed every road twice.",
                     demeanor="Shrewd, fair, slow to trust and slower to forget a cheat.",
                     voice="Dry and frank; trades news of the road along with her wares.",
                     secret="Carries a sealed package she's been paid never to open or deliver early.",
                     hook="Will take on guards who don't ask what's in the third wagon.")),
}

from rulesets.dnd.settings.forgotten_realms.underdark_tradesmen import (
    TRADESMEN as _UNDERDARK_TRADESMEN)
TRADESMEN = {**TRADESMEN, **_UNDERDARK_TRADESMEN}

import copy as _copy
import dataclasses as _dc

from engine.state import Combatant as _Combatant


def _ts(*, str_=10, dex=10, con=10, int_=10, wis=10, cha=12, hp=12, ac=11, pb=2, level=2,
        klass="merchant", race="human", profs=(), attacks=None, creature_type="humanoid",
        alignment="", alignment_key="", gender="non_applicable") -> dict:
    return {
        "abilities": {"str": str_, "dex": dex, "con": con, "int": int_, "wis": wis, "cha": cha},
        "proficiencies": list(profs) or ["persuasion", "insight"], "proficiency_bonus": pb,
        "hp": hp, "max_hp": hp, "ac": ac, "level": level, "class": klass, "race": race,
        "attacks": list(attacks or [{"name": "dagger", "bonus": 3, "damage": "1d4+1", "reach": "melee"}]),
        "intelligence": 10, "creature_type": creature_type, "comprehends_language": True,
        "mindless": False, "alignment": alignment, "alignment_key": alignment_key, "gender": gender,
    }


_EXTRAS = {
    "old_wenna": dict(
        sheet=_ts(str_=8, dex=9, con=11, int_=11, wis=15, cha=12, hp=9, ac=10, level=2, klass="herbalist",
                  profs=["medicine", "nature"]),
        mannerisms="Sorts dried herbs into twists of paper as she talks; cups a hand to one ear.",
        dialogue=("Bless you, dearie, come in out of the wind -- your cheeks are half the color they ought "
                  "to be. Now what ails you, and don't lie, I've seen worse and kept my mouth shut.",
                  "This twist's for fever, that one's for a broken heart -- and no, I'll not say which "
                  "costs more, because grief and heat both think they're entitled to your last copper.",
                  "There's a thing down the old well been turning the water bad. Fish won't bite, "
                  "dogs won't drink. You look the sort to ask why instead of crossing yourself and "
                  "hoping.",
                  "I sell simples, not miracles. But simples done right have surprised better men "
                  "than you.",
                  "Your mother -- is she well? No? Then take this bundle on trust and pay me when "
                  "fortune remembers your name.",
                  )),
    "garrick_cobble": dict(
        sheet=_ts(str_=9, dex=14, con=11, int_=12, wis=11, cha=13, hp=11, ac=12, level=2, klass="tinker",
                  race="halfling", profs=["sleight_of_hand", "persuasion"]),
        mannerisms="Juggles a tin cup while pitching; pats the cart like a fond, noisy old dog.",
        dialogue=("A bargain, friend, a steal! You won't see its like till the next tinker, and he's a "
                  "crook who'd sell you a bent nail and call it a crown jewel.",
                  "Roads east are bad this season -- bandits at the ford, wolves past the mill, and "
                  "a taxman with a new smile. Buy a good lantern, eh? Two? I'll throw in flint.",
                  "Walk me to the next town and I'll throw in the whetstone and half the gossip. "
                  "Company's worth more than coin out here, and I've got ears in every hayloft.",
                  "That buckle's army surplus -- honest surplus, not the kind that still screams. "
                  "Fits your belt, not your conscience.",
                  "If you're carrying anything 'found,' I don't ask. If you're carrying trouble, I "
                  "price accordingly. Fair's the only road I know.",
                  )),
    "jessa_quickfingers": dict(
        sheet=_ts(str_=10, dex=15, con=11, int_=13, wis=11, cha=14, hp=14, ac=13, level=3, klass="dealer",
                  race="tiefling", profs=["deception", "sleight_of_hand", "persuasion"]),
        mannerisms="Shuffles coins across her knuckles; smiles with half her mouth.",
        dialogue=("Everything's for sale, sweetness -- the trick is knowing what you're really buying, "
                  "and whether you'll still like the taste of it in the morning.",
                  "I don't ask where you got it. You don't ask where it's going. We'll get along "
                  "beautifully, and Waterdeep stays beautifully ignorant.",
                  "That price is friendship rates. Push me and you'll meet the other rate -- the one "
                  "my friends in the Watch use when they're feeling creative.",
                  "Try the ring on. No, the left hand -- superstition pays my rent. Now tell me "
                  "what story you're running from.",
                  "A Masked Lord owes me a favor, which means I owe you nothing unless it profits "
                  "us both. That's the Trades Ward in one sentence.",
                  )),
    "old_embric": dict(
        sheet=_ts(str_=15, dex=11, con=14, int_=12, wis=13, cha=11, hp=24, ac=15, level=4, klass="weaponsmith",
                  profs=["athletics", "history"], attacks=[{"name": "warhammer", "bonus": 4, "damage": "1d8+2", "reach": "melee"}]),
        mannerisms="Squints down every blade he hands over; speaks slower the more it matters.",
        dialogue=("I made that. I don't make junk. If it breaks, you broke it wrong or you met "
                  "someone better -- and either way, don't bring me the pieces with excuses.",
                  "A weapon's a promise. Don't buy more promise than you mean to keep, because "
                  "steel remembers cowards the way dogs remember fear.",
                  "There's one blade I'll not price. It's not for sale -- it's for whoever it's for, "
                  "and you'll know if that's you before you ask.",
                  "Feel the weight. Good. Now feel the balance. If your wrist lies to you, your "
                  "enemy won't.",
                  "I forged for mercenaries once. Learned their language. Learned what regret sounds "
                  "like when it clanks on a table.",
                  )),
    "madame_vashti": dict(
        sheet=_ts(str_=9, dex=12, con=11, int_=15, wis=14, cha=16, hp=16, ac=12, level=4, klass="curio dealer",
                  race="half-elf", profs=["arcana", "deception", "insight"]),
        mannerisms="Lets a long pause sit before naming a price; touches each piece like it's sleeping.",
        dialogue=("Every curio has a story, and every story has a price. This one's is... expensive, "
                  "in the way that makes your purse lighter and your sleep more interesting.",
                  "I deal in the strange, the old, and the slightly cursed. Do specify which you're "
                  "after, darling -- I dress them differently but they share a wardrobe.",
                  "Buy it if you must. Only don't come back to tell me it whispers. They all whisper "
                  "eventually; the art is deciding which voices to answer.",
                  "That ring belonged to someone who loved too quickly. It still does. Are you sure "
                  "you want that kind of loyalty?",
                  "The Chasm market pays for pretty dangers. Bring me something from the old quarter "
                  "and I'll make you forget what you paid.",
                  )),
    "halgrim_pawn": dict(
        sheet=_ts(str_=13, dex=11, con=13, int_=11, wis=12, cha=11, hp=20, ac=13, level=3, klass="pawnbroker",
                  profs=["intimidation", "insight"]),
        mannerisms="Bites coins out of habit; keeps one hand below the counter.",
        dialogue=("Dock-ward rates: I pay little, I ask less. That's why you came down here instead "
                  "of the Wide, isn't it -- because respectable folk have respectable prices.",
                  "Hot goods? Cold goods? On this counter it's all just goods once the ink dries. "
                  "Name your number and don't waste my afternoon with heroics.",
                  "Try to cheat me and the harbor's right there. It's heard a lot of last words and "
                  "even more last-minute bargains that didn't take.",
                  "I know what came off which ship before the captain does. That knowledge costs, "
                  "but ignorance costs more in the Dock Ward.",
                  "Buyin' or sellin'? Pick. I ain't got all day, and the tide doesn't wait for "
                  "your sob story either.",
                  )),
    "quillan_myr": dict(
        sheet=_ts(str_=8, dex=12, con=12, int_=18, wis=15, cha=12, hp=22, ac=13, level=7, klass="archmage",
                  profs=["arcana", "history"], attacks=[{"name": "arcane bolt", "bonus": 7, "damage": "2d8", "reach": "ranged"}]),
        mannerisms="Finishes your sentences distractedly; addresses the air beside you as often as you.",
        dialogue=("You came a long way for trinkets. Very well -- but do not touch the blue ones; "
                  "they remember fingers, and not kindly.",
                  "Coin? I've no use for coin. Bring me a thing I cannot buy and we'll talk like "
                  "civilized minds instead of cattle with purses.",
                  "The wards remember faces. Mine remembers yours now. Tread accordingly, and don't "
                  "make me explain how a tower learns to dislike someone.",
                  "That staff is not for you. Yet. Convince me otherwise with something sharper than "
                  "gold -- a page, a secret, a problem worth solving.",
                  "I sell marvels to keep them from worse owners. If that offends your purse, go buy "
                  "a dull knife somewhere honest.",
                  )),
    "lady_of_the_grove": dict(
        sheet=_ts(str_=10, dex=16, con=12, int_=14, wis=17, cha=18, hp=26, ac=15, level=7, klass="fey trader",
                  race="fey", creature_type="fey", profs=["nature", "deception", "persuasion"],
                  attacks=[{"name": "bramble lash", "bonus": 6, "damage": "1d10+3", "reach": "melee"}]),
        mannerisms="Speaks in the second person about you as if telling your story; never quite blinks.",
        dialogue=("Welcome, mortal, to the green where the light bends toward old promises. You will "
                  "pay in coin, or memory, or years -- choose quickly, before the grove chooses for you.",
                  "I do not bargain. I offer. The offer is fair; it is only never kind, and kindness "
                  "was never the currency of roots and rain.",
                  "Take the gift freely given. Refuse the gift, and we are still bound -- that is the "
                  "way of it, and mortals always look surprised when the forest keeps accounts.",
                  "You harmed a sapling on the path in. You will mend it, or you will pay double in "
                  "something that grows back slower than coin.",
                  "This draught remembers summer. Drink, and remember with it -- or don't, and owe me "
                  "the forgetting.",
                  )),
    "shyntra_drow": dict(
        sheet=_ts(str_=10, dex=16, con=12, int_=15, wis=13, cha=15, hp=24, ac=15, level=6, klass="trade-mistress",
                  race="drow", profs=["deception", "intimidation", "insight"],
                  alignment="Neutral Evil", alignment_key="ne",
                  attacks=[{"name": "poisoned rapier", "bonus": 6, "damage": "1d8+3", "reach": "melee"}]),
        mannerisms="Smiles only with the mouth; lets her guards' shadows do the threatening.",
        dialogue=("Surface-dweller. How quaint, and how brave, to deal this far down where the dark "
                  "has teeth and manners. Sit. Let us pretend civility is still a currency.",
                  "My wares are rare because the getting of them is lethal. The price reflects the "
                  "corpses, the bribes, and the silence required to ship them through spider country.",
                  "Betray the bargain and House Auvryndar will find you. We are very good at finding "
                  "things that thought the Underdark was merely deep.",
                  "That ring rode up on a corpse that used to be a rival. Wear it if you dare; I "
                  "don't offer refunds for conscience.",
                  "You may pay in gold, blood, or leverage. Choose the one you'll miss least when "
                  "morning never comes.",
                  )),
    "xanthros": dict(
        sheet=_ts(str_=15, dex=14, con=15, int_=16, wis=13, cha=17, hp=33, ac=16, level=8, klass="cambion collector",
                  race="fiend", creature_type="fiend", profs=["deception", "persuasion", "arcana"],
                  alignment="Lawful Evil", alignment_key="le",
                  attacks=[{"name": "infernal blade", "bonus": 7, "damage": "1d10+4", "reach": "melee"}]),
        mannerisms="Reads the fine print of your soul while smiling; taps a clawed finger when pleased.",
        dialogue=("Ahh, a customer with a pulse. Refreshing down here where so many bargains end "
                  "with less of one. Now -- what would you give to possess what you desire?",
                  "Gold is acceptable. A favor is better. A name, a year, a regret -- best of all, "
                  "because those appreciate while coin only tarnishes.",
                  "Read the terms. Read them again. I never cheat; I simply let you cheat yourself "
                  "with a smile and a signature.",
                  "This blade drank a paladin's oath once. It thirsts still. If you buy it, mean "
                  "what you swing, or it will mean it for you.",
                  "You want extraordinary. Good. Ordinary bores me. Tell me what you'll miss when "
                  "the price comes due -- I'll make it worth missing.",
                  )),
    "embered_mara": dict(
        sheet=_ts(str_=12, dex=13, con=13, int_=12, wis=14, cha=12, hp=22, ac=13, level=4, klass="caravan trader",
                  profs=["survival", "insight", "intimidation"]),
        mannerisms="Glances at the horizon mid-sentence; keeps a tally stick she notches as you deal.",
        dialogue=("Crossed every road in Faerûn twice, rain or raid or worse. Whatever you need, I've "
                  "hauled it through country that would make your mapmaker weep.",
                  "Fair price, fair weight, and I remember a cheat to my grave and into the next "
                  "if Tymora's feeling literal. We clear?",
                  "Don't ask about the third wagon. The pay for not asking is the wagon stays shut "
                  "and you keep your teeth.",
                  "News costs if it's fresh. This bit's half a day old: the Ash Road's got new "
                  "predators and older grudges.",
                  "You want guards? Fine. You want guards who don't peek? That costs more, because "
                  "curiosity kills my profit margin.",
                  )),
    "brannor_stonehand": dict(
        sheet=_ts(str_=15, dex=11, con=15, int_=11, wis=12, cha=11, hp=26, ac=16, level=4, klass="blacksmith",
                  race="dwarf", profs=["athletics", "history"],
                  attacks=[{"name": "smith's hammer", "bonus": 4, "damage": "1d8+2", "reach": "melee"}])),
    "sister_yelena": dict(
        sheet=_ts(str_=10, dex=11, con=12, int_=13, wis=15, cha=14, hp=18, ac=13, level=3, klass="acolyte",
                  profs=["religion", "medicine", "persuasion"],
                  attacks=[{"name": "mace", "bonus": 2, "damage": "1d6", "reach": "melee"}])),
}


def _apply_extras():
    for k, ex in _EXTRAS.items():
        t = TRADESMEN.get(k)
        if t is None:
            continue
        card = t.card
        if card is not None:
            if ex.get("dialogue") and not card.dialogue_examples:
                card = _dc.replace(card, dialogue_examples=tuple(ex["dialogue"]))
            if ex.get("mannerisms") and not card.mannerisms:
                card = _dc.replace(card, mannerisms=ex["mannerisms"])
        TRADESMEN[k] = _dc.replace(t, card=card, sheet=ex.get("sheet"))


_apply_extras()


def build_trader(key: str):
    t = TRADESMEN.get(key)
    if t is None or t.sheet is None:
        return None
    sheet = _copy.deepcopy(t.sheet)
    sheet["card"] = t.card
    return _Combatant(name=t.name, is_pc=False, sheet=sheet)
