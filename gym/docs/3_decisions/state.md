# State Module

_1 Sep 2026_

## Decision

The environment tracks sixteen scalar game-state fields plus five world channels — the 32×32 maze, the 32-slot creature array, floor objects, the lit torch, and holes/ladders — ships them over the FIFO as fixed-size tagged records, and deserializes them into an immutable `DaggorathState` value object in Python.

The frame is 20 bytes (12 u8 + 4 u16) holding the sixteen fields in fixed order — the shared contract with Lua's `SCHEMA`. Seven tags exist: `S` (frame changed), `T` (command-area text changed), `B` (both), and the world records `M`, `C`, `O`, `H`. Change detection drops identical frames, writing a record only when its snapshot differs. Of the sixteen fields, fourteen reach the observation's `scalars` channel (`PERCEIVED_FIELDS`); the two ambient-light components are true-state only.

The sixteen fields: `game_mode`, `display_function`, `at_floor`, `at_cell_x`, `at_cell_y`, `at_heading`, `ambient_light_physical`, `ambient_light_magical`, `effective_light_physical`, `effective_light_magical`, `player_weight`, `player_strength`, `m0221`, `player_fainting`, `heart_beat_interval`, `evil_wizard_dead`. `heart_rate` is derived (60 / interval) and never shipped. The lit torch's `minutes`, `physical_light`, and `magic_light` are object data, shipped in the `O` record as a six-byte lit-torch entry rather than as scalars.

## Why

- **Track what the player perceives, plus self-state.** The field list is the player's own frame: position, heading, light, body (weight, strength, the exertion pool `m0221`), heart, and the modal display. Light ships as its two sums — the *effective* physical and magical light the player actually sees. The components (the ambient level and the torch's own light) are true-state: the player sees the dungeon brighten, never the torch's contribution.
- **Object data, not pointers.** Holdings ship as decoded identities (hands, pack), never raw addresses. The torch's minutes/light were the last pointer-read fields in the schema; they now ship as a lit-torch entry in the object record, the same way the hands and pack do.
- **Strength is not hidden — it's imprecise.** The player genuinely knows their strength through effect (a kill makes you stronger; stronger means fewer hits). The environment always tracks it — reward and termination need it — and exposing the exact number is a training accelerant; the "agent learns its own body" variant is a deferred curriculum ablation.
- **Immutability for safe, fast reads.** `DaggorathState` uses `__slots__` and overrides `__setattr__`, so the reported state cannot be mutated from Python and attribute access stays a single C-level lookup.
- **The wire is the shared contract.** Byte order in Lua's `SCHEMA` and Python's `FIELDS` must match exactly, so the same bytes mean the same field on both sides.

## What Changed

- `emulation/plugins/daggorath/state.lua` — `SCHEMA`, per-frame sampling, the `S`/`T`/`B`/`M`/`C`/`O`/`H` records (the `O` record now carries the lit torch), readiness-gated on `displayFunction`.
- `daggorath_gym/state.py` — `FIELDS`, `PERCEIVED_FIELDS`, `DaggorathState`, and `as_perceived()` (the perception gates).
- Creature and object sampling (`C`/`O` records) and the command-area decode (`screen.py`) are part of this module's pipeline.

## Reference

- Decisions: `docs/3_decisions/readiness-gating.md`, `docs/3_decisions/ipc-hybrid.md`
