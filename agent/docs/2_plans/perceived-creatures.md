# Perceived Creatures — Plan

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The environment ships the perceived `creatures` channel as 32 slot-aligned rows, one per slot in the game's creature array, each carrying `alive`, `type`, `X`, `Y`. Slot order is instance identity, so the same situation permutes across rows and the policy must learn an order that carries no meaning. This plan adds an agent-side wrapper that compacts the channel to 8 rows and orders them canonically, reducing that permutation before the feature extractor sees it.

The scope is the agent's presentation of perceived creatures only. The environment's perceived channel and true state are unchanged: the 32-row channel is still what the environment reports, and the wrapper reshapes it. This follows the boundary drawn in `../1_discussions/perceived-creatures.md` and `../1_discussions/perception-shaping.md`: the environment reports perception whole, and shaping is the agent's imperative concern.

## The wrapper

A new wrapper, `CanonicalCreaturesWrapper`, sits with the existing observation wrappers in `daggorath_agent/wrappers.py`. It consumes the perceived observation's `creatures` channel and returns the same Dict observation with that channel reshaped to 8 rows. A module constant `CREATURE_CHANNEL_SLOTS = 8` bounds the reshaped channel, matching the pack and floor-object caps.

The wrapper updates the observation space's `creatures` Box from 32 rows to 8 rows, so the space and the reshaped observation stay consistent.

## The ordering

Visible creatures are ordered by danger, most dangerous first. The wrapper holds that ranking as an explicit constant, `CREATURE_POWER_ORDER`: a tuple of type tokens from Wizard (0x0B) down to Spider (0x00), the game's own spawn order ("start with most powerful"). Within a type, the incoming row index ascending breaks the tie.

The type column already in the perceived channel supplies each creature's power. The wrapper maps the token through `CREATURE_POWER_ORDER` to a rank and sorts by that rank, the same way the reward wrapper holds its valuation rather than asking the environment for it. The constant is the explicit expression of power at the customization interface: a developer reads and edits the tuple, so the ranking is documented where it lives instead of hiding in a descending byte comparison.

```
CanonicalCreaturesWrapper.observation()
    → reads the perceived creatures channel (32 rows)
    → keeps rows whose alive byte is nonzero
    → sorts the kept rows by CREATURE_POWER_ORDER rank, then by incoming row index ascending
    → takes the first CREATURE_CHANNEL_SLOTS rows
    → writes each as alive, type, X, Y
```

## Where it lands

- `daggorath_agent/wrappers.py` — `CanonicalCreaturesWrapper`, `CREATURE_CHANNEL_SLOTS`, and `CREATURE_POWER_ORDER`.
- The environment is unchanged: `daggorath_gym` keeps reporting the 32-slot perceived channel and the 32-slot true-state `C` record.

## Open questions

- Whether 8 is enough, settled by a trace of the maximum simultaneously visible count.
- The same-type tie-break. Incoming row index is accepted for now; distance and angle could refine it later.
- The scorpion wrinkle: token order ranks scorpion (0x06) above hatchet-giant (0x05) despite lower raw strength, accepted as the game's own ranking.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/perceived-creatures.md` | The discussion this plan follows |
| `../1_discussions/perception-shaping.md` | The agent-side shaping boundary |
| `../3_decisions/observation-wrapper.md` | The existing wrapper decision this extends |
| `../../../gym/docs/2_plans/creatures.md` | The creature array and the 12-type catalogue |
| `../../../gym/docs/3_decisions/perception.md` | The environment's perceived state, the objective whole |
| `../../../docs/game/combat-model.md` | The strength-vs-damage model and type strengths |
