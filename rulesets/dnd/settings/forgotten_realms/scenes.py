from __future__ import annotations

from engine.scene import Feature, Presence, Scene, SceneZone


def watchers_barrow(make_enemy):
    def cultist(name, hp=11):
        return make_enemy(name, hp=hp, ac=12, alignment="le")

    return Scene(
        key="watchers_barrow", name="The Watcher's Barrow", kind="dungeon",
        zones={
            "entrance": SceneZone("entrance", "The Barrow Mouth",
                                  "A low stone doorway in a grassy mound, cold air sighing out.",
                                  adjacent=("antechamber",), is_exit=True, mood="hushed, watchful"),
            "antechamber": SceneZone("antechamber", "The Antechamber",
                                     "A round room of cracked flagstones; old murals peel from the walls.",
                                     adjacent=("entrance", "gallery"), cover="light"),
            "gallery": SceneZone("gallery", "The Offering Gallery",
                                 "A long hall lined with burial niches, candle-stubs guttering.",
                                 adjacent=("antechamber", "deep_chamber"), mood="reverent and wrong"),
            "deep_chamber": SceneZone("deep_chamber", "The Deep Chamber",
                                      "A vaulted tomb around a black sarcophagus, the air thick with power.",
                                      adjacent=("gallery",), cover="heavy", mood="dread"),
        },
        features={
            "cairn": Feature("cairn", "a disturbed cairn", "antechamber",
                             interactions=("search",), contents=("potion_of_healing",),
                             description="A heap of stones someone has already pawed through."),
            "tripwire": Feature("tripwire", "a near-invisible tripwire", "antechamber",
                                hidden=True, notice="moderate",
                                note="Strung to a rockfall; springs the gallery's alarm if missed."),
            "reliquary": Feature("reliquary", "a pried-open reliquary", "gallery",
                                 interactions=("search", "take"), contents=("scroll_of_revivify", "antitoxin"),
                                 description="A stone box, its gold prised half away."),
            "sealed_door": Feature("sealed_door", "a rune-sealed door", "gallery",
                                   locked=True, gates="deep_chamber",
                                   description="Cold iron scored with binding runes; it does not want to open."),
            "sarcophagus": Feature("sarcophagus", "the black sarcophagus", "deep_chamber",
                                   interactions=("search",), contents=("ring_of_protection",),
                                   hidden=False, description="Lidless, and far too cold."),
        },
        presences={
            "acolyte": Presence("acolyte", "a wounded acolyte", "entrance", kind="npc",
                                disposition="friendly",
                                note="Fled the cult; will warn the party what waits below if helped."),
            "cultist_a": Presence("cultist_a", "a hooded cultist", "antechamber", kind="enemy",
                                  disposition="hostile", awareness="unaware", combatant=cultist("Hooded Cultist")),
            "cultist_b": Presence("cultist_b", "a chanting cultist", "gallery", kind="enemy",
                                  disposition="hostile", awareness="unaware", combatant=cultist("Chanting Cultist")),
            "cultist_c": Presence("cultist_c", "a chanting cultist", "gallery", kind="enemy",
                                  disposition="hostile", awareness="unaware", combatant=cultist("Chanting Cultist")),
            "leader": Presence("leader", "the Barrow-Warden", "deep_chamber", kind="enemy",
                               disposition="hostile", hidden=True, notice="hard",
                               combatant=make_enemy("The Barrow-Warden", hp=30, ac=14, alignment="le"),
                               note="A cult leader mid-ritual; sealed away until the door is opened or it is sensed."),
        },
        pc_zone="entrance",
        hooks=("the acolyte begs you to stop the ritual", "the chanting rises as you go deeper",
               "the sealed door's runes hum when touched"),
    )


from rulesets.dnd.settings.forgotten_realms.underdark_scenes import SCENES as _UNDERDARK_SCENES

SCENES = {"watchers_barrow": watchers_barrow, **_UNDERDARK_SCENES}


def build(key: str, make_enemy):
    factory = SCENES.get((key or "").lower())
    return factory(make_enemy) if factory else None


def list_scenes() -> list:
    return list(SCENES.keys())
