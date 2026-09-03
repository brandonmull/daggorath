# Perception

_1 Sep 2026_

## Decision

The observation is a six-channel `Dict` — `scalars` (19, uint16), `hands` (2), `pack` (8), `creatures` (32×4), `objects` (8×3), and a two-plane `map` (2×32×32) — assembled by `as_perceived()` and gated by light (line-of-sight) and mode (LOOK vs EXAMINE).

## Why

- **Act-first, fairness-later.** Prioritize the state the agent needs to *act* — the maze, creatures, light — over faithfulness to what a real player perceives. A shell of self-fields is a working interface, not a trainable task.
- **The gate is RAM line-of-sight, not screen pixels.** The game computes visibility from RAM, so the environment mirrors that logic rather than reverse-engineering the display. Reach is `min(light, 10)`; `light == 0` is blackout.
- **Modal perception.** LOOK reveals the dungeon, EXAMINE reveals the pack — mutually exclusive via `displayFunction`.
- **No memory, no novelty.** Perception is instantaneous; memory and "first seen" bookkeeping are the agent's and the reward wrapper's job, never the observation's.
- **`Dict` + `MultiInputPolicy`.** A CNN reads the spatial map; an MLP reads the flat scalars and entity tables.

## What Changed

- `daggorath_gym/state.py` — `PERCEIVED_SPACE` and `as_perceived()`.
- `daggorath_agent/feature_extractor.py` — the CNN + MLP split over the channels.
