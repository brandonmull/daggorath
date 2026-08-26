# Persist Learning — Plan

_How training persists: learned weights are written to disk, survive the training run, and can be loaded by a later run._

## Purpose

A training run must outlive itself. Without persistence, "train for a bit, then utilize the training later" has no meaning — the weights vanish when the process exits. Persistence makes the learned agent a durable, reloadable artifact.

## Dependencies

This feature rests on three things. Two are already in the codebase; one is knowledge that must be recorded here because it is required for the read side to work.

### Already implemented — recorded here for completeness

- **Checkpoint writing** lives in `daggorath_agent/train.py`: a `CheckpointCallback` writes periodic snapshots, and a final `model.save(...)` writes the definitive copy. This was introduced by the watch-training plan as "Where training goes — checkpoints."
- **The checkpoint directory** is `daggorath-agent/checkpoints/`, declared in `.gitignore`. Weights are large generated binaries, not source; they must never be committed.

### Currently undocumented — specified here

- **The checkpoint format and contract** (below), which nothing has yet written down but which the read side depends on.
- **The load mechanism** (below), which the deferred entry points will use.

## What a checkpoint is

A checkpoint is the file written by Stable-Baselines3's `model.save(path)`: a standard `.zip` archive containing

- the policy network weights (the learned parameters, feature extractor included),
- the optimizer state (so training can resume exactly, not just start from a loss snapshot),
- normalization statistics (none yet, but the slot exists),
- the hyperparameters and configuration.

Because the observation is a `Dict` read by a custom extractor, the checkpoint stores `DaggorathFeaturesExtractor` **by import path**, not by copying the class. Two consequences, both hard requirements on the codebase:

1. `DaggorathFeaturesExtractor` must keep its module path and class name. Renaming or moving it breaks every existing checkpoint.
2. Loading a checkpoint requires importing `daggorath_agent.feature_extractor` so the class resolves — which is why the package layout matters.

## Current state — the write side

Training already persists learning. On a run it writes:

- `checkpoints/ppo-daggorath_<STEP>_steps.zip` — every `checkpoint_freq` steps (default 10,000),
- `checkpoints/ppo-daggorath.zip` — the final model, overwritten on each completed run.

The write side is complete and in service.

## The load side — the contract for future entry points

Reading a checkpoint back has a fixed shape, and it is recorded here so the deferred entry points implement it once, correctly:

```
model = PPO.load(path)
model.set_env(env)              # the loaded model carries no environment
model.learn(total_timesteps=...)  # to continue, or skip to just predict
```

Two specifics that would otherwise be footguns:

- **`set_env` is mandatory.** A loaded model has policy weights but no environment attached; predicting or learning without reattaching fails.
- **`reset_num_timesteps=False` is what "continue" means.** `learn()` defaults to `reset_num_timesteps=True`, which would restart the step counter and the learning-rate schedule from zero. To genuinely continue earlier training, pass `False`.

## Entry points

The two read-side entry points are specified here against this exact contract. `--resume` is implemented; `play.py` is deferred.

### Reload to continue — `train.py --resume` (implemented)

```
python -m daggorath_agent.train --resume checkpoints/ppo-daggorath --total-timesteps 50000
```

Loads the checkpoint, reattaches the environment, and learns more steps on top, with `reset_num_timesteps=False` to preserve the schedule. Without `--resume`, training stays as today: fresh random initialization.

### Reload for use — `play.py` (deferred)

Load a checkpoint and watch the trained agent act, with no further training:

```
python -m daggorath_agent.play --model checkpoints/ppo-daggorath
```

Builds the environment windowed via the same `make_env(window=True, sound="sdl")` as training, then loops `reset → predict → step` for `--episodes` in a visible MAME window. Default is deterministic action selection. `--sound none` dodges the known WSLg jitter.

## Status

The read side of this plan is partially built: `--resume` is implemented, and `play.py` remains deferred.

## Decisions

- **Persistence is one concept.** Writing is live today; reading is specified here and deferred. The plan is the contract that makes the deferred half mechanical.
- **The checkpoint is gitignored output, never source.**
- **The extractor's import path is a persistence contract.** Its name and location are frozen by this decision.
- **"Continue" means `reset_num_timesteps=False`.** Anything else silently restarts learning rather than extending it.