from __future__ import annotations

from dataclasses import dataclass

RARITY_ORDER = ("common", "uncommon", "rare", "very_rare", "legendary", "artifact")
CATEGORIES = ("weapon", "armor", "shield", "gear", "potion", "scroll",
              "wondrous", "ring", "rod", "staff", "wand", "ammunition", "tool")


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    category: str
    rarity: str
    value: int
    attunement: bool = False
    bonuses: tuple = ()
    effects: str = ""
    lore: str = ""
    special: str = ""
    regions: tuple = ()
    plot: bool = False
    requires_rule: str = ""
    slot: str = ""
    hands: int = 1
    armor_type: str = ""
    weapon_kind: str = ""
    finesse: bool = False
    ranged: bool = False
    weight: float = 0.0
    ac: int = 0
    dex_cap: int = 99
    str_req: int = 0
    grants: tuple = ()


def _i(key, name, cat, rar, val, **kw):
    return Item(key, name, cat, rar, val, **kw)


_ALL = [
    _i("dagger", "Dagger", "weapon", "common", 2, bonuses=("1d4 piercing", "finesse, light, thrown"),
       slot="main_hand", weapon_kind="simple", finesse=True, hands=1, weight=1,
       lore="A simple blade; every traveler carries one."),
    _i("longsword", "Longsword", "weapon", "common", 15, bonuses=("1d8 slashing", "versatile"),
       slot="main_hand", weapon_kind="martial", hands=1, weight=3,
       lore="The reliable arming sword of soldiers across the Realms."),
    _i("greataxe", "Greataxe", "weapon", "common", 30, bonuses=("1d12 slashing", "heavy, two-handed"),
       slot="main_hand", weapon_kind="martial", hands=2, weight=7,
       lore="A brutal woodsman's weapon favored by those who like a fight short."),
    _i("shortbow", "Shortbow", "weapon", "common", 25, bonuses=("1d6 piercing", "range 80/320"),
       slot="main_hand", weapon_kind="simple", hands=2, ranged=True, weight=2,
       lore="A hunter's bow, quiet and quick."),
    _i("leather_armor", "Leather Armor", "armor", "common", 10, bonuses=("AC 11 + DEX",),
       slot="armor", armor_type="light", ac=11, dex_cap=99, weight=10,
       lore="Boiled hide; light and quiet."),
    _i("chain_mail", "Chain Mail", "armor", "common", 75, bonuses=("AC 16", "STR 13, disadvantage on Stealth"),
       slot="armor", armor_type="heavy", ac=16, dex_cap=0, str_req=13, weight=55,
       lore="Interlocking rings over padding; a footman's protection."),
    _i("shield", "Shield", "shield", "common", 10, bonuses=("+2 AC",),
       slot="off_hand", armor_type="shield", ac=2, weight=6,
       lore="A band of wood and steel on the arm."),
    _i("hempen_rope", "Hempen Rope (50 ft)", "gear", "common", 1, lore="Fifty feet of stout rope."),
    _i("torch", "Torch", "gear", "common", 1, effects="Bright light 20 ft for an hour.",
       lore="Pitch and rag on a stick."),
    _i("rations", "Trail Rations (1 day)", "gear", "common", 1, lore="Jerky, hardtack, dried fruit."),
    _i("healers_kit", "Healer's Kit", "gear", "common", 5, effects="Ten uses; stabilize a dying creature without a check.",
       lore="Bandages, salves, and splints in a leather roll."),
    _i("thieves_tools", "Thieves' Tools", "tool", "common", 25, effects="Pick locks and disarm traps (with proficiency).",
       lore="Picks, a small file, and a mirror on a handle."),
    _i("spellbook", "Spellbook", "gear", "common", 50, lore="A hundred blank vellum pages awaiting a wizard's hand."),
    _i("holy_symbol", "Holy Symbol", "gear", "common", 5, lore="An emblem of a god, worn or held as a focus."),
    _i("lantern_hooded", "Hooded Lantern", "gear", "common", 5, effects="Bright light 30 ft; can be shuttered.",
       lore="Tin and glass; burns a pint of oil for hours."),

    _i("potion_of_healing", "Potion of Healing", "potion", "common", 50, effects="Regain 2d4+2 HP.",
       lore="A red draught that smells faintly of cloves."),
    _i("potion_of_greater_healing", "Potion of Greater Healing", "potion", "uncommon", 150,
       effects="Regain 4d4+4 HP.", lore="A deeper crimson, warm to the touch."),
    _i("antitoxin", "Antitoxin", "potion", "common", 50, effects="Advantage on saves vs poison for 1 hour.",
       lore="A bitter alchemical tincture."),
    _i("potion_of_climbing", "Potion of Climbing", "potion", "uncommon", 180,
       effects="A climbing speed and advantage to climb for 1 hour.", lore="It clings to the vial like syrup."),
    _i("alchemists_fire", "Alchemist's Fire", "gear", "common", 50, effects="Thrown; 1d4 fire each turn until smothered.",
       lore="A flask that ignites on contact with air."),
    _i("scroll_of_identify", "Scroll of Identify", "scroll", "common", 100, effects="Cast Identify once.",
       lore="A single spell inked for one use."),
    _i("scroll_of_fireball", "Scroll of Fireball", "scroll", "rare", 500, effects="Cast Fireball (3rd level) once.",
       lore="The runes are warm and faintly smell of smoke."),
    _i("scroll_of_revivify", "Scroll of Revivify", "scroll", "rare", 1000, effects="Cast Revivify once.",
       lore="Holy script that hums against the fingertips."),

    _i("plus_one_weapon", "+1 Weapon", "weapon", "uncommon", 500, bonuses=("+1 to attack and damage",),
       lore="Forge-marks glow faintly along a finely balanced blade."),
    _i("cloak_of_protection", "Cloak of Protection", "wondrous", "uncommon", 1000, attunement=True,
       bonuses=("+1 AC", "+1 to all saves"), lore="A traveler's cloak woven with a quiet ward."),
    _i("bag_of_holding", "Bag of Holding", "wondrous", "uncommon", 500,
       effects="Holds 500 lb in an extradimensional space.", lore="Heavier inside than out, and never full."),
    _i("boots_of_elvenkind", "Boots of Elvenkind", "wondrous", "uncommon", 500,
       effects="Advantage on Stealth to move quietly.", lore="Soft grey leather that makes no sound."),
    _i("wand_of_magic_missiles", "Wand of Magic Missiles", "wand", "uncommon", 500,
       effects="7 charges; cast Magic Missile.", lore="A slender rod of ash, three darts carved at the tip."),
    _i("driftglobe", "Driftglobe", "wondrous", "uncommon", 750, effects="A floating globe of light you command.",
       lore="A glass sphere that wakes to your word and follows at a hover."),
    _i("eyes_of_the_eagle", "Eyes of the Eagle", "wondrous", "uncommon", 500, attunement=True,
       effects="Advantage on sight-based Perception.", lore="Crystal lenses that bring the far near."),

    _i("plus_one_armor", "+1 Armor", "armor", "rare", 1500, bonuses=("+1 AC",),
       lore="The plates carry a smith's sigil that never tarnishes."),
    _i("ring_of_protection", "Ring of Protection", "ring", "rare", 3500, attunement=True,
       bonuses=("+1 AC", "+1 to all saves"), lore="A plain band that turns aside what would harm you."),
    _i("flame_tongue", "Flame Tongue", "weapon", "rare", 5000, attunement=True,
       bonuses=("+2d6 fire on a hit",), effects="A command word sheathes the blade in flame.",
       lore="Speak the word and fire runs the length of the steel, throwing dancing light; the blade "
            "remembers every battle it has lit.", regions=("baldurs_gate", "waterdeep")),
    _i("cloak_of_displacement", "Cloak of Displacement", "wondrous", "rare", 6000, attunement=True,
       effects="Attackers have disadvantage until you're hit.",
       lore="You stand a half-step from where you seem; the eye slides off you."),
    _i("boots_of_speed", "Boots of Speed", "wondrous", "rare", 4000, attunement=True,
       effects="Double your speed; attackers have disadvantage (10 min/rest).",
       lore="Heels that spark blue when you run."),
    _i("wand_of_fireballs", "Wand of Fireballs", "wand", "rare", 5000, attunement=True,
       effects="7 charges; cast Fireball.", lore="Blackened at the tip, and warm even unused."),
    _i("drow_blade", "Drow Long Knife", "weapon", "rare", 2500, attunement=True,
       bonuses=("+1, but its magic fades in sunlight",), lore="Cruel dark-elven steel, etched with spider-silk patterns.",
       regions=("underdark",)),

    _i("staff_of_fire", "Staff of Fire", "staff", "very_rare", 25000, attunement=True,
       effects="10 charges; Burning Hands, Wall of Fire, Fireball; resist fire.",
       lore="Charred oak shot through with veins of ember that pulse when you grip it."),
    _i("dancing_sword", "Dancing Sword", "weapon", "very_rare", 24000, attunement=True,
       effects="Toss it to fight on its own for a few rounds.",
       lore="It leaves your hand and hangs in the air, point weaving, waiting for a foe."),
    _i("plus_two_weapon", "+2 Weapon", "weapon", "very_rare", 8000, bonuses=("+2 to attack and damage",),
       lore="A masterwork blade humming with contained force."),

    _i("holy_avenger", "Holy Avenger", "weapon", "legendary", 75000, attunement=True,
       bonuses=("+3 to attack and damage", "+2d10 radiant vs fiends and undead"),
       effects="In a paladin's hand it sheds an aura of protection.",
       lore="A sword of the great cause, blessed at a god's own altar; in unworthy hands it is only "
            "fine steel, but borne by the pure it blazes like a fragment of the dawn.",
       regions=("waterdeep",)),
    _i("staff_of_power", "Staff of Power", "staff", "legendary", 95000, attunement=True,
       effects="20 charges of mighty spells; +2 to attack, AC, and saves while held.",
       lore="An archmage's staff, capped with a clear gem that holds a caged star; it can be broken "
            "in extremity to loose all its power at once."),

    _i("dawnshard", "The Dawnshard", "wondrous", "uncommon", 0, plot=True,
       special="A god's relic hiding behind a humble rarity -- a splinter of a slain deity of light.",
       lore="It looks like a dull shard of amber on a thong, worth a few coins to any honest "
            "appraiser. It is nothing of the kind. Within sleeps a mote of a dead god of dawn, and "
            "those who would wake it -- or end it forever -- have already begun to move.",
       regions=()),
    _i("whisperfang", "Whisperfang", "weapon", "rare", 0, attunement=True, plot=True,
       special="Alive, talking, and malevolent; it whispers to whoever holds it.",
       bonuses=("+1, +2d6 necrotic when it 'feeds'",),
       lore="A thin black blade with a voice like silk over a knife. It flatters, it bargains, it "
            "lies -- and it is patient. It has worn a dozen wielders, and remembers each of their ends."),
    _i("crown_of_the_lost_king", "Crown of the Lost King", "wondrous", "legendary", 0, attunement=True,
       plot=True, special="Cursed: it binds the wearer's fate to a kingdom that died screaming.",
       lore="A circlet of tarnished gold and grief. Wear it and the dead realm's last king wakes "
            "behind your eyes, and will not easily be put back to sleep."),
    _i("sealed_codex", "The Sealed Codex", "gear", "rare", 0, plot=True,
       special="Contains a sealed pact three factions would kill to read -- or to burn.",
       lore="Bound in skin that isn't, clasped with a lock no key fits. Whatever bargain it records "
            "has outlived everyone who signed it, and they are not all resting quietly."),
]

