# NPC catalog

Each `*.json` here is one NPC. `engine.content.load_npc_file(path, ruleset)` turns it into
a runtime `Combatant` using the active ruleset's enemy factory; fields the factory doesn't
take are ignored, so the same schema adapts across rulesets.

## Fields
- `name` (str, required) — display name.
- `kind` (str) — `"vampire"`, `"ghoul"`, `"mortal"`, `"wraith"`, … . Some rules key off it
  (e.g. the Thaumaturgy rite *Ward versus Ghouls* only bites a `kind: "ghoul"`).
- `summary` (str) — designer note; not read by the engine.
- `attributes` (obj) — `strength, dexterity, stamina, charisma, manipulation, appearance,
  perception, intelligence, wits`; omit any to default to 2.
- `abilities` (obj) — e.g. `brawl, melee, dodge, intimidation, stealth, occult, …`; default 0.
- `disciplines` (obj) — rating by **label**, e.g. `{"Potence": 2, "Obtenebration": 4,
  "Path of Blood": 3}`. Passive Disciplines (Potence/Fortitude/Celerity/Auspex) apply
  automatically; the rest become invocable powers at that rating.
- `attack` (obj) — `{name, attribute, skill, damage_rating}`; defaults to fangs and fists.
- `soak` (int) — base soak before Fortitude (which is added automatically).
- `generation` (int) — `0` for a ghoul/mortal; vampires 6–13. Gates Dominate and the blood pool.
- `humanity` (int 1–10), `intelligence` (int), `morale` (int), `mindless` (bool),
  `comprehends_language` (bool).
- `inventory` (list), `known_rituals` (list of ritual keys) — for spellcaster NPCs.
- `statuses` (list) — starting status tokens (e.g. `["warded"]` to shield against blood magic).
- `persona` (obj) — free-form flavor (voice, wants, fears) for the combat bark/rant hook.

See `../../docs/extend_content.txt` for a worked example and the full status vocabulary.
