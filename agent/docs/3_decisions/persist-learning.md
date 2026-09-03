# Persist Learning

_1 Sep 2026_

## Decision

A checkpoint is what `model.save(path)` writes — a `.zip` holding the policy weights, optimizer state, normalization statistics (empty slot), and hyperparameters. The load contract is `PPO.load(path)` → `set_env(env)` → `learn(..., reset_num_timesteps=False)`; `train.py --resume` is the implemented entry point.

## Why

- **The extractor's import path is a persistence contract.** The checkpoint stores `DaggorathFeaturesExtractor` by import path, not by copying the class — renaming or moving it breaks every existing checkpoint.
- **`set_env` is mandatory.** A loaded model has weights but no environment; predicting or learning without reattaching fails.
- **"Continue" means `reset_num_timesteps=False`.** The default `True` restarts the step counter and learning-rate schedule; `False` genuinely extends the run.

## What Changed

- `daggorath_agent/train.py` — `CheckpointCallback` + final `model.save(...)` (write side), and `--resume` (read side).
- The checkpoint directory is `agent/checkpoints/` (gitignored).

## Reference

- Remaining: `../2_plans/persist-learning.md` (`play.py`)
