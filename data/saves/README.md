# Saves

A save is the **character record + world condition** in one JSON file:
the PC sheet and statuses, the current location and mode, recent narration history, and
story `flags`. Written by `engine.state.save_game(state, path)` and restored by
`load_game(path)` (also re-exported from `engine.content`).

## Shape
```
{ "pc": { "name", "is_pc", "statuses": [...], "sheet": { ...full character sheet... } },
  "location": "A Tremere Chantry Cell",
  "mode": "exploration",
  "history": [ {"role": "narrator"|"player", "text": "..."} ],
  "flags": { "chapter": "Prologue: The Ledger", ... } }
```
The `sheet` is ruleset-shaped and opaque to the engine — for the Storyteller ruleset it holds
attributes, abilities, disciplines, blood, humanity, willpower, inventory, known_rituals, and
more. `example_aisling.json` is a complete, loadable example. See `../../docs/extend_content.txt`
for using `flags` to drive a story.
