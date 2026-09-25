# Knowledge Store Experiences

## Goal

Collect real experiences from the running game in the shape the knowledge-store plan defines, so beliefs and plans can be built from them by hand. The agent boots the real environment and plays the torch recipe, EXAMINE then PULL LEFT TORCH then USE LEFT, with a few turns around it.

## Status

Built and collecting.

## Approach

The driver boots `DaggorathEnv` headless and plays an eight-command script. Each command becomes one experience: the full perceived situation before the action, the command, and the facts that changed after it, in order. The situation is a plain object keyed by fact name; effects is an array of partial states, each a subset of the situation's facts.

The situation reads the perceived observation and the object wrapper. Each effect is one change step: the facts that differed from the previous step, in the order the game reported them.

## The perceived state

Each situation object holds the 10 perceived scalar fields by name, then `hands`, `pack`, and `floor`. The hands and pack are lists of object structures, each with a type, a specifier, and the flags revealed, consumable, and consuming, or null for an empty slot. The floor is a list of class names. The structures come from the agent's `PerceivedObjectsWrapper`.

Two scalar values are worth naming for reading the log. `display_function` is `52838` for LOOK and `54421` for EXAMINE. `effective_light_physical` is `0` in the dark, `7` once the torch is lit, and `0` in any mode other than LOOK, since the light is a dungeon fact.

The pack reads all-null outside EXAMINE, because the game hides the inventory outside that view. Once examined, its slots read the object structures, and the lit torch's slot carries `consuming: true`.

## The scenario

| step | action | what the run shows |
|---|---|---|
| 1 | TURN LEFT | nothing changes, heading is not perceived |
| 2 | EXAMINE | display LOOK to EXAMINE, pack all-null to WOODEN SWORD, PINE TORCH |
| 3 | ATTACK LEFT | nothing changes, the hand is empty |
| 4 | PULL LEFT TORCH | a hand empty to PINE TORCH, pack drops the torch |
| 5 | USE RIGHT | nothing changes, the hand is empty |
| 6 | USE LEFT | a hand PINE TORCH to empty, pack gains the lit torch |
| 7 | MOVE | no movement, m0221 0 to 7, heart_beat_interval 46 to 40 |
| 8 | LOOK | display EXAMINE to LOOK, pack all-null, effective_light 0 to 7, m0221 7 to 5, heart_beat_interval 40 to 41 |

What the run shows. The empty-hand commands change nothing perceived. MOVE against a wall changes nothing positionally but exerts the player, so m0221 (the exertion pool) rises and the heart beats faster. The lit dungeon appears on LOOK, not at USE, because the light scalars are gated to LOOK. Because effects is an array, a step that changes several times lands as several partial states: LOOK's effects are the body's drift, then the view flip with the light, then more drift.

## Output shape

`experiences.json` has two top-level keys:

- `session`: the one run, with its goal "light the torch".
- `experiences`: the eight steps, each with an id, session id, situation, action, and effects. The situation is an object keyed by fact name; effects is an array of such objects, in order.

## Beliefs

`beliefs.py` defines the belief shape — a situation, an action, and effects — matching the experience's shape, so nothing is lost. Each belief is read off one experience from the log: the full situation before the action becomes the belief's situation, and the observed changes become the belief's effects. It writes `beliefs.json`.

The four beliefs:

| id | action | effects |
|---|---|---|
| 1 | EXAMINE | display EXAMINE, pack revealed |
| 2 | PULL LEFT TORCH | a hand torch, pack loses torch |
| 3 | USE LEFT | a hand empty, pack regains the lit torch |
| 4 | LOOK | display LOOK, pack hidden, light 7, plus the body drift |

Belief 4 is the one to notice. Its situation, display EXAMINE with the torch in the pack, does not say the torch is lit, because the lit state is true-state and invisible to perception. The light effect it writes is under-determined by its situation, which is exactly the attribution problem the store is meant to expose.

Run it with `python agent/sandbox/knowledge-store/beliefs.py`.

## Running

```bash
python agent/sandbox/knowledge-store/collect_experiences.py
```

Boots MAME headless, plays the script, and writes `experiences.json` next to the script.

`generate_experiences.py` is the no-MAME alternative: it writes the same experience shape from a hand-held state to `experiences.simulated.json`, for iterating on the shape without waiting on the game.

## Next

The chain runs the torch recipe cleanly. The lit state already did its work: the unlit and lit torch no longer compare equal, so the earlier fan-out is gone. The next session is about breaking the chain, by appending a second session's beliefs to the same log and watching where the matching gives out.

Confusers left to try:

- **Pack contents change.** Pick up or stow an object before the recipe, so the pack holds a third item and the old beliefs stop chaining to the new ones.
- **Effect noise.** A command whose settle window overlaps the body's own drift, so its effect carries m0221 and the heart and matches nothing downstream. LOOK already shows this.
- **Contradiction.** An action whose outcome turns on a fact the situation does not record, ATTACK against a creature versus empty air. The situation reads the same, the effects differ, and two beliefs disagree.
- **MOVE.** With position cut from perception, a move and a bump into a wall read the same, since only exertion and the map change and the map is not yet a recorded fact.

Each attempt is a script change to `collect_experiences.py`, then a re-run of the collector, beliefs, and chain.