try:
    from rulesets.dnd.additional.items_oota import OOTA_ITEMS as _OOTA
except ImportError:
    _OOTA = ()

_ALL = list(_ALL) + list(_OOTA)
ITEMS = {it.key: it for it in _ALL}


def register(items) -> None:
    for it in items:
        if it.key in ITEMS:
            _ALL[:] = [x for x in _ALL if x.key != it.key]
        _ALL.append(it)
        ITEMS[it.key] = it


def get(key: str) -> Item | None:
    return ITEMS.get((key or "").lower())


def _available(it: Item, rules) -> bool:
    return not it.requires_rule or (rules is not None and it.requires_rule in rules)


def all_items(rules=None) -> list:
    return list(_ALL) if rules is None else [it for it in _ALL if _available(it, rules)]


def tradeable(rules=()) -> list:
    return [it for it in _ALL if not it.plot and _available(it, rules)]


def by_category(category: str) -> list:
    return [it for it in _ALL if it.category == category]


STARTING_KITS = {
    "barbarian": ("greataxe", "leather_armor", "rations", "torch"),
    "bard": ("longsword", "leather_armor", "healers_kit", "rations"),
    "cleric": ("longsword", "chain_mail", "shield", "holy_symbol", "potion_of_healing"),
    "druid": ("dagger", "leather_armor", "healers_kit", "rations"),
    "fighter": ("longsword", "shield", "chain_mail", "potion_of_healing"),
    "monk": ("dagger", "rations", "torch"),
    "paladin": ("longsword", "shield", "chain_mail", "holy_symbol", "potion_of_healing"),
    "ranger": ("shortbow", "leather_armor", "dagger", "rations"),
    "rogue": ("dagger", "leather_armor", "thieves_tools", "potion_of_healing"),
    "sorcerer": ("dagger", "torch", "rations"),
    "warlock": ("dagger", "leather_armor", "torch"),
    "wizard": ("dagger", "spellbook", "torch", "scroll_of_identify"),
}


def starting_kit(class_key: str) -> list:
    return list(STARTING_KITS.get((class_key or "").lower(), ("dagger", "rations", "torch")))


def by_rarity(rarity: str) -> list:
    return [it for it in _ALL if it.rarity == rarity]


def in_region(region: str) -> list:
    r = (region or "").lower()
    return [it for it in _ALL if not it.regions or r in it.regions]
