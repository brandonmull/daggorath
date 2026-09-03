# State Module

_1 Sep 2026_

## Decision

The environment tracks nineteen game-state fields plus four world channels — the 32×32 maze, the 32-slot creature array, floor objects, and holes/ladders — ships them over the FIFO as fixed-size tagged records, and deserializes them into an immutable `DaggorathState` value object in Python.

The frame is 23 bytes (15 u8 + 4 u16) holding the nineteen fields in fixed order — the shared contract with Lua's `SCHEMA`. Seven tags exist: `S` (frame changed), `T` (command-area text changed), `B` (both), and the world records `M`, `C`, `O`, `H`. Change detection drops identical frames, writing a record only when its snapshot differs.

The nineteen fields: `game_mode`, `at_floor`, `at_cell_x`, `at_cell_y`, `at_heading`, `ambient_light_physical`, `ambient_light_magical`, `effective_light_physical`, `effective_light_magical`, `torch_minutes`, `torch_physical_light`, `torch_magic_light`, `player_weight`, `player_strength`, `m0221`, `heart_beat_interval`, `player_fainting`, `evil_wizard_dead`, `display_function`. `heart_rate` is derived (60 / interval) and never shipped.

## Why

- **Track what the player perceives, plus self-state.** The field list is the player's own frame: position, heading, light, body (weight, strength, the exertion pool `m0221`), heart, and the modal display. Light ships as its two sums *and* their torch factors so the agent can relate its torch to its ability to see.
- **Strength is not hidden — it's imprecise.** The player genuinely knows their strength through effect (a kill makes you stronger; stronger means fewer hits). The environment always tracks it — reward and termination need it — and exposing the exact number is a training accelerant; the "agent learns its own body" variant is a deferred curriculum ablation.
- **Immutability for safe, fast reads.** `DaggorathState` uses `__slots__` and overrides `__setattr__`, so the reported state cannot be mutated from Python and attribute access stays a single C-level lookup.
- **The wire is the shared contract.** Byte order in Lua's `SCHEMA` and Python's `FIELDS` must match exactly, so the same bytes mean the same field on both sides.

## What Changed

- `emulation/plugins/daggorath/state.lua` — `SCHEMA`, per-frame sampling, the `S`/`T`/`B`/`M`/`C`/`O`/`H` records, readiness-gated on `displayFunction`.
- `daggorath_gym/state.py` — `FIELDS`, `DaggorathState`, and `as_perceived()` (the perception gates).
- Creature and object sampling (`C`/`O` records) and the command-area decode (`screen.py`) are part of this module's pipeline.

## Reference

- Decisions: `docs/3_decisions/readiness-gating.md`, `docs/3_decisions/ipc-hybrid.md`
