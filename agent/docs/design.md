# Daggorath Agent — Design Reference

_What this package is, why it's built this way, and what remains deferred. The audience is someone reading `daggorath-agent` as the reference trainer for the Daggorath Gym environment. For the expanded concepts behind these choices (what `VecEnv` is, why activations exist, what a wheel is), see [learnings.md](learnings.md)._

## Purpose

`daggorath-agent` is an installable package, but it is a **reference implementation, not a general-purpose library**. It answers the question the environment deliberately leaves open: *how do I actually train against this thing?* The environment exposes a `Dict` observation and a factored `MultiDiscrete` action; this package wires those into a working Stable-Baselines3 PPO run that an external user can read and adapt to their own stack. It is editable-installed alongside `daggorath-gym` so the two develop together, and it declares its dependencies in `pyproject.toml` rather than a `requirements.txt` — but its purpose is still to be read and adapted, not to serve as an install-anything dependency of a larger system.

## The training pipeline

The whole job is one function, `train()` in `train.py`:

```
train()
    → build the environment headless
    → apply the reward wrapper
    → widen the uint16 scalars to int32
    → wrap in a single-slot vector environment
    → train PPO
```

Concretely, `make_env()` layers three objects:

1. **`DaggorathEnv(mame_config=MameConfig(window=False, sound="none"))`** — the raw environment, built headless. MAME is not started here; it starts only on `reset()`.
2. **`DaggorathRewardWrapper`** — the environment's shipped default reward. It reads the true, ungated state through the environment's `current_state` property and replaces the environment's `0.0` placeholder with a real scalar. The reward is an explicit opt-in, never a second registered id — the world and its worth stay separate.
3. **`CastScalarsWrapper`** — widens the observation's `uint16` scalars to `int32` (details below).

`train()` then wraps that in **`DummyVecEnv([make_env])`** — the single-process vector-environment implementation inside Stable-Baselines3. A brief why: SB3's algorithms accept only the `VecEnv` interface, not a bare `gym.Env`, so even a single environment must be wrapped; `DummyVecEnv` is the one-slot implementation, `SubprocVecEnv` would be multiprocessing overhead for N = 1. See [learnings.md](learnings.md) for what `VecEnv` actually is.

Finally it constructs:

```
PPO(
    "MultiInputPolicy",
    vector_env,
    policy_kwargs={"features_extractor_class": DaggorathFeaturesExtractor},
)
```

`MultiInputPolicy` is the built-in policy for `Dict` observations; the custom extractor tells it how to read that `Dict`.

## The feature extractor

The observation is a six-channel `Dict`. Five channels are flat (`scalars`, `hands`, `pack`, `creatures`, `objects`); one — `map` — is spatial, a two-plane image `(2, 32, 32)` carrying the maze edge bytes and the per-cell feature bytes.

The default extractor would flatten everything into an MLP. `DaggorathFeaturesExtractor` instead applies the **CNN + MLP split**:

- The **CNN branch** reads `map`, downsampling with stride-2 convolutions (learned shrinks, no pooling) and finishing with a `Flatten`.
- The **MLP branch** reads the five flat channels, flattened and concatenated.
- The two branches are **concatenated** and projected to a single feature vector (`features_dim=256`).

Why a custom extractor at all: SB3's built-in one routes a channel to a CNN only when its shape reads as an image — a 3-D channel with 1 or 3 channels. Our `(2, 32, 32)` map has two channels and would fall through to the MLP, so the custom extractor re-implements that routing decision. Two implementation notes:

- `scalars` is `uint16` and every other channel `uint8`; the extractor casts to `float` before use.
- The CNN output width is **measured from a synthetic forward pass** in `__init__` rather than hand-computed, so the final projection's input width is exact by construction.

## The observation wrapper

`CastScalarsWrapper` widens the `scalars` channel from `uint16` to `int32` and mirrors the change in the observation space.

The reason is specific to torch: **torch has no `uint16` tensor type**, and SB3's `torch.as_tensor` conversion raises on it, crashing before the extractor sees the data. Widening to `int32` is lossless (values range 0–65535) and leaves every other channel (`uint8`, which torch accepts) untouched. This is the one adaptation made purely to fit SB3's tensor types.

## Why these components live agent-side

The boundary is deliberate and matches the deployment design:

- **The environment reports; the trainer adapts.** `daggorath_gym` stays trainer-agnostic — it imports `gymnasium` and `numpy` only. Anything that exists to fit a specific training library (the `uint16 → int32` cast, the `MultiInputPolicy` extractor) belongs in `daggorath-agent`.
- **The reward is a valuation, not a fact.** The environment's `step()` returns `0.0`; the wrapper assigns worth. A trainer may supply its own wrapper instead — the shipped one is the default, not the only answer.
- **The world and its worth stay separate.** There is exactly one registered concept — the raw environment. The reward wrapper and the extractor are opt-ins layered on top, never baked in.

## Deferred work

- **Joint action masking.** The action space is `MultiDiscrete([26, 31])` — a command template and an object specifier. The INCANT template is valid only with the nine ring specifiers. SB3's per-axis masking cannot express that cross-axis constraint, so a joint-mask policy belongs here as a custom policy. It is deferred: the environment's `derive_command_index` returns `None` for an invalid INCANT pair and `step()` treats it as a no-op, so plain PPO runs correctly and merely wastes the occasional step. Only about 2.7% of the 806 combinations are invalid.