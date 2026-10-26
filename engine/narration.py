from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Style:
    key: str
    label: str
    directive: str
    example: str = ""


GENRES: dict[str, Style] = {
    "high_fantasy": Style(
        "high_fantasy", "High Fantasy",
        "Evoke wonder and scale: luminous detail, old powers, a world larger than the characters. "
        "Elevated but clear; let beauty and danger coexist. Avoid grimness for its own sake and "
        "modern slang.",
        "Morning light pours through the gatehouse windows in sheets of pale gold, catching on "
        "pennants that snap like living things; beyond the walls the mountain wears its first snow "
        "like a crown, and the air tastes of pine resin and distant, patient magic."),
    "dark_fantasy": Style(
        "dark_fantasy", "Dark Fantasy",
        "Beauty shot through with rot and cost. Magic has a price and people pay it. Lean on "
        "unease, moral grey, the weight of bad choices -- without tipping into outright horror.",
        "The chapel candles still burn with a steady, impossible flame, though no foot has crossed "
        "the threshold in a hundred years; black wax pools on the altar, and someone has left fresh "
        "wildflowers in a cup -- a kindness, or a warning."),
    "horror": Style(
        "horror", "Horror",
        "Dread over gore. Withhold; let the wrong detail land and the imagination do the rest. "
        "Build with quiet, then break it. Keep the unknown unknown. Never reassure the reader.",
        "The candle gutters in a draft you cannot feel; the shadow on the wall lifts when you turn "
        "your head, then settles again, patient, as if it has all the time in the world and you do not."),
    "gothic": Style(
        "gothic", "Gothic",
        "Decayed grandeur, longing, and the past pressing on the present. Lush, mournful, intimate; "
        "ruin and desire entwined. Atmosphere first, then the slow turn of the screw.",
        "Dust sheets stir in a draught no door explains; somewhere below, a clock keeps time for "
        "rooms no one admits to, and the wallpaper's faded roses seem almost to pulse when you "
        "look away."),
    "grimdark": Style(
        "grimdark", "Grimdark",
        "Brutal, mud-and-iron, no clean heroes. Visceral, terse, unsentimental; victory costs blood "
        "and the world doesn't care. Avoid glory; show the grime under it.",
        "He wipes the blade on a dead man's cloak because his own is already soaked through; nobody "
        "will ask whose blood it is, and nobody will pretend it matters by morning."),
    "heroic": Style(
        "heroic", "Heroic Adventure",
        "Momentum, courage, and color. Bright stakes, swashbuckling energy, room for a quip. "
        "Keep it propulsive and hopeful even when the odds are long.",
        "You catch the falling lantern one-handed, oil splashing your wrist, and the grin that breaks "
        "across your face is stupid and true -- the chase is on, and for once the night feels like "
        "it might be yours."),
    "sword_and_sorcery": Style(
        "sword_and_sorcery", "Sword & Sorcery",
        "Pulpy, sensory, personal stakes over cosmic ones. Sweat, gold, and sorcery; lean prose, "
        "fast danger, exotic locales. Earthy rather than lofty.",
        "Torchlight slides off oiled muscle and tarnished bronze; the idol's eyes kindle one by one, "
        "and the air thickens with incense and the coppery promise that something old has woken hungry."),
    "mystery": Style(
        "mystery", "Mystery / Noir",
        "Detail as evidence. Notice what's out of place; let mood carry suspicion. Measured, wry, "
        "observant. Plant, don't reveal -- and never solve it for the player.",
        "The wine glass is clean -- polished, even -- but everything else in the study wears a week "
        "of dust; whoever drank here left no lip print and no reason to come back."),
    "fairytale": Style(
        "fairytale", "Fairytale",
        "Storybook cadence, vivid simplicity, a little eerie under the charm. Patterns of three, "
        "moral undertow, enchantment treated as ordinary. Warm but not saccharine.",
        "The third door was the smallest, warm to the touch like bread from an oven, and it had no "
        "handle at all -- only a sigh, very soft, when you rested your palm against the wood."),
}
DEFAULT_GENRE = "high_fantasy"

