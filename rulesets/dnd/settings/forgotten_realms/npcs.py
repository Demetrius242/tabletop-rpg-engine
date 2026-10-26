from __future__ import annotations

import copy
from dataclasses import dataclass

from engine.state import Combatant
from rulesets.dnd.settings.base import NPCCard


@dataclass(frozen=True)
class NPCDef:
    card: NPCCard
    sheet: dict


def _sheet(*, str_=10, dex=10, con=10, int_=10, wis=10, cha=10,
           hp=11, ac=12, pb=2, level=2, klass="commoner", race="human", profs=(), attacks=None,
           creature_type="humanoid", alignment="", alignment_key="",
           gender="non_applicable", intelligence=10) -> dict:
    s = {
        "abilities": {"str": str_, "dex": dex, "con": con, "int": int_, "wis": wis, "cha": cha},
        "proficiencies": list(profs), "proficiency_bonus": pb,
        "hp": hp, "max_hp": hp, "ac": ac,
        "level": level, "class": klass, "race": race,
        "attacks": list(attacks or [{"name": "fist", "bonus": 2, "damage": "1d4", "reach": "melee"}]),
        "intelligence": intelligence,
        "creature_type": creature_type, "comprehends_language": True, "mindless": False,
        "alignment": alignment, "alignment_key": alignment_key,
        "gender": gender,
    }
    return s


