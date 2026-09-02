# Deployment

_1 Sep 2026_

## Decision

One repo holds two packages — `daggorath-gym` (the environment, `gymnasium` + `numpy` only) and `daggorath-agent` (the reference trainer) — separated by an import boundary, not a repo boundary. `MameConfig` (window, sound) and `IpcConfig` (FIFO path, command host/port) flow through the environment's constructor.

## Why

- **The environment never imports a training library.** The split is a boundary, not a fork: the environment stays trainer-agnostic, and the trainer adapts.
- **The reward is a choice, not a fact.** Only the raw environment would be registered (`Daggorath-v0`); the reward wrapper is an explicit opt-in, so the world and its worth stay separate.
- **`daggorath-agent` is the reference implementation.** Registration answers "how do I get the env"; the agent package answers "how do I actually train with it" — the wiring an external user copies.

## What Changed

- `gym/` — `daggorath_gym` (environment, emulator, reward, state, commands, screen, navigation).
- `agent/` — `daggorath_agent` (`train.py`, `feature_extractor.py`, `wrappers.py`).
- Deferred: `Daggorath-v0` registration (Known Issue #1); joint action masking.