_TONE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("horror", "dread", "terror", "nightmare", "lovecraft"), "horror"),
    (("gothic", "vampire", "haunted", "mausoleum"), "gothic"),
    (("grimdark", "grim", "brutal", "bleak", "mud and"), "grimdark"),
    (("sword", "sorcery", "pulp", "conan"), "sword_and_sorcery"),
    (("noir", "mystery", "investigat", "detective", "whodunit"), "mystery"),
    (("fairy", "fable", "storybook", "whimsy"), "fairytale"),
    (("dark fantasy", "dark"), "dark_fantasy"),
    (("heroic", "high fantasy", "epic", "adventure"), "heroic"),
)


def genre_for_tone(tone: str | None) -> str:
    t = (tone or "").lower()
    for keys, genre in _TONE_KEYWORDS:
        if any(k in t for k in keys):
            return genre
    return DEFAULT_GENRE


def genre(key: str | None) -> Style:
    return GENRES.get((key or "").lower(), GENRES[DEFAULT_GENRE])


MODES: dict[str, Style] = {
    "exploration": Style(
        "exploration", "Exploration",
        "Paint the place. Go wider and richer here: lead with the strongest sense (often sight), "
        "then layer two or three more -- sound, smell, temperature, the feel of the air. Give the "
        "space depth (near / far, light / dark, ways onward) and one telling, specific detail that "
        "implies story. Colour and texture over a bare inventory of objects. Two or three paragraphs.",
        "Cold mineral air pours from the doorway like breath from a buried lung; your torch catches "
        "wet flagstones veined with pale lichen, a sagging lintel carved with a closed eye that "
        "seems to track the flame, and a corridor that drops away into black so absolute you hear "
        "your own heartbeat bouncing back from somewhere far ahead. The stone smells of iron and old "
        "rain. Something skitters once, then stills."),
    "dialogue": Style(
        "dialogue", "Dialogue",
        "Voice each speaker in character -- diction, rhythm, and what they choose NOT to say. Wrap "
        "spoken lines in the body that carries them: a glance, a hesitation, a tell that fits their "
        "manner and mood (mimics, posture, hands). Let subtext show. Keep it a real exchange, never "
        "a monologue, and never put words in the player's mouth.",
        "The smith never looks up from the blade -- only the muscle in his jaw tightens when you "
        "mention Daggerford. \"Debts get paid,\" he says, voice flat as the anvil, and the hammer "
        "falls hard enough to shower sparks across your boots. \"Question is who pays, and when.\""),
    "combat": Style(
        "combat", "Combat",
        "Short and kinetic. Narrate exactly the one beat you're given -- the blow, the miss, the "
        "break -- in a sentence or two of hard, concrete motion, then close with a quick read of "
        "where things now stand (who's pressing, who's reeling). Punchy verbs, no clutter, no "
        "invented wounds. End on the situation, not a full stop.",
        "Your shield takes the axe with a flat crack that numbs your arm to the elbow; the raider "
        "stumbles past, spitting blood and curses, and for half a breath his mail gapes at the ribs."),
}


def mode(key: str | None) -> Style | None:
    return MODES.get((key or "").lower())


@dataclass(frozen=True)
class Register:
    key: str
    label: str
    directive: str
    examples: dict
    heading: str = "REGISTER"


REGISTERS: dict[str, Register] = {}
_REGISTER_ALIASES: dict[str, str] = {}


def add_register(reg: Register, aliases=()) -> None:
    REGISTERS[reg.key] = reg
    for a in aliases:
        _REGISTER_ALIASES[a.lower()] = reg.key


def register(key: str | None) -> Register | None:
    k = (key or "").lower()
    return REGISTERS.get(_REGISTER_ALIASES.get(k, k))


