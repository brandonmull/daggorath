# Training Pipeline

_1 Sep 2026_

## Decision

The whole job is one function: `train()` builds the environment headless, applies the reward and cast wrappers, wraps the result in a single-slot vector environment, and trains PPO. `make_env()` layers three objects in a fixed order — `DaggorathEnv` → `DaggorathRewardWrapper` → `CastScalarsWrapper`.

## Why

- **Even one environment must be vectorized.** SB3's algorithms accept only the `VecEnv` interface, not a bare `gym.Env`, so `DummyVecEnv` wraps the single env in-process; `SubprocVecEnv` would be multiprocessing overhead at N=1.
- **Wrapper order is fixed.** The reward wrapper wraps the raw env so it can read `current_state`; the cast wrapper wraps the reward wrapper so the reward still sees the original observation.

## What Changed

- `daggorath_agent/train.py` — `make_env()` (env → reward → cast) and `train()` (VecEnv → PPO → checkpoints), plus the `--watch`/`--resume` CLI.
- Deferred: joint action masking for the INCANT verb form — a cross-axis constraint SB3's per-axis masks can't express. Until then `derive_command_index` returns `None` for invalid pairs and `step()` no-ops.
