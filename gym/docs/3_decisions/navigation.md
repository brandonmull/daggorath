# Navigation

_1 Sep 2026_

## Decision

The 32×32 maze — one byte per cell packing four 2-bit edge fields (0 open, 1 normal door, 2 magic door, 3 wall) — and the holes/ladders table are decoded in pure Python, and the visible set is a corridor walk with reach `min(light, 10)`.

## Why

- **"Cell," not "room."** The dungeon is a uniform grid of cells and has no rooms at all — only halls. The word matters because every cell packs four edges, not an area.
- **Sight is light-bounded and per-channel.** The physical light drives the corridor walk; the magic light separately gates magic doors and magical creatures. `effective_light_physical == 0` is pure blackout.
- **Magic doors are a distinct edge value, rewritten in perception.** A magic door draws as a triangle under magic light but reads as a wall under a physical-only torch — so the perceived map reports the light-gated type while the true byte stays internal.
- **Instantaneous visibility, no memory.** The environment reports only what is visible now; map memory is the agent's job, built in a wrapper.

## What Changed

- `daggorath_gym/navigation.py` — `decode_edge`, `walk_corridor`, `rewrite_magic_doors`; direction numbering follows the disassembly (0 North, 1 East, 2 South, 3 West).
- `emulation/plugins/daggorath/state.lua` — the `M` and `H` world-channel records.

## Reference

- Finding: `docs/findings/deterministic-maze.md`