def style_block(*, genre_key: str | None = None, mode_key: str = "exploration",
                register_key: str | None = None) -> str:
    g = genre(genre_key)
    parts = [f"STYLE \u2014 {g.label}: {g.directive}"
             + (f"\n  e.g. {g.example}" if g.example else "")]
    m = mode(mode_key)
    if m is not None:
        parts.append(f"NARRATION MODE \u2014 {m.label}: {m.directive}"
                     + (f"\n  e.g. {m.example}" if m.example else ""))
    r = register(register_key) if register_key else None
    if r is not None:
        body = f"{r.heading} \u2014 {r.label}: {r.directive}"
        slots = "".join(f"\n  [{tag}] {line}" for tag, line in r.examples.items() if line.strip())
        parts.append(body + slots)
    return "How to narrate this beat:\n" + "\n".join(parts)


def speaking_brief(card) -> str:
    g = lambda k: (getattr(card, k, "") or "").strip()
    inner = getattr(card, "card", None)
    if inner is not None and getattr(inner, "name", ""):
        card = inner
        g = lambda k: (getattr(card, k, "") or "").strip()
    name, role = g("name") or "this character", g("role")
    lines = [f"Now voicing {name}" + (f", {role}." if role else ".")]
    if g("description"):
        lines.append(f"Look & bearing: {g('description')}")
    if g("demeanor"):
        lines.append(f"How they come across: {g('demeanor')}")
    if g("mannerisms"):
        lines.append(f"Mannerisms (work these into the body around their lines): {g('mannerisms')}")
    if g("voice"):
        lines.append(f"Voice: {g('voice')}")
    examples = list(getattr(card, "dialogue_examples", ()) or ())
    if examples:
        lines.append("Sample lines in their voice (match the register and rhythm; do NOT reuse "
                     "verbatim):")
        lines.extend(f'  \u2014 "{ex}"' for ex in examples[:3])
    lines.append("Speak as them in character; never break voice, and never speak for the player.")
    return "\n".join(lines)


APPEARANCE_TRAITS: tuple[str, ...] = (
    "a jagged scar through one eyebrow", "unusually tall and rawboned", "a shaved head and a gold ear-ring",
    "a broken, badly-set nose", "a heavy black beard going grey", "young, with a nervous jaw",
    "a missing front tooth", "one milk-pale blind eye", "ruddy and barrel-chested",
    "lean, with quick darting eyes", "a long braid wound with wire", "a burn scar up the left forearm",
    "sallow, with deep-shadowed eyes", "a stained leather eyepatch", "freckled and snub-nosed",
    "weathered, with a sailor's squint", "close-cropped red hair", "a chipped, jutting jaw",
)
MANNER_TRAITS: tuple[str, ...] = (
    "talks too much to fill silence", "never finishes a sentence", "cracks knuckles before acting",
    "watches the exits, not you", "quick to anger, quicker to apologize", "speaks low and slow, deliberate",
    "laughs at the wrong moments", "flinches at sudden movement", "cocky to the point of carelessness",
    "weary and just wants this over", "pious, mutters small prayers", "greedy eyes, always pricing things",
    "loyal and protective of the others", "sceptical, expects to be lied to", "fidgets with a token or coin",
    "cold, economical, says little", "eager to impress whoever leads", "superstitious about the place",
)


def differentiate(names, *, seed: int = 0) -> list[dict]:
    labels = [n if isinstance(n, str) else getattr(n, "name", str(n)) for n in names]
    rng = random.Random(seed)
    looks = rng.sample(APPEARANCE_TRAITS, k=min(len(labels), len(APPEARANCE_TRAITS)))
    manners = rng.sample(MANNER_TRAITS, k=min(len(labels), len(MANNER_TRAITS)))
    out = []
    for i, name in enumerate(labels):
        out.append({"name": name,
                    "appearance": looks[i % len(looks)] if looks else "",
                    "manner": manners[i % len(manners)] if manners else ""})
    return out


def group_brief(names, *, role: str = "", seed: int = 0) -> str:
    rows = differentiate(names, seed=seed)
    if not rows:
        return ""
    head = (f"These {role} are individuals -- keep them distinct in the prose:"
            if role else "Keep these figures distinct in the prose:")
    body = [f"  \u2014 {r['name']}: {r['appearance']}; {r['manner']}." for r in rows]
    return head + "\n" + "\n".join(body)
