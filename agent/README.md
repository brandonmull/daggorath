# Daggorath Agent

The training harness for the [Daggorath Gym](../gym) environment. This is the reference end-to-end PPO trainer: it consumes `daggorath_gym` as a library and turns it into a working Stable-Baselines3 run.

The split is deliberate — the environment package imports no training library, and this package imports only what it needs to train. See `gym/docs/3_decisions/deployment.md` for the full design.

## Prerequisites

- WSL (MAME runs under WSL; see the environment's `README.md` for MAME + ROM setup).
- A Python 3.12 venv.

## Install

Run from the workspace root, where both packages sit side by side:

```
source .venv/bin/activate
pip install -e gym
pip install -e agent
```

Both packages are editable-installed, so `daggorath_gym` and `daggorath_agent` resolve from source. `pip install -e gym` also brings in the environment's own `gymnasium`/`numpy` deps; `pip install -e agent` brings in Stable-Baselines3, torch, and SB3-contrib.

## Run

```bash
cd ~/Projects/Daggorath/agent
source ../.venv/bin/activate
python -m daggorath_agent.train --watch
```

`--watch` opens the MAME window with sound, so you watch the agent act as it trains. Checkpoints land in `checkpoints/` (periodic) and `checkpoints/ppo-daggorath` (final).

Headless, no window: `python -m daggorath_agent.train`

Other options:
- `--sound none` — windowed but silent
- `--total-timesteps N` — bound the run (default 100000)
- `--resume checkpoints/ppo-daggorath` — continue a previous run on top of its saved weights

## Tests

```
pip install pytest
python -m pytest tests/
```

The tests verify the `train()` wiring without launching MAME — they build the extractor and a PPO policy on the environment's real spaces and check shapes and action validity. `pytest` is the only dev dependency not already in `pyproject.toml`.

## Layout

| Path | Role |
|------|------|
| `daggorath_agent/train.py` | The `train()` pipeline — env -> reward -> VecEnv -> PPO |
| `daggorath_agent/feature_extractor.py` | `DaggorathFeaturesExtractor` — CNN over the map, MLP over the flat channels |
| `daggorath_agent/wrappers.py` | `CastScalarsWrapper` — widens the uint16 scalars to int32 so torch can ingest them |
| `tests/test_train.py` | Smoke tests for the `train()` wiring — extractor shape and a valid PPO action, no MAME |
| `pyproject.toml` | Package config and dependencies |
| `docs/3_decisions/` | Implemented concepts — pipeline, extractor, observation wrapper, reward, watch-training, persist-learning |
| `docs/concepts.md` | The concepts behind the decisions — `VecEnv`, activations, torch dtypes |
| `docs/findings/` | Hard-won operating lessons — pip tooling, WSL CUDA, stdout buffering |
| `docs/1_discussions/` | Open questions and not-yet-decided ideas |
| `docs/2_plans/watch-training.md` | Feature plan — the remaining `-video none` headless enforcement |
| `docs/2_plans/persist-learning.md` | Feature plan — the remaining `play.py` |
| `docs/1_discussions/curriculum.md` | Curriculum — course ordering and rewards, open discussion |

## Why the wrappers and extractor live here

Two adaptations are trainer-specific, so they belong in this package, never the environment:

1. **`CastScalarsWrapper`** — the environment's `scalars` channel is `uint16`, and torch has no `uint16` tensor type, so Stable-Baselines3 would crash on it. The wrapper widens it losslessly to `int32`. The environment stays trainer-agnostic.
2. **`DaggorathFeaturesExtractor`** — the observation is a `Dict` whose `map` channel is a two-plane image and whose other five channels are flat arrays. The extractor routes the map through a small CNN (stride-2 convolutions, no pooling) and the rest through an MLP, then concatenates.

Deferred: a joint action-mask policy for the INCANT verb form (see the deployment decision). For now plain PPO relies on the environment's no-op fallback for invalid INCANT pairs.

## Documentation

Documentation lives under `docs/`:

- **`docs/3_decisions/`** — implemented concepts: the training pipeline, feature extractor, observation wrapper, reward, watch-training, and persist-learning, each with its decision and reasoning.
- **`docs/concepts.md`** — the expanded concepts behind those choices: what `VecEnv` is, why activations exist, what a stride does.
- **`docs/findings/`** — hard-won operating lessons: pip tooling, WSL CUDA, stdout buffering.
- **`docs/1_discussions/`** — open questions and ideas not yet decided (pre-planning), including `curriculum.md` (course ordering and rewards).
- **`docs/2_plans/`** — what remains: `watch-training.md` (the `-video none` enforcement) and `persist-learning.md` (`play.py`).

This is intentionally lighter than the gym package's docs (`2_plans/`, `3_decisions/`, `findings/`), which reflect months of reverse-engineering. The harness documents itself in these files, and `docs/2_plans/` grows as new features are scoped.
