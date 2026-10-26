# D&D additional rules

The layer that turns the core d20 system into a recognizable D&D character builder. The core
ruleset folds all of this in automatically when this package is importable (and falls back to a
minimal built-in roster if it's removed).

## What's here
- **alignment.py** — the nine alignments on the Law x Morality grid, modeled like Vampire's
  **Nature & Demeanor**: a character has a *true* alignment and a *presented* one (their mask),
  defaulting to the same. Like Demeanor, it's a roleplay/narration descriptor with no dice;
  `profile(true, presented)` returns the pair and a `narration_note()` for the AI.
- **races.py** — nine races (`human, elf, dwarf, halfling, tiefling, dragonborn, gnome,
  half_elf, half_orc`) with ability bonuses, size, speed, darkvision, resistances, languages,
  named traits, and **granted skill proficiencies** (Elf → Perception, Half-Orc → Intimidation).
  Tieflings and halflings are fully fleshed out (Infernal Legacy / fire resistance; Lucky, Brave).
- **classes.py** — all **twelve** classes outlined at level 1: hit die, two saving-throw
  proficiencies, an armor/weapon baseline (→ AC and the starting attack), a skill list + how many
  to choose, spellcasting type (`full`/`prepared`/`half`/`pact`/None) and ability, and the
  signature level-1 features. It's an outline: a playable L1 sheet plus documented features, not
  the full progression (rage counts, slots, subclasses live in the feature text, not simulated).
- **proficiencies.py** — the proficiency bonus by level, the logic that turns skill picks +
  race grants into the sheet's proficiency list, saving-throw math, and spell DC / attack bonus.

## How creation uses it
With this layer present, the wizard runs six steps: name → race → class → **alignment** →
abilities → **skills**. The skills step is *dynamic*: its options are the chosen class's skill
list and its count is the class's number (Rogue 4, Ranger/Bard 3, most others 2), via the
engine's `options_for` / `count_for` hooks. `build_pc` then assembles the sheet — applying race
bonuses and traits, class HP/AC/attack/saves/features, chosen + race-granted proficiencies, the
alignment pair, and spellcasting stats for casters.

## Honest scope
Alignment has no mechanical hook (faithful to D&D — it's for narration). Unarmored Defense
(Barbarian/Monk) and unarmored casters are approximated via an AC base + DEX, not the exact
10 + DEX + CON/WIS formula. Half-Elf "Skill Versatility" and Rogue/Bard Expertise are noted as
traits but not implemented as extra picks. Everything mechanical (abilities, HP, AC, attack,
proficiency bonus on skills and saves, spell DC) is real and drives a working level-1 sheet.

## Backgrounds, leveling, and alignment mechanics

Three further modules round out the additional layer:

- **backgrounds.py** — twelve backgrounds, each granting two skill proficiencies plus tools,
  languages, equipment, and a background *feature*. Each also carries the roleplay tables 5e uses
  — suggested **personality traits, ideals, bonds, and flaws** — which are the **narrative data
  handed to the LLM**: `build_pc` stashes them (with the feature) under `sheet["roleplay"]` via
  `roleplay_seed()`, and the narrator reads them to voice the character and seed hooks. Creation
  gains a **background** step (name → race → class → background → alignment → abilities → skills).
- **leveling.py** — the full **1-to-20 progression for every class**. `derive_level` returns the
  proficiency bonus, max HP (PHB fixed-average), the cumulative feature list, spell slots (full /
  half / pact tables), the class's scaling resources (rage count, ki, sneak-attack dice, extra
  attacks, lay-on-hands pool, bardic die, sorcery points, eldritch-blast beams, ...), and how many
  ASIs are due. The ruleset applies it via `advance_to_level(pc, n)` / `level_up(pc)` — which also
  rescale the attack bonus and spell DC for the new proficiency bonus — and exposes the whole table
  through `class_progression(class_key)`.
- **alignment.py (mechanics)** — the parts of 5e where alignment actually bites. The Evil-and-Good
  spell family (Detect / Protection from / Magic Circle) keys off six **creature types**
  (aberration, celestial, elemental, fey, fiend, undead), so NPCs carry a `creature_type` and the
  ruleset exposes `detect_evil_and_good`, `protection_from_evil_and_good`, and `magic_circle_blocks`.
  Alignment-**gated magic items** (Holy Avenger, the Talismans, the Books of Exalted Deeds / Vile
  Darkness) and **sentient-item conflict** key off the nine-grid, via `attune_item` and
  `sentient_item_conflict`.

### Honest scope (these features)
Leveling is an **outline grown to 20**: HP, PB, slots, scaling resources, ASI *counts*, and the
named feature list are all real, but subclass choices appear as a generic "Subclass feature" and
ASIs are reported as pending (abilities aren't auto-raised — that's left to the player/narrator).
Alignment mechanics implement exactly what 5e defines (deliberately light): the type-based spells
and the item/sentient-item rules. Backgrounds grant their fixed skills, tools, languages, feature,
and the full narrative tables for the LLM.

## Spell lists and the narrator briefing

- **spells.py** — the **per-class spell lists**. Each spell is defined once and carries the set of
  classes whose list it's on, so the eight casters' lists derive from a single source of truth
  (adding a spell is a one-liner). A spell records its level (0 = cantrip), school, and a one-line
  effect for the narrator. Helpers give a class's full list, its list grouped by level, and the
  **repertoire size** — cantrips known plus spells *known* (Bard/Sorcerer/Ranger/Warlock, fixed
  counts) or *prepared* (Cleric/Druid/Wizard = ability mod + level; Paladin = ability mod + half
  level). The ruleset records this on `sheet["spellcasting"]` (`cantrips_known`, `spells_method`,
  `spells_count`) at build and on level-up, and exposes the list via `class_spell_list(key)` /
  `available_spells(pc)`. This is a curated cross-section of the iconic SRD/PHB spells at every
  level, not the full catalogue; spells narrate as qualitative effects rather than simulated dice.
- **Narrator briefing** — the background **roleplay seed** now reaches the prose. A new optional
  Ruleset hook, `narrator_briefing(pc)`, returns a compact second-person character brief (identity,
  alignment leaning, the background feature, and a personality trait / ideal / bond / flaw drawn
  from the seed). The exploration and combat narrators prepend it to their system prompt, so the
  model voices the character in keeping with who they are — while the hard rules (no invented
  outcomes, no numbers) stay intact. A ruleset that supplies no briefing leaves the prompt
  unchanged, so the engine stays system-agnostic.

## Choosing roleplay, choosing spells, and resting

- **Roleplay selection in creation** — creation now ends with four steps to pick a personality
  **trait, ideal, bond, and flaw** from the chosen background's tables (dynamic `choose_one` steps
  whose options come from the background). The picks are stored under `sheet["roleplay"]["chosen"]`
  and are exactly what the narrator briefing voices (falling back to the first suggestion if a game
  builds a sheet without choosing).
