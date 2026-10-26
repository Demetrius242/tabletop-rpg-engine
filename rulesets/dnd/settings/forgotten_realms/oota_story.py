from __future__ import annotations

from engine.story import (Adventure, NpcPhase, NpcTask, Outcome, StoryEvent, Task, Transition)


def build_oota_ch1() -> Adventure:
    velkynvelve = StoryEvent(
        key="velkynvelve_escape", title="Prisoners of Velkynvelve", scene_key="velkynvelve",
        intro_cue=("You come awake in a cage of iron and stone, the drow outpost of Velkynvelve "
                   "humming around you. Your gear is piled on a guard's table; a chasm wind moans "
                   "through the spider-silk bridges. This is the moment -- while the priestess is "
                   "at her prayers, before the next patrol."),
        tasks=(
            Task(key="free_allies", summary="Free the other prisoners from the slave pens.",
                 outcomes=(
                     Outcome("full",
                             when={"all": [{"at": "slave_pens"}, {"any": [
                                 {"check": "sleight_of_hand", "band_at_least": "success"},
                                 {"check": "athletics", "band_at_least": "success"}]}]},
                             effects=({"set_disposition": "eldeth", "to": "friendly"},
                                      {"set_disposition": "jimjar", "to": "friendly"},
                                      {"set_flag": "allies_freed", "value": True},
                                      {"cue": "The cage gives with a grudging clank. Eldeth Feldrun "
                                              "and Jimjar slip free, already reaching for anything "
                                              "that can cut drow throats."}),
                             summary="Eldeth and Jimjar are freed, cleanly."),
                     Outcome("partial",
                             when={"all": [{"at": "slave_pens"}, {"any": [
                                 {"check": "sleight_of_hand", "band_at_least": "marginal"},
                                 {"check": "athletics", "band_at_least": "marginal"}]}]},
                             effects=({"set_disposition": "eldeth", "to": "friendly"},
                                      {"set_disposition": "jimjar", "to": "friendly"},
                                      {"set_flag": "allies_freed", "value": True},
                                      {"raise_alarm": "suspicious"},
                                      {"cue": "The lock scrapes open -- but a guard's head turns at "
                                              "the sound. You're free, and nearly caught."}),
                             summary="Freed, but the noise drew a guard's eye."),
                     Outcome("fail",
                             when={"any": [{"check": "sleight_of_hand", "band_is": "botch"},
                                           {"check": "athletics", "band_is": "botch"}]},
                             effects=({"raise_alarm": "alert"},
                                      {"cue": "Metal snaps and clatters down the chasm; a whistle "
                                              "shrills across the pens. So much for quiet."}),
                             summary="Botched -- the alarm goes up."),
                 )),
            Task(key="reach_bridge", summary="Slip across the rope bridge toward the way out.",
                 outcomes=(
                     Outcome("full", when={"at": "rope_bridge"},
                             effects=({"set_flag": "at_bridge", "value": True},),
                             summary="You reach the spider-silk bridge over the chasm."),
                 )),
        ),
        npc_tasks=(
            NpcTask(key="ilvara_ritual", npc="ilvara", cadence="combat_round",
                    summary="Ilvara completes a spider-prayer to Lolth.",
                    start_when={"in_scene": "velkynvelve"},
                    abort_when={"any": [{"defeated": "ilvara"}, {"flag": "allies_freed"}]},
                    phases=(
                        NpcPhase("gather", "Ilvara lifts her scourge and begins to pray.", skill="",
                                 cue="On the platform, Ilvara raises her scourge and starts a low, "
                                     "droning prayer to the Spider Queen."),
                        NpcPhase("channel", "Webs gather in the dark.", skill="religion",
                                 difficulty="medium", advance_on="success",
                                 cue="The shadows above the altar thicken and skitter with unseen legs."),
                        NpcPhase("call", "A servitor answers.", skill="religion", difficulty="hard",
                                 advance_on="success",
                                 cue="Something vast shifts just past the torchlight, answering her call."),
                    ),
                    on_complete=({"place": "quaggoth", "zone": "priestess_platform"},
                                 {"raise_alarm": "alert"},
                                 {"cue": "Ilvara's prayer is answered -- a hulking servitor stirs "
                                         "from the pit and turns its blind hunger toward you."})),
        ),
        transitions=(
            Transition(when={"any": [{"all": [{"flag": "allies_freed"}, {"at": "rope_bridge"}]},
                                     {"victor": "party"}]},
                       to="underdark_flight"),
        ),
    )

    flight = StoryEvent(
        key="underdark_flight", title="Flight in the Dark", scene_key="",
        intro_cue=("You plunge into the black tunnels, the outpost's horns fading behind you. The "
                   "Underdark swallows sound and light alike. Two ways call from the dark: the damp "
                   "reek of an underground lake, or a distant red glow of forges."),
        tags=(("toward_lake", "heading for water, an underground lake, the Darklake, kuo-toa, a "
               "boat or the shore",
               ("lake", "water", "darklake", "boat", "skiff", "shore", "kuo", "dock", "fish")),
              ("toward_forge", "heading toward the duergar city, forges, smoke, heat, or a gate",
               ("forge", "smoke", "gracklstugh", "duergar", "gate", "city", "heat", "foundry", "red"))),
        tasks=(
            Task(key="choose_route", summary="Choose which way to flee through the Underdark.",
                 outcomes=(
                     Outcome("lake", when={"tag": "toward_lake"},
                             effects=({"set_flag": "route", "value": "lake"},
                                      {"goto": "sloobludop_arrival"}),
                             summary="Toward the Darklake and Sloobludop."),
                     Outcome("forge", when={"tag": "toward_forge"},
                             effects=({"set_flag": "route", "value": "forge"},
                                      {"goto": "gracklstugh_arrival"}),
                             summary="Toward the forges of Gracklstugh."),
                 )),
        ),
        npc_tasks=(
            NpcTask(key="pursuit", npc="ilvara", cadence="long_rest",
                    summary="Ilvara's hunters close on your trail.",
                    start_when=True,
                    abort_when={"any": [{"in_scene": "sloobludop_shore"},
                                        {"in_scene": "gracklstugh_gate"}]},
                    phases=(
                        NpcPhase("track", "Trackers pick up the scent.", skill="",
                                 cue="Far back down the tunnel, torches bob into view."),
                        NpcPhase("gain", "They gain ground while you rest.", skill="",
                                 cue="You've lingered too long; the hunt is closer when you wake."),
                    ),
                    on_complete=({"set_flag": "hunted", "value": True},
                                 {"cue": "Drow voices echo close now -- you cannot rest again "
                                         "until you reach somewhere with walls."})),
        ),
    )

    sloobludop = StoryEvent(
        key="sloobludop_arrival", title="The Mad Prophets of Sloobludop", scene_key="sloobludop_shore",
        intro_cue=("The tunnel opens onto a slimed shore of the Darklake. Kuo-toa chant to gods they "
                   "invent each dawn; skiffs bob on the black water. Shuushar the Awakened watches "
                   "you with unsettling calm."),
        tasks=(
            Task(key="treat_with_kuotoa", summary="Win passage or peace from the kuo-toa.",
                 outcomes=(
                     Outcome("full", when={"check": "persuasion", "band_at_least": "success"},
                             effects=({"set_flag": "kuo_allied", "value": True},
                                      {"cue": "Shuushar inclines his head; the whip lowers its mace. "
                                              "You have a skiff, and a fragile welcome."}),
                             summary="The kuo-toa grant you passage."),
                     Outcome("partial", when={"visited": "idol_plaza"},
                             effects=({"cue": "You reach the plaza of new gods -- watched, wary, "
                                              "but not yet attacked."},),
                             summary="You reach the prophets, tension high."),
                     Outcome("fail", when={"alarm": "alert"},
                             effects=({"cue": "A prophet shrieks that you are false gods; the shore "
                                              "erupts in webbed fury."},),
                             summary="The village turns on you."),
                 )),
        ),
        transitions=(
            Transition(when={"all": [{"task": "treat_with_kuotoa", "state": "done"}, {"at": "mud_dock"}]},
                       to="ch1_end"),
        ),
    )

    gracklstugh = StoryEvent(
        key="gracklstugh_arrival", title="The Gate of Gracklstugh", scene_key="gracklstugh_gate",
        intro_cue=("Forge-glow and hammerfall: the duergar city of Gracklstugh. Grey dwarves eye "
                   "you from a soot-black gate. Papers, a bribe, or blood will get you through."),
        tasks=(
            Task(key="pass_the_gate", summary="Get past the duergar gate into the city.",
                 outcomes=(
                     Outcome("full", when={"has_item": "gracklstugh_pass"},
                             effects=({"set_flag": "passed_gate", "value": True},
                                      {"cue": "You present the writ of passage; the guards wave you "
                                              "through with a grunt."}),
                             summary="A writ of passage opens the gate."),
                     Outcome("partial", when={"any": [
                         {"check": "deception", "band_at_least": "success"},
                         {"check": "persuasion", "band_at_least": "success"}]},
                             effects=({"set_flag": "passed_gate", "value": True},
                                      {"cue": "A confident lie and a hard stare; the duergar decide "
                                              "you're more trouble to stop than to admit."}),
                             summary="You talk your way past the gate."),
                     Outcome("fail", when={"alarm": "alert"},
                             effects=({"cue": "A guard bellows the alarm; war picks come up all "
                                              "along the gate."},),
                             summary="The gate turns hostile."),
                 )),
        ),
        transitions=(
            Transition(when={"all": [{"task": "pass_the_gate", "state": "done"}, {"at": "foundry_lane"}]},
                       to="ch1_end"),
        ),
    )

    end = StoryEvent(
        key="ch1_end", title="Deeper Still", scene_key="",
        intro_cue=("Behind you, Velkynvelve is a fading nightmare; ahead, the Underdark stretches on "
                   "without end. You have survived the first night of your escape -- but the demon "
                   "lords are stirring, and the dark is only getting deeper. (End of Chapter 1.)"),
        entry_effects=({"set_flag": "oota_ch1_complete", "value": True},),
    )

    events = {e.key: e for e in (velkynvelve, flight, sloobludop, gracklstugh, end)}
    return Adventure(
        key="oota_ch1", title="Out of the Abyss -- Escape from Velkynvelve",
        start_event="velkynvelve_escape", events=events,
        party=({"pregen": "sarit"}, {"pregen": "ront"}, {"pregen": "pog"}),
        metadata={"blurb": ("Break the drow slave pens of Velkynvelve, flee into the Underdark, and "
                            "reach Sloobludop or Gracklstugh. Party: Sarith (ranger), Ront, Pog."),
                  "tone": "dark survival in the Underdark",
                  "description": (
                      "A vertical slice of the classic Underdark campaign. You wake a prisoner in "
                      "the drow outpost of Velkynvelve and must seize the one chance to run: free "
                      "your fellow captives, cross the spider-silk bridge over the chasm, and vanish "
                      "into the lightless tunnels before the priestess Ilvara finishes her prayer to "
                      "Lolth. Beyond lies a fork -- the kuo-toa shore of Sloobludop or the forge-city "
                      "gate of Gracklstugh -- each a different way to survive the first night."),
                  "chapters": [
                      {"n": 1, "title": "Prisoners", "implemented": True},
                      {"n": 2, "title": "Into Darkness", "implemented": False},
                      {"n": 3, "title": "The Darklake", "implemented": False},
                      {"n": 4, "title": "Gracklstugh", "implemented": False},
                      {"n": 5, "title": "Neverlight Grove", "implemented": False},
                      {"n": 6, "title": "Blingdenstone", "implemented": False},
                      {"n": 7, "title": "Escape from the Underdark", "implemented": False},
                      {"n": 8, "title": "Audience in Gauntlgrym", "implemented": False},
                      {"n": 9, "title": "Mantol-Derith", "implemented": False},
                      {"n": 10, "title": "Descent into the Depths", "implemented": False},
                      {"n": 11, "title": "Gravenhollow", "implemented": False},
                      {"n": 12, "title": "The Wormwrithings", "implemented": False},
                      {"n": 13, "title": "The Labyrinth", "implemented": False},
                      {"n": 14, "title": "The City of Spiders", "implemented": False},
                      {"n": 15, "title": "The Fetid Wedding", "implemented": False},
                      {"n": 16, "title": "The Vast Oblivium", "implemented": False},
                      {"n": 17, "title": "Against the Demon Lords", "implemented": False},
                  ]})
