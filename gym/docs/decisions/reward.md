# Reward

_1 Sep 2026_

## Decision

Reward is an agent-side wrapper, not the environment: it reads the true state through `current_state` and collapses three layers — spikes, potentials, information gain — plus a reject penalty into one scalar per step. Coefficients: win +1.0, death −1.0, discovery +0.1, advance +0.01, survival γ·Φ(s′) − Φ(s) with Φ = `player_strength − m0221`, γ = 0.99.

## Why

- **Fact vs. valuation.** The environment reports facts and returns `0.0`; the reward is a valuation the trainer brings. The policy never sees true state; the reward is supposed to.
- **"Almost everything counts" — and stays safe via potential-based shaping.** Define Φ(state) = "how good is this situation now," and pay γ·Φ(s′) − Φ(s). It densifies the gradient without ever changing the optimal policy, unlike sprinkling arbitrary bonuses.
- **Light is a proxy; combat and heart are one signal.** Reward torch minutes, not `ambient_light` (which jumps on the Wizard's death). And penalize the survival margin `player_strength − m0221`, not raw heart rate — attacking raises exertion exactly like being hit, so a heart-rate penalty would punish the fighting that wins.
- **Advance vs. discovery.** A dense per-cell trickle pays locomotion; a sparse structural term pays salient features (junction, door, dead end). Discovery dominates; advance is small — discovery alone is too sparse, advance alone is cell-counting.
- **Information gain is novelty-bounded.** Pay the first unknown→known transition only, or the agent stands still and stares at what it already knows.

## What Changed

- `daggorath_gym/reward.py` — `DaggorathReward` (spikes, survival potential, advance, combat novelty, reject penalty) and `DaggorathRewardWrapper`.
- Deferred: structural discovery, reveal/seen/heard novelty, and the six remaining potentials.
