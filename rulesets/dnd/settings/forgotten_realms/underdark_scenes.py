from __future__ import annotations

from engine.scene import Feature, Presence, Scene, SceneZone


def _drow(name, hp=16, ac=15):
    def _make(make_enemy):
        return make_enemy(name, hp=hp, ac=ac, attack=("shortsword", 4, "1d6+2"),
                          creature_type="humanoid", alignment="ne", gender="female")
    return _make


def velkynvelve(make_enemy):
    handler = make_enemy("Drow Slave Handler", hp=32, ac=15, attack=("whip", 4, "1d4+2"),
                         alignment="le", gender="male")
    quaggoth = make_enemy("Quaggoth Thonot", hp=45, ac=13, attack=("claws", 5, "2d6+3"),
                          creature_type="monstrosity", mindless=False, gender="male")

    return Scene(
        key="velkynvelve", name="Velkynvelve", kind="dungeon",
        zones={
            "slave_pens": SceneZone("slave_pens", "The Slave Pens",
                                    "Iron cages tiered along a wet cavern wall; fungus stew steams in a trough.",
                                    adjacent=("rope_bridge", "quaggoth_pit"), cover="light",
                                    mood="miserable and watched"),
            "rope_bridge": SceneZone("rope_bridge", "The Rope Bridge",
                                     "Spider-silk ropes over a chasm; far below, something glitters.",
                                     adjacent=("slave_pens", "priestess_platform"), hazard="the chasm"),
            "priestess_platform": SceneZone("priestess_platform", "Ilvara's Platform",
                                            "A carved ledge with a stone altar and silk banners.",
                                            adjacent=("rope_bridge",), cover="heavy", mood="cruel and holy"),
            "quaggoth_pit": SceneZone("quaggoth_pit", "The Quaggoth Pit",
                                      "A reeking lower pit where brutes are kept hungry.",
                                      adjacent=("slave_pens",), cover="none", mood="bestial"),
        },
        features={
            "loose_chain": Feature("loose_chain", "a loose chain link", "slave_pens",
                                   interactions=("search",), hidden=True, notice="moderate",
                                   note="Could weaken a cage with effort and time."),
            "stew_pot": Feature("stew_pot", "the fungus stew pot", "slave_pens",
                                interactions=("search",), contents=("cave_moss_rations",),
                                description="Grey slop that keeps slaves walking."),
            "guard_locker": Feature("guard_locker", "a guard locker", "rope_bridge",
                                    interactions=("search", "take"), contents=("drow_poison_vial", "potion_of_healing"),
                                    locked=True, notice="easy"),
            "holy_chest": Feature("holy_chest", "Ilvara's reliquary chest", "priestess_platform",
                                  interactions=("search", "take"), contents=("spider_staff", "scroll_of_revivify"),
                                  locked=True, notice="hard", description="Spider sigils and a lock of bone."),
            "pit_grate": Feature("pit_grate", "a rusted pit grate", "quaggoth_pit",
                                 interactions=("search",), note="Weak enough to bend; noise will draw guards."),
        },
        presences={
            "jimjar": Presence("jimjar", "Jimjar the svirfneblin", "slave_pens", kind="npc",
                               disposition="friendly",
                               note="Whispers odds on escape and offers to pick a lock."),
            "eldeth": Presence("eldeth", "Eldeth Feldrun", "slave_pens", kind="npc", disposition="friendly",
                               note="Ready to fight if given a weapon."),
            "handler": Presence("handler", "a drow slave handler", "rope_bridge", kind="enemy",
                                disposition="hostile", awareness="alert", combatant=handler),
            "guard_a": Presence("guard_a", "a drow guard", "rope_bridge", kind="enemy",
                                disposition="hostile", awareness="unaware",
                                combatant=make_enemy("Drow Guard", hp=16, ac=15, alignment="ne", gender="female")),
            "guard_b": Presence("guard_b", "a drow guard", "priestess_platform", kind="enemy",
                                disposition="hostile", awareness="unaware",
                                combatant=make_enemy("Drow Guard", hp=16, ac=15, alignment="ne", gender="female")),
            "ilvara": Presence("ilvara", "Ilvara Mizzrym", "priestess_platform", kind="enemy",
                               disposition="hostile", hidden=False, awareness="alert",
                               combatant=make_enemy("Ilvara Mizzrym", hp=71, ac=16, attack=("scourge", 5, "1d8+2"),
                                                    alignment="ne", gender="female", intelligence=14)),
            "quaggoth": Presence("quaggoth", "a quaggoth thonot", "quaggoth_pit", kind="enemy",
                                 disposition="hostile", awareness="unaware", combatant=quaggoth),
        },
        pc_zone="slave_pens",
        hooks=("the chasm wind carries prayers and screams", "a patrol crosses the bridge on schedule",
               "Stool's myconid spores calm the guards -- briefly"),
    )


