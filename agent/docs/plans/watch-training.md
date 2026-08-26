# Watch Training — Plan

_How a user runs training while watching the agent play in the MAME window. This is a feature plan, kept separate from [design.md](../design.md), which records the current reference trainer._

## Purpose

Expose a single, obvious way to express the intention "train while I watch." Today `train.py` is hardcoded headless (`MameConfig(window=False, sound="none")`), so there is no affordance for watching. The intent — watching — should be one token on the command line, not two flags the user must remember to pair.

## Interface

```
python -m daggorath_agent.train                          # default: headless, no window, silent
python -m daggorath_agent.train --watch                  # windowed + sound — the watch-training experience
python -m daggorath_agent.train --watch --sound none     # windowed but silent (dodges WSLg jitter)
python -m daggorath_agent.train --total-timesteps 25000  # bound the run length
```

- `--watch` is the intention: it sets `window=True` and `sound="sdl"` together.
- `--sound` is an optional override for `--watch`; it otherwise follows the watch default.
- `--total-timesteps` passes through to `learn()`.

## Under the hood

### `make_env(window, sound)`

`make_env()` gains two parameters and forwards them into `MameConfig`. The default remains the current headless behavior (`window=False`, `sound="none"`) so the library form of `train()` is unchanged.

### `train()` forwards playback

`train(total_timesteps, seed, window=False, sound="none")` forwards the two knobs to `make_env()` and passes `total_timesteps` to `model.learn()`. It stays the library-callable entry point.

### `__main__` parses the flags

A minimal argparse block maps the three flags onto `train()`. `--watch` expands to `window=True, sound="sdl"`; an explicit `--sound` overrides.

## Where training goes — checkpoints

Training currently goes nowhere: `learn()` returns the model in memory and the run ends, dropping the weights. That must stop for "the current level of training" to mean anything reloadable.

- Checkpoints land in **`daggorath-agent/checkpoints/`**, gitignored. Weights are large generated binaries, not source.
- A **checkpoint callback** snapshots periodically during `learn()` so a long run is not all-or-nothing.
- A final `model.save("checkpoints/ppo-daggorath")` writes the definitive copy.

This checkpoint is also the reloadable definition of "current level of training," enabling a later `play.py` that loads it and watches playback without training.

## What "watching" actually is

MAME's own window is the rendering; there is no separate Gym `render()`. With `window=True`, the MAME window appears, and because each `env.step()` blocks on `recv()` at the game's real-time frame rate, the emulator advances at native speed — the agent is watched acting as it learns.

Note: `window=False` today only omits `-window`; the launch does not emit `-video none`, so "headless" is not strictly enforced under WSLg. Enforcing it properly (`-video none`) is a separate change, out of scope here.

## Pacing caveat

Training is paced by MAME running the CoCo 3 in real time, so one environment step ≈ one real-time frame. This is slow by reinforcement-learning standards, but it is what makes watching meaningful. Accelerating MAME (`-throttle 0` / frame-skip) is a separate, careful change because it alters gameplay timing.

## Scope

This plan covers **`train.py` only** plus a `.gitignore` for `checkpoints/`:

- parameterize `make_env(window, sound)`,
- forward those knobs through `train()`,
- add checkpoint persistence (periodic + final save),
- add the `--watch` / `--sound` / `--total-timesteps` CLI,
- add `daggorath-agent/.gitignore` for `checkpoints/`.

`play.py` (load a checkpoint and watch playback without training) is a separate, later plan.

## Decisions

- **`--watch` is the intention; `--sound` is the escape hatch.** The common case is one flag. The edge case (WSLg audio jitter) is an override, not part of the normal invocation.
- **Checkpoints are gitignored artifacts.** They are not source; they must never be committed.
- **`window=True` is "watching."** There is no `-video none` today, so the only reliable way to watch is to request the window explicitly.