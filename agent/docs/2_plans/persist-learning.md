# Persist Learning — Plan

_What remains: loading a checkpoint to watch playback without training._

## Remaining

`play.py` — load a checkpoint and watch the trained agent act, with no further training:

```
python -m daggorath_agent.play --model checkpoints/ppo-daggorath
```

Builds the environment windowed via `make_env(window=True, sound="sdl")`, then loops `reset → predict → step` for `--episodes`. Default is deterministic action selection; `--sound none` dodges the WSLg jitter.

## Reference

- Implemented: `../3_decisions/persist-learning.md`
