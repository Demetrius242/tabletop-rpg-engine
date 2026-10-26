from __future__ import annotations

from dataclasses import dataclass

LAW = ("lawful", "neutral", "chaotic")
MORALITY = ("good", "neutral", "evil")


@dataclass(frozen=True)
class Alignment:
    key: str
    label: str
    law: str
    morality: str
    tendency: str


ALIGNMENTS = {
    "lg": Alignment("lg", "Lawful Good", "lawful", "good",
                    "Does the right thing as duty and code demand; honest, honorable, dependable."),
    "ng": Alignment("ng", "Neutral Good", "neutral", "good",
                    "Does the most good without much care for rules; kind and helpful first."),
    "cg": Alignment("cg", "Chaotic Good", "chaotic", "good",
                    "Follows conscience over law; values freedom and mercy, distrusts authority."),
    "ln": Alignment("ln", "Lawful Neutral", "lawful", "neutral",
                    "Order, tradition, and the code above all -- reliable, but unbending."),
    "tn": Alignment("tn", "True Neutral", "neutral", "neutral",
                    "Keeps the balance; acts by circumstance and self-interest, avoids extremes."),
    "cn": Alignment("cn", "Chaotic Neutral", "chaotic", "neutral",
                    "Prizes personal freedom; unpredictable, follows whim more than principle."),
    "le": Alignment("le", "Lawful Evil", "lawful", "evil",
                    "Takes what it wants within rules and hierarchy; methodical, honors useful bargains."),
    "ne": Alignment("ne", "Neutral Evil", "neutral", "evil",
                    "Pure self-interest; does whatever it can get away with, no loyalty but advantage."),
    "ce": Alignment("ce", "Chaotic Evil", "chaotic", "evil",
                    "Violence, greed, and cruelty unchecked; destructive and contemptuous of order."),
}

ORDER = ("lg", "ng", "cg", "ln", "tn", "cn", "le", "ne", "ce")


def get(key: str) -> Alignment | None:
    return ALIGNMENTS.get((key or "").lower())


@dataclass(frozen=True)
class AlignmentProfile:
    true: Alignment
    presented: Alignment

    @property
    def is_masking(self) -> bool:
        return self.true.key != self.presented.key

    def narration_note(self) -> str:
        if not self.is_masking:
            return f"{self.true.label}: {self.true.tendency}"
        return (f"presents as {self.presented.label} ({self.presented.tendency}) "
                f"but is truly {self.true.label} ({self.true.tendency})")


def profile(true_key: str, presented_key: str | None = None) -> AlignmentProfile | None:
    true = get(true_key)
    if true is None:
        return None
    presented = get(presented_key) if presented_key else true
    return AlignmentProfile(true=true, presented=presented or true)


CREATURE_TYPES = ("aberration", "beast", "celestial", "construct", "dragon", "elemental",
                  "fey", "fiend", "giant", "humanoid", "monstrosity", "ooze", "plant", "undead")

EVIL_AND_GOOD_TYPES = ("aberration", "celestial", "elemental", "fey", "fiend", "undead")


def detect_evil_and_good(creature_type: str) -> str | None:
    ct = (creature_type or "").lower()
    return ct if ct in EVIL_AND_GOOD_TYPES else None


def protection_disadvantage(attacker_type: str) -> bool:
    return (attacker_type or "").lower() in EVIL_AND_GOOD_TYPES


def magic_circle_blocks(configured_type: str, creature_type: str) -> bool:
    ct = (creature_type or "").lower()
    cfg = (configured_type or "").lower()
    return cfg in EVIL_AND_GOOD_TYPES and ct == cfg


@dataclass(frozen=True)
class AlignedItem:
    key: str
    name: str
    requires: tuple
    mismatch: str
    benefit: str


ALIGNED_ITEMS = {
    "holy_avenger": AlignedItem(
        "holy_avenger", "Holy Avenger", ("good",),
        "A non-good wielder gains none of its holy power -- no aura, no extra radiant damage.",
        "In good hands (a paladin): +3 to hit/damage, +2d10 radiant vs fiends and undead, and a "
        "magic-resistance aura for nearby allies."),
    "talisman_of_pure_good": AlignedItem(
        "talisman_of_pure_good", "Talisman of Pure Good", ("good",),
        "An evil creature that touches it takes 6d6 radiant damage; a neutral creature, 1d6 per use.",
        "A good cleric or paladin can unleash Searing Burst on fiends/undead and add +2 to attacks."),
    "talisman_of_ultimate_evil": AlignedItem(
        "talisman_of_ultimate_evil", "Talisman of Ultimate Evil", ("evil",),
        "A good creature that touches it takes 8d6 necrotic damage; a neutral creature, 4d6 per use.",
        "An evil wielder can open a flaming chasm beneath good/neutral foes and add +2 to attacks."),
    "book_of_exalted_deeds": AlignedItem(
        "book_of_exalted_deeds", "Book of Exalted Deeds", ("good",),
        "Only a good creature can absorb its teachings; others gain nothing and the book vanishes.",
        "Over days of study: +2 Wisdom (max 24), an exalted boon, and access to celestial allies."),
    "book_of_vile_darkness": AlignedItem(
        "book_of_vile_darkness", "Book of Vile Darkness", ("evil",),
        "A non-evil reader risks madness and gains none of its dark gifts.",
        "Dark study grants an ability increase, a vile boon, and command over the lower planes."),
}


def _meets(al: Alignment, requires) -> bool:
    for v in requires:
        if v in MORALITY and al.morality != v:
            return False
        if v in LAW and al.law != v:
            return False
    return True


def item_attunement(actor_alignment_key: str, item_key: str) -> dict | None:
    item = ALIGNED_ITEMS.get((item_key or "").lower())
    al = get(actor_alignment_key)
    if item is None or al is None:
        return None
    ok = _meets(al, item.requires)
    return {"item": item.name, "requires": item.requires, "allowed": ok,
            "effect": item.benefit if ok else item.mismatch}


def _opposed(a: str, b: str) -> bool:
    return {"good", "evil"} == {a, b} or {"lawful", "chaotic"} == {a, b}


def sentient_item_conflict(wielder_alignment_key: str, item_alignment_key: str) -> dict | None:
    w = get(wielder_alignment_key)
    it = get(item_alignment_key)
    if w is None or it is None:
        return None
    conflict = _opposed(w.morality, it.morality) or _opposed(w.law, it.law)
    return {"conflict": conflict, "wielder": w.label, "item_alignment": it.label,
            "note": ("The item resists and may seize control (a Charisma contest)."
                     if conflict else "Closely enough aligned; the item does not struggle.")}
