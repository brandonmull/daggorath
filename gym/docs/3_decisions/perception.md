# Perception

_1 Sep 2026_

## Decision

The observation is a six-channel `Dict` — `scalars` (10, uint16), `hands` (2), `pack` (8), `creatures` (32×4), `objects` (8×3), and a two-plane `map` (2×32×32) — assembled by `as_perceived()` and gated by light (line-of-sight) and mode (LOOK vs EXAMINE). The light scalars are the two effective sums only; the ambient and torch components are true-state. The two light scalars read 0 outside LOOK: the player sees the dungeon's light only in the dungeon view.

## Why

- **Act-first, fairness-later.** Prioritize the state the agent needs to *act* — the maze, creatures, light — over faithfulness to what a real player perceives. A shell of self-fields is a working interface, not a trainable task.
- **The gate is RAM line-of-sight, not screen pixels.** The game computes visibility from RAM, so the environment mirrors that logic rather than reverse-engineering the display. Reach is `min(light, 10)`; `light == 0` is blackout.
- **Light is perceived as its effect, not its parts.** The player sees the dungeon brighten and magic doors appear, never the torch's own light or the ambient level — so the observation carries only the two effective sums, and the components are true-state.
- **Modal perception.** LOOK reveals the dungeon, EXAMINE reveals the pack, mutually exclusive via `displayFunction`. The two light scalars belong to the dungeon view, so they read 0 outside LOOK.
- **Heading is true-state.** The player sees the dungeon shape ahead, not a compass bearing, so `at_heading` is not perceived and facing must be inferred from the map.
- **Position and level are true-state.** The player has no coordinates and no level readout, so `at_floor`, `at_cell_x`, and `at_cell_y` are not perceived. Where the agent is must come from spatial memory built over the map, never from the observation.
- **Floor objects read class-only.** The 3D view draws them as pictures keyed by class alone, never the proper name or reveal state, so the objects channel reports the class, and the proper name and reveal state reach perception only once the object is possessed.
- **The lit torch is highlighted in the pack.** The EXAMINE view color-flips the lit torch's name, and that is the only place color changes, so the pack channel carries the highlight as a bit beside the specifier. The hands and floor objects stay plain.
- **Perceived is declared, not inferred.** Each field marks itself perceived (opt-in, default hidden), and the observation is the positive filter of those marks, so a hidden fact never leaks into perception by default.
- **No memory, no novelty.** Perception is instantaneous; memory and "first seen" bookkeeping are the agent's and the reward wrapper's job, never the observation's.
- **`Dict` + `MultiInputPolicy`.** A CNN reads the spatial map; an MLP reads the flat scalars and entity tables.

## What Changed

- `daggorath_gym/state.py` — `PERCEIVED_SPACE` and `as_perceived()`.
- `daggorath_agent/feature_extractor.py` — the CNN + MLP split over the channels.
