# Combat Detection

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The command-latency sandbox's `fighting-monster` experiment needs to see a hit land, not just a death — its control is "an attack with nothing in range changes nothing," and its test is "an attack that connects changes a combat field." The discussion in `../1_discussions/combat-detection.md` narrows that to two creature-array fields the `C` record omits: `damage` (slot + 10) and `strength` (slot + 0), the player's no-health-bar facts.

The scope is to put those on the wire as true-state facts, so a non-lethal hit is observable. This document is a pre-build spec; the open questions below must settle before implementation.

## What is sampled

The creature array is already scanned single-pass into the `C` record — `alive`, `type`, `X`, `Y` per slot. The plan adds the creature's `damage` and `strength` to that scan, so each slot ships six bytes instead of four. Both are true-state: the player never sees a creature's hitpoints or raw strength, so they do not reach the perceived `creatures` channel; the sandbox reads them through the environment's true state.

`damage` (slot + 10) is the decisive one — it rises when a hit lands, which is the "changed" the experiment watches. `strength` (slot + 0) is the creature's max hitpoints and also the kill reward, so it is needed only if the experiment wants to grade how hard a hit was; the discussion leaves that open.

## Open questions

- **Which fields.** Ship `damage` alone, or `damage` and `strength`?
- **Where.** Extend the `C` record with two bytes per slot, or ship a separate record for the engaged creature alone?
- **Perceived or true-state.** Confirm both stay out of the perceived `creatures` channel — the boundary holds for a creature the player is actively fighting.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/combat-detection.md` | The discussion this plan follows |
| `../2_plans/creatures.md` | The creature array scan this extends |
| `gym/docs/references/game/ram.md` | The creature array layout — `strength` and `damage` slots |
| `docs/game/combat-model.md` | The strength-vs-damage combat model |
| `../../../agent/sandbox/command-latency/fighting-monster/README.md` | The experiment these fields serve |
