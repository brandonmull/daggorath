# Daggorath Agent

The training harness for the [Daggorath Gym](../gym) environment. This is the reference end-to-end PPO trainer: it consumes `daggorath_gym` as a library and turns it into a working Stable-Baselines3 run.

The split is deliberate — the environment package imports no training library, and this package imports only what it needs to train. See `gym/docs/plans/deployment/plan.md` for the full design.

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
| `docs/design.md` | Design reference — pipeline, extractor, wrappers, deferred work |
| `docs/learnings.md` | Concepts and operating lessons — `VecEnv`, activations, wheels, and more |
| `docs/considerations.md` | Ideas and design considerations, not yet decided |
| `docs/plans/watch-training.md` | Feature plan — the `--watch` training interface and checkpoint persistence |
| `docs/plans/persist-learning.md` | Feature plan — checkpoint format, the load contract, `--resume` |
| `docs/plans/curriculum.md` | Curriculum plan — the staged ladder, reward channels, and command masking |

## Why the wrappers and extractor live here

Two adaptations are trainer-specific, so they belong in this package, never the environment:

1. **`CastScalarsWrapper`** — the environment's `scalars` channel is `uint16`, and torch has no `uint16` tensor type, so Stable-Baselines3 would crash on it. The wrapper widens it losslessly to `int32`. The environment stays trainer-agnostic.
2. **`DaggorathFeaturesExtractor`** — the observation is a `Dict` whose `map` channel is a two-plane image and whose other five channels are flat arrays. The extractor routes the map through a small CNN (stride-2 convolutions, no pooling) and the rest through an MLP, then concatenates.

Deferred: a joint action-mask policy for the INCANT template (see the deployment plan). For now plain PPO relies on the environment's no-op fallback for invalid INCANT pairs.

## Documentation

Documentation lives under `docs/`:

- **`docs/design.md`** — the design reference: the `train()` pipeline, the feature extractor and observation wrapper, the environment-vs-trainer boundary, and the deferred joint-mask policy. It records *what we use and a brief why*.
- **`docs/learnings.md`** — the expanded concepts and operating lessons behind those choices: what `VecEnv` is, why activations exist, what a wheel is, and the mistakes worth not repeating. It will grow as more is learned.
- **`docs/considerations.md`** — ideas and observations from working with the project that are not yet decided.
- **`docs/plans/`** — feature plans, including `watch-training.md` (the `--watch` interface), `persist-learning.md` (checkpoint format, the load contract, and `--resume`), and `curriculum.md` (the staged ladder and command masking).

This is intentionally lighter than the gym package's four-phase docs (`plans/`, `reviews/`, `decisions/`, `findings/`), which reflect months of reverse-engineering. The harness documents itself in these files, and `docs/plans/` grows as new features are scoped.
