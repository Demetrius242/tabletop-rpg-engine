# Settings (the world a campaign happens in)

Ruleset-dependent world data the narrator and GM read to keep a campaign consistent. A `Setting`
bundles:

- **tone / narration angle** -- a short label plus a paragraph that tells the narrator how the
  world should *feel* (heroic high fantasy reads very differently from dark fantasy). This is
  prepended to the narrator's system prompt as a **world briefing**, the same way a character's
  roleplay seed shapes their voice.
- **world concepts** -- the gods, factions, and forces that matter (one or two lines each).
- **sights** -- famous landmarks, for flavor and reference.
- **locations** -- reusable scene templates (`a night street`, `a dark forest`, `a lonely tower`,
  a roadhouse, a harbor at dusk, a haunted ruin), each with a description, a mood cue, and hooks.
- **NPC cards** -- named characters with a role, description, demeanor, a voice cue for the
  narrator, a GM-only secret, and an adventure hook.

## What's here
- `base.py` -- the `Setting`, `Location`, `NPCCard`, and `WorldConcept` structures, plus
  `Setting.narration_brief()` (the world briefing) and location/NPC lookups.
- `forgotten_realms.py` -- the first concrete setting: **The Forgotten Realms (Sword Coast)**,
  around Waterdeep and Baldur's Gate. Heroic high fantasy with frontier grit; the Weave and the
  gods, the factions (Harpers, Zhentarim, Lords' Alliance, Emerald Enclave, Order of the Gauntlet),
  seven reusable locations, and six original NPC cards (an innkeeper, a Harper contact, a Zhentarim
  fixer, a priest of Tymora, a dock-ward fence, a Watch sergeant).

## How the ruleset uses it
The ruleset loads `SETTINGS` and activates `DEFAULT` (Forgotten Realms). `current_setting()`,
`use_setting(key)`, `location(key)`, `npc(key)`, `list_locations()`, `list_npcs()`, and
`world_brief()` expose it; `narrator_briefing(pc)` composes the active world brief with the
character brief so the narrator is grounded in both. `use_setting(None-equivalent)` (clearing
`self.setting`) leaves prose un-briefed, so the engine stays system-agnostic.

## Honest scope
The world concepts reference the canonical published setting in brief, original prose (flavor and
facts, not sourcebook text); the NPC cards are original characters. Locations are *templates* for
the GM/narrator -- there's no scene runner wiring them into play automatically yet, and NPC cards
are reference data rather than spawned combatants. Adding a setting is a new file plus a registry
line; adding a location or NPC is a one-liner.

## Tradesmen (in the Forgotten Realms package)

`forgotten_realms/tradesmen.py` holds thirteen merchants spread across the Sword Coast, scaling
with where and who they are: village herb-wives and roadside tinkers (cheap common consumables),
city dealers (broad uncommon stock, the odd rare piece), and elite specialists in dangerous places
(small, restricted, rare-or-better assortments). The more singular the wares, the more singular the
person -- an old herb-wife in a village, a charismatic tiefling dealer in Waterdeep, a fey lady in
the High Forest, a drow trade-mistress in the Underdark, a reclusive archmage on the moors, and a
cambion collector beneath Baldur's Gate. Each `Tradesman` sets the shop's region, allowed
categories, rarity floor/ceiling, size, markup/buy-back, restock interval, and rarity bias, and
carries an `NPCCard`. The ruleset generates their stock at game start and restocks it as long rests
pass (see additional/README.md and trade.py); plot items never appear.