def gracklstugh_gate(make_enemy):
    return Scene(
        key="gracklstugh_gate", name="Gracklstugh Gate", kind="dungeon",
        zones={
            "outer_gate": SceneZone("outer_gate", "The Outer Gate",
                                    "Soot-black stone arch; duergar spears catch forge-light.",
                                    adjacent=("foundry_lane",), is_exit=True, mood="industrial menace"),
            "foundry_lane": SceneZone("foundry_lane", "Foundry Lane",
                                      "Hammerfall and slave carts; heat shimmers on the air.",
                                      adjacent=("outer_gate", "market_stall"), cover="light"),
            "market_stall": SceneZone("market_stall", "Y's Market Stall",
                                      "A svirfneblin cart of salvage, rope, and suspicious tonics.",
                                      adjacent=("foundry_lane",), mood="wary commerce"),
        },
        features={
            "writ_posting": Feature("writ_posting", "a writ posting board", "outer_gate",
                                    interactions=("search",), contents=("gracklstugh_pass",),
                                    description="Official seals and threats in Undercommon."),
            "tax_chest": Feature("tax_chest", "a tax chest", "foundry_lane",
                                 interactions=("search", "take"), contents=("adamantine_chain",),
                                 locked=True, notice="moderate"),
            "y_cart": Feature("y_cart", "Y's trading cart", "market_stall",
                              interactions=("search",), contents=("goggles_of_night",),
                              description="Salvage priced for the desperate."),
        },
        presences={
            "y": Presence("y", "Y the deep gnome trader", "market_stall", kind="npc", disposition="neutral",
                          note="Sells gear; knows who asks too many questions."),
            "duergar_a": Presence("duergar_a", "a duergar guard", "outer_gate", kind="enemy",
                                  disposition="hostile", awareness="alert",
                                  combatant=make_enemy("Duergar Guard", hp=26, ac=16, attack=("war pick", 4, "1d8+2"),
                                                       alignment="le", gender="male")),
            "duergar_b": Presence("duergar_b", "a duergar guard", "foundry_lane", kind="enemy",
                                  disposition="hostile", awareness="unaware",
                                  combatant=make_enemy("Duergar Guard", hp=26, ac=16, alignment="le", gender="male")),
            "slaver": Presence("slaver", "a duergar slaver", "foundry_lane", kind="enemy",
                              disposition="hostile", awareness="unaware",
                              combatant=make_enemy("Duergar Slaver", hp=30, ac=15, attack=("whip", 4, "1d4+2"),
                                                   alignment="le")),
        },
        pc_zone="outer_gate",
        hooks=("the Deepking's tax must be paid", "forge smoke hides movement",
               "a writ of passage opens the inner city"),
    )


def sloobludop_shore(make_enemy):
    return Scene(
        key="sloobludop_shore", name="Sloobludop Shore", kind="dungeon",
        zones={
            "mud_dock": SceneZone("mud_dock", "The Mud Dock",
                                  "Fish-gut planks and slime; skiffs bob on black water.",
                                  adjacent=("idol_plaza",), is_exit=True, mood="humid madness"),
            "idol_plaza": SceneZone("idol_plaza", "The Plaza of New Gods",
                                     "Fresh idols painted each dawn; incense of rot and devotion.",
                                     adjacent=("mud_dock", "shrine_pool"), cover="light"),
            "shrine_pool": SceneZone("shrine_pool", "The Shrine Pool",
                                     "Waist-deep water lit by glowing fungi; something watches from below.",
                                     adjacent=("idol_plaza",), mood="reverent and wrong"),
        },
        features={
            "skiff": Feature("skiff", "a kuo-toa skiff", "mud_dock",
                             interactions=("search",), description="Paddles missing; Shuushar might help."),
            "fresh_idol": Feature("fresh_idol", "a wet clay idol", "idol_plaza",
                                  interactions=("search",), note="The face resembles a party member today."),
            "offering_bowl": Feature("offering_bowl", "an offering bowl", "shrine_pool",
                                     interactions=("take",), contents=("slippery_mind_fish_oil", "helm_of_underwater_action"),
                                     description="Fish and silver and stranger things."),
        },
        presences={
            "shuushar": Presence("shuushar", "Shuushar the Awakened", "mud_dock", kind="npc",
                                 disposition="friendly", note="Offers to paddle; counsels calm."),
            "blurg": Presence("blurg", "Blurg the orog", "mud_dock", kind="npc", disposition="neutral",
                              note="For hire as muscle; likes stew."),
            "whip": Presence("whip", "a kuo-toa whip", "idol_plaza", kind="enemy",
                             disposition="hostile", awareness="alert",
                             combatant=make_enemy("Kuo-toa Whip", hp=33, ac=11, attack=("mace", 4, "1d6+2"),
                                                  creature_type="humanoid", alignment="ce")),
            "priest": Presence("priest", "a kuo-toa archpriest", "shrine_pool", kind="enemy",
                               disposition="hostile", hidden=True, notice="hard",
                               combatant=make_enemy("Kuo-toa Archpriest", hp=97, ac=13, attack=("mace", 6, "1d6+3"),
                                                    alignment="ce", intelligence=12)),
        },
        pc_zone="mud_dock",
        hooks=("a prophet names a new god", "the Darklake route to Gracklstugh",
               "Bloppblippolp's idol 'weeps' before storms"),
    )


SCENES = {
    "velkynvelve": velkynvelve,
    "gracklstugh_gate": gracklstugh_gate,
    "sloobludop_shore": sloobludop_shore,
}


def build(key: str, make_enemy):
    factory = SCENES.get((key or "").lower())
    return factory(make_enemy) if factory else None


def list_scenes() -> list:
    return list(SCENES.keys())
