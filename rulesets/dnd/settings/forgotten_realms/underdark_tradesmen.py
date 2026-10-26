from __future__ import annotations

import copy as _copy
import dataclasses as _dc

from engine.state import Combatant as _Combatant
from rulesets.dnd.settings.base import NPCCard, Tradesman

TRADESMEN = {
    "y_underdark": Tradesman(
        "y_underdark", "Y", "Gracklstugh outskirts", "underdark",
        tier="town", categories=("gear", "tool", "potion"), max_rarity="uncommon",
        stock_size=6, markup=1.2, sell_rate=0.45, restock_interval=4,
        card=NPCCard("y_underdark", "Y", "deep gnome salvage trader", "deep gnome",
                     adventure="out_of_the_abyss",
                     description="A svirfneblin in smoked goggles beside a salvage cart.",
                     demeanor="Wary, fair within limits.",
                     voice="Clipped Undercommon; coin first.",
                     mannerisms="Taps stone twice before speaking.",
                     dialogue_examples=(
                         "Rope, picks, antitoxin -- pick two, pay now. Ask for credit and leave before "
                         "I decide you're worth the trouble of remembering.",
                         "Velkynvelve survivors pay double. I don't ask why you escaped or who you "
                         "left screaming. Coin talks cleaner than confession.",
                         "Mind flayer silver spends same as any, if you know how to wrap it. Don't "
                         "flash it in Gracklstugh unless you want friends you can't see.",
                         "I sell necessities, not hope. Hope is what gets surface folk eaten between "
                         "breakfast and regret.",
                         "Tap stone twice when you leave. Superstition keeps me alive. You should "
                         "borrow some.",
                     ),
                     secret="Reports refugee traffic to Blingdenstone.",
                     hook="Survival gear at the Gracklstugh edge.")),
    "kuo_toa_trader": Tradesman(
        "kuo_toa_trader", "Gissnek", "Sloobludop fish market", "sloobludop",
        tier="village", categories=("gear", "potion"), max_rarity="common",
        stock_size=4, markup=0.9, sell_rate=0.35, restock_interval=5,
        card=NPCCard("kuo_toa_trader", "Gissnek", "kuo-toa fishmonger", "kuo-toa",
                     adventure="out_of_the_abyss",
                     description="A damp kuo-toa with a basket of blind cave fish and too many teeth.",
                     demeanor="Cheerfully mad; prices change when 'the god' whispers.",
                     voice="Gurgling trade-chant.",
                     mannerisms="Offers fish as gift, then demands payment.",
                     dialogue_examples=(
                         "Fish for coin, coin for god, god for fish -- good trade, yes? Gissnek is "
                         "honest priest and honest merchant, mostly same thing!",
                         "You not drow. Good! Drow not buy, drow take, drow make sermon about taking. "
                         "You buy like person with soul still attached.",
                         "Lamp oil for boats, rope for boats, prayers for boats. Darklake hungry; "
                         "Gissnek sells everything that keeps boats out of its belly.",
                         "Take fish as gift! ...Now pay for gift. Tradition. Bloppblippolp approves "
                         "of tradition. Probably.",
                         "Paddles cheap today. Gods whisper cheap prices when hungry. You hungry? "
                         "Gissnek can tell.",
                     ),
                     secret="Sells stolen skiff paddles.",
                     hook="Cheap consumables and Darklake passage rumors.")),
}

_EXTRAS = {
    "y_underdark": {
        "sheet": {
            "abilities": {"str": 10, "dex": 14, "con": 12, "int": 13, "wis": 14, "cha": 10},
            "proficiencies": ["insight", "investigation"], "proficiency_bonus": 2,
            "hp": 16, "max_hp": 16, "ac": 14, "level": 2, "class": "merchant", "race": "deep gnome",
            "attacks": [{"name": "light crossbow", "bonus": 4, "damage": "1d8+2", "reach": "ranged"}],
            "intelligence": 13, "creature_type": "humanoid", "comprehends_language": True,
            "mindless": False, "alignment": "Neutral Good", "alignment_key": "ng",
        },
    },
    "kuo_toa_trader": {
        "sheet": {
            "abilities": {"str": 12, "dex": 10, "con": 12, "int": 10, "wis": 11, "cha": 12},
            "proficiencies": ["persuasion"], "proficiency_bonus": 2,
            "hp": 18, "max_hp": 18, "ac": 11, "level": 1, "class": "merchant", "race": "kuo-toa",
            "attacks": [{"name": "club", "bonus": 3, "damage": "1d4+1", "reach": "melee"}],
            "intelligence": 10, "creature_type": "humanoid", "comprehends_language": True,
            "mindless": False, "alignment": "Chaotic Neutral", "alignment_key": "cn",
        },
    },
}


def _apply():
    for k, ex in _EXTRAS.items():
        t = TRADESMEN.get(k)
        if t is None:
            continue
        TRADESMEN[k] = _dc.replace(t, sheet=ex.get("sheet"))


_apply()


def build_trader(key: str):
    t = TRADESMEN.get(key)
    if t is None or t.sheet is None:
        return None
    sheet = _copy.deepcopy(t.sheet)
    sheet["card"] = t.card
    return _Combatant(name=t.name, is_pc=False, sheet=sheet)