- **Choosing spells** — `prepare_spells(pc, keys)` (Cleric/Druid/Wizard/Paladin) and
  `set_known_spells(pc, keys)` (Bard/Sorcerer/Ranger/Warlock) set a caster's repertoire, validated
  against the class list and capped at the prepared/known count; `set_cantrips(pc, keys)` does the
  same for cantrips. Off-list picks, duplicates, cantrips-as-leveled-spells, and overflow are all
  dropped, so the stored list is always legal.
- **Long rest** — `long_rest(pc, prepared=None)` restores HP to full, refreshes spell slots
  (`spell_slots_remaining`) and per-rest resources, and lets a prepared caster swap their prepared
  spells. The engine exposes it as a **`rest`** command (alongside look/status/save/quit). Note:
  spell/resource *expenditure* isn't simulated yet, so today a rest mainly restores HP and re-arms
  the repertoire — the mechanic is in place for when casting is tracked.

## Spending resources (expenditure simulation)

Casters and martials now *spend* what they use, and rests bring it back:

- **Spell slots** — the sheet tracks `spell_slots_remaining` alongside the maxima. `cast_spell(pc,
  key)` spends the lowest slot of at least the spell's level (upcasting when low slots run out);
  cantrips are free; warlocks spend Pact Magic slots. `spend_slot(pc, level)` is the low-level door.
- **Class resources** — `resources_remaining` holds the finite pools (rages, ki, lay-on-hands
  points, channel divinity, action surge, sorcery points, ...). `spend_resource(pc, name, amount)`
  draws them down and refuses to overspend; `resource_remaining(pc, name)` reads them.
- **Rests** — `short_rest(pc)` refreshes the short-rest pools (ki, action surge, channel divinity,
  wild shape, bardic inspiration) and a warlock's pact slots; `long_rest(pc)` restores HP and
  refills *every* slot and pool, re-prepares (if asked), and advances the world clock (shops may
  restock). Level-up also refreshes pools to their new maxima.

## Items and trade

- **`items.py`** — a catalogue of ~46 items. Each `Item` carries a category, rarity, gp value,
  attunement flag, mechanical bonuses, effects, lore (a line for gear, something fancier for the
  marvels), optional **special details** (cursed, alive, talking, a god's relic behind a humble
  rarity), the **regions** it can appear in (empty = anywhere), and a **`plot`** flag. Plot items
  (the Dawnshard, Whisperfang, the Crown of the Lost King, the Sealed Codex) never enter free trade.
- **`trade.py`** — 5e-style pricing (`price_to_buy` = value x markup; `price_to_sell` = value x
  buy-back rate) plus shop generation. `generate_stock` weights eligible items by rarity (common is
  plentiful, legends scarce), filtered by a tradesman's categories, rarity floor/ceiling, and
  region, with plot items excluded and a `rarity_bias` to tilt toward the exotic. `restock` rolls a
  shop forward, keeping rarer wares longer (retention rises with rarity) and topping back up to size.

The ruleset wires these together: `open_shops(seed)` rolls every tradesman's stock at game start,
`shop_listing(key)` shows wares with prices, `buy`/`sell` move gold and items (refusing to buy plot
items), and each long rest advances a world clock that restocks tradesmen as their interval comes up.

## Resting in cities

`rest_context(location)` decides whether the party is inside a settlement and whether they can rent
a bed (reading the active setting's `Location.kind`, with keyword fallbacks). `rest_attempt(...)`
then resolves a long rest: the wild and rented inn rooms rest normally, but bedding down openly in a
city draws the City Watch -- a warning, then a final warning, then an arrest for disturbing the
public order (a night in a cell and a small fine) unless the party leaves, talks their way out, or
fights the guards off. The engine's `rest` command tracks attempts and the imprisonment flag.