NPCS: dict[str, NPCDef] = {
    "maela_brightwater": NPCDef(
        card=NPCCard(
            "maela_brightwater", "Maela Brightwater", "innkeeper", "human",
            description="A broad, grey-braided woman with flour on her forearms and a ledger-sharp eye.",
            demeanor="Warm and motherly to paying guests; unflappable.",
            voice="Plain, dry humor; calls everyone 'duck' and misses nothing.",
            mannerisms="Wipes the same clean spot on the bar while she sizes you up; never sits.",
            dialogue_examples=(
                "Sit yourself down, duck -- you look like three days of bad road and a fourth of bad "
                "decisions. Cup of broth first, questions after.",
                "Room's two silver, bath's a copper, and the stew won't kill you. That's a promise, "
                "not a boast, and I've kept worse promises for worse folk.",
                "I hear things in this taproom. Doesn't mean I say them aloud. Depends who's buying, "
                "who's listening, and whether I like the look of their boots.",
                "There's a back stair by the cellar, duck, if a body needed to not be seen leaving. "
                "Hypothetically. I'd know nothing about it either way.",
                "Pay your tab and we'll stay friends. Don't, and you'll find Faerûn's a small place "
                "-- and I'm the reason it feels smaller.",
            ),
            secret="She fences information to the Harpers and keeps a room for those who need to vanish.",
            hook="Knows who's hiring, who's lying, and which road has gone bad this season."),
        sheet=_sheet(str_=11, dex=10, con=13, int_=12, wis=14, cha=13, hp=16, ac=11, level=3,
                     klass="commoner", profs=["insight", "persuasion"], intelligence=12,
                     attacks=[{"name": "cudgel", "bonus": 2, "damage": "1d6", "reach": "melee"}])),

    "sef_the_quill": NPCDef(
        card=NPCCard(
            "sef_the_quill", "Sef the Quill", "Harper contact", "half-elf",
            description="A slight, ink-stained clerk with quick eyes and a forgettable face.",
            demeanor="Mild, helpful, eager to seem boring.",
            voice="Soft and precise; hides meaning in small talk about the weather and the price of grain.",
            mannerisms="Adjusts spectacles he doesn't need; folds every scrap of paper into quarters.",
            dialogue_examples=(
                "Terrible weather for the barley, they say. Terrible weather for a lot of things "
                "lately -- though I wouldn't know, I only mind the ink and the margins.",
                "I only copy ledgers for honest merchants. Still, a ledger tells you who fears whom, "
                "if you read the smudges and the dates men tried to hide.",
                "Walk with me past the bookbinder's, would you? Nice day for it. Don't look at the "
                "man in the green cloak -- and don't slow down when he looks at you.",
                "There's quiet work, if you've the stomach for it. Not heroic work. The kind that "
                "stops a cruelty before it learns to call itself law.",
                "You were never here. I was always here, copying a dull inventory. That's the "
                "arrangement, and arrangements keep people breathing.",
            ),
            secret="A ranking Harper agent running a cell out of a bookbinder's shop.",
            hook="Recruits the party for quiet work: stop a cruelty before it becomes a catastrophe."),
        sheet=_sheet(str_=9, dex=14, con=11, int_=15, wis=13, cha=12, hp=13, ac=13, level=3,
                     klass="agent", race="half-elf", profs=["deception", "investigation", "insight"],
                     intelligence=15,
                     attacks=[{"name": "hidden dagger", "bonus": 4, "damage": "1d4+2", "reach": "melee"}])),

    "ulthar_vond": NPCDef(
        card=NPCCard(
            "ulthar_vond", "Ulthar Vond", "Zhentarim fixer", "human",
            description="A trim man in good, sober clothes, rings on careful fingers, a banker's smile.",
            demeanor="Courteous, generous, entirely transactional.",
            voice="Smooth and reasonable; every threat sounds like a favor.",
            mannerisms="Turns a heavy signet ring while he talks; never raises his voice, ever.",
            dialogue_examples=(
                "Please, sit -- you look like a person who carries problems in both pockets. Wine? "
                "I find business goes down easier with something good in the glass and bad news "
                "already swallowed.",
                "I don't deal in threats, my friend. I deal in consequences, and I'd so much rather "
                "we never had to discuss them over a second bottle.",
                "The work is simple, the pay is generous, and your name stays off every paper in "
                "three cities. A nod is enough. We're agreed, aren't we?",
                "You owe me now -- not money, not yet. I keep careful accounts of favors, and I "
                "promise you, ask anyone who's settled late how patient I am.",
                "The Black Network rewards loyalty with gold and introductions. It has a longer, "
                "colder memory for the other thing, and I do hate awkwardness.",
            ),
            secret="Launders the Black Network's coin through legitimate caravans; owns several Watch debts.",
            hook="Offers lucrative, deniable jobs -- and remembers exactly what you owe him."),
        sheet=_sheet(str_=10, dex=12, con=12, int_=14, wis=13, cha=16, hp=18, ac=13, level=4,
                     klass="fixer", profs=["persuasion", "deception", "insight"], intelligence=14,
                     alignment="Lawful Evil", alignment_key="le",
                     attacks=[{"name": "poisoned needle", "bonus": 3, "damage": "1d4+1", "reach": "melee"}])),

    "mother_aldith": NPCDef(
        card=NPCCard(
            "mother_aldith", "Mother Aldith", "priest of Tymora", "halfling",
            description="A round, beaming halfling priest with a lucky copper worn smooth on a thong.",
            demeanor="Generous, fearless, a touch of the gambler in everything she does.",
            voice="Bright and blessing-quick; 'Fortune favors the bold, dear -- so be bold.'",
            mannerisms="Flips her worn copper and catches it without looking; laughs at her own nerve.",
            dialogue_examples=(
                "Fortune favors the bold, dear -- so be bold, lift your chin, and let the Lady sort "
                "the rest before fear talks you out of trying.",
                "You're hurt. Sit, hush, let old Aldith see -- ah. There. Tymora's luck knits what "
                "the road tears, if you'll hold still and trust a halfling's hands.",
                "I'd wager my last copper you're trouble. Good. Trouble's where the Lady does her "
                "best work, and I've never been afraid of long odds.",
                "The temple's poorer than it looks, between us. A debt came due that shouldn't have, "
                "and I paid it smiling because the alternative was worse for my flock.",
                "Bring back what was stolen from us and I'll call down every blessing I've got -- "
                "healing, luck, the whole noisy chorus -- and I'll mean every word of it.",
            ),
            secret="Bankrupted the temple covering a parishioner's debt to the Zhentarim; the note is due.",
            hook="Trades healing and blessings for the recovery of a stolen reliquary."),
        sheet=_sheet(str_=9, dex=11, con=12, int_=11, wis=16, cha=14, hp=17, ac=14, level=4,
                     klass="cleric", race="halfling", profs=["medicine", "religion", "insight"],
                     intelligence=11,
                     attacks=[{"name": "mace", "bonus": 2, "damage": "1d6", "reach": "melee"},
                              {"name": "sacred flame", "bonus": 5, "damage": "1d8", "reach": "ranged"}])),

    "greasy_pell": NPCDef(
        card=NPCCard(
            "greasy_pell", "Greasy Pell", "dock-ward fence", "human",
            description="A wiry, twitchy man who smells of fish-oil and smoke, always near an exit.",
            demeanor="Nervy, ingratiating, quick to deal and quicker to bolt.",
            voice="Rapid, wheedling, drops names he shouldn't.",
            mannerisms="Eyes flick to the door every few words; counts coins twice with quick, dirty fingers.",
            dialogue_examples=(
                "Friend! Friend -- easy, easy. You didn't hear it from me, but I can move that trinket "
                "by morning. No questions, half its worth, and you never saw my face.",
                "Keep your voice down, will you? Half the men in here'd sell their mothers for a "
                "silver and a pat on the head, and I know which half by the smell.",
                "Came off the night boat, that did -- wrapped in oilcloth, still damp. Don't ask "
                "whose. I never asked, see? That's how Pell stays breathing another week.",
                "I'll give you four. Four! It's hot as a forge and you know it. ...Fine. Five, and "
                "you're robbing a poor man who only wants to eat. Hand it over.",
                "If anyone asks, we never spoke. If the Watch asks, I'll cry on their boots -- "
                "I'm very good at crying. Wretched, helpless. Academy-trained.",
            ),
            secret="Skims from the smugglers he serves and is one slip from the harbor floor.",
            hook="Will buy or move anything; knows what came off the ships last night."),
        sheet=_sheet(str_=10, dex=14, con=10, int_=12, wis=11, cha=11, hp=11, ac=12, level=2,
                     klass="rogue", profs=["sleight_of_hand", "deception", "stealth"], intelligence=12,
                     attacks=[{"name": "gutting knife", "bonus": 4, "damage": "1d4+2", "reach": "melee"}])),

    "sergeant_dornan": NPCDef(
        card=NPCCard(
            "sergeant_dornan", "Sergeant Dornan Holt", "City Watch sergeant", "half-orc",
            description="A scarred, square half-orc in Watch livery, helmet under one heavy arm.",
            demeanor="Brusque, tired, fundamentally fair.",
            voice="Clipped and weary; has heard every excuse twice.",
            mannerisms="Cracks the knuckles of his shield hand; sizes up exits and weapons before faces.",
            dialogue_examples=(
                "Move along or have a reason. Those are the choices, and I'm short on patience for "
                "a third -- especially after midnight in my ward.",
                "I've heard that one before. Twice, in fact. Once from a man we fished out of the "
                "harbor the next morning, still smiling like he thought charm was armor.",
                "I don't care who your father is or whose seal is on your letter. In my ward the "
                "law's the law, and tonight the law's me with a sore back and a short temper.",
                "There's a thing the Patriars won't let me touch -- too many silk gloves in the "
                "way. Help me touch it, and I'll forget I saw a knife on your belt. One night only.",
                "Keep your nose clean and we'll never speak again. I'd consider that a kindness "
                "from both of us, and I don't hand those out often.",
            ),
            secret="Quietly protects a witness the Patriars want silenced, at growing risk to himself.",
            hook="Will overlook small trouble for help with the crimes his masters won't let him touch."),
        sheet=_sheet(str_=16, dex=11, con=15, int_=10, wis=12, cha=10, hp=30, ac=16, level=4,
                     klass="guard", race="half-orc", profs=["athletics", "intimidation"], intelligence=10,
                     attacks=[{"name": "watch sword", "bonus": 5, "damage": "1d8+3", "reach": "melee"},
                              {"name": "crossbow", "bonus": 3, "damage": "1d8", "reach": "ranged"}])),
}

from rulesets.dnd.settings.forgotten_realms.underdark_npcs import NPCS as _UNDERDARK_NPCS
NPCS = {**NPCS, **_UNDERDARK_NPCS}

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
