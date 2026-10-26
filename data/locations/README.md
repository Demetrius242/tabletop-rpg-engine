# Location catalog

Each `*.json` is one location: a graph of named **zones**. `load_location_file(path)` builds
an `Arena` the combat controller uses for movement, reach, cover, and fleeing.

## Fields
- `name` (str), `summary` (str) — label and designer note.
- `zones` (list, required) — each zone:
  - `name` (str, required)
  - `adjacent` (list of zone names) — one move-step connects these. Keep it **symmetric**
    (if A lists B, B should list A).
  - `cover` — `"none" | "light" | "heavy"` (raises a ranged defender's difficulty).
  - `elevation` (int) — a higher attacker gets a small to-hit edge.
  - `hazard` (str) — narrative flavor.
  - `is_exit` (bool) — fleeing means reaching a zone flagged `true`. **Every map needs one.**
- `placements` (obj) — optional `"<combatant name>": "<zone name>"` starting positions.

See `../../docs/extend_content.txt`.
