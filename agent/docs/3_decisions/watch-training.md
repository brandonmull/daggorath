# Watch Training

_1 Sep 2026_

## Decision

Training exposes one intention flag, `--watch`, which sets the MAME window and sound together; `--sound` overrides, `--total-timesteps` bounds the run. Checkpoints land in `agent/checkpoints/` (gitignored) — periodic snapshots plus a final `ppo-daggorath`.

## Why

- **`--watch` is the intention; `--sound` is the escape hatch.** The common case is one flag; the WSLg audio jitter is an override, not part of the normal invocation.
- **Checkpoints are gitignored artifacts.** Weights are large generated binaries, not source.
- **`window=True` is "watching."** MAME's own window is the rendering — there is no Gym `render()` — and each `step()` blocks on `recv()` at real-time rate, so the agent is watched acting as it learns.

## What Changed

- `daggorath_agent/train.py` — `make_env(window, sound)`, `train(...)` forwarding the knobs, the `--watch`/`--sound`/`--total-timesteps` CLI, `CheckpointCallback` + final save.

## Reference

- Remaining: `../2_plans/watch-training.md` (the `-video none` headless enforcement)
