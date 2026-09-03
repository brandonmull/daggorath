# Observation Wrapper

_1 Sep 2026_

## Decision

`CastScalarsWrapper` widens the observation's `scalars` channel from `uint16` to `int32` and mirrors the change in the observation space. Every other channel is `uint8` and passes through untouched.

## Why

- **torch has no `uint16` tensor type.** SB3's `torch.as_tensor` conversion raises on `uint16`, crashing before the extractor runs. Widening to `int32` is lossless (values are 0-65535) and leaves the rest alone.
- **It lives agent-side.** The environment stays trainer-agnostic; the one adaptation made purely to fit SB3's tensor types belongs in the agent, never in `daggorath_gym`.

## What Changed

- `daggorath_agent/wrappers.py` — `CastScalarsWrapper`.
