# Combat Detection

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The command-latency sandbox's `fighting-monster` experiment needs to see a hit land, not just a death — its control is "an attack with nothing in range changes nothing," and its test is "an attack that connects changes a combat field." The discussion in `../1_discussions/combat-detection.md` narrows that to two creature-array fields the `C` record omits: `damage` (slot + 10) and `strength` (slot + 0), the player's no-health-bar facts.

The scope is to put those on the wire as true-state facts, so a non-lethal hit is observable. The decisions below settle the discussion's open questions.

## What is sampled

The creature array is already scanned single-pass into the `C` record — `alive`, `type`, `X`, `Y` per slot. The plan adds the creature's `damage` (slot + 10) and `strength` (slot + 0) to that scan, each two bytes, so each slot ships eight bytes instead of four: the four perceived fields first, then `damage` and `strength` as two little-endian bytes each, matching the scalar wire convention. Both are true-state: the player never sees a creature's hitpoints or raw strength, so they do not reach the perceived `creatures` channel, which keeps its four fields; the sandbox reads them through the environment's true state.

`damage` is the decisive one — it rises when a hit lands, which is the "changed" the experiment watches. `strength` is the creature's max hitpoints and also the kill reward, so the trace reading can grade how hard a hit was (damage moved against strength) without re-deriving it from the type token.

## Decisions

- **Ship both fields.** `damage` is the hit signal; `strength` grades the hit against the creature's max hitpoints. The parent harness's shared signal set already names both, and the trace is read after the run, so grading costs nothing at record time.
- **Extend the `C` record, not a separate engaged-creature record.** The single-pass scan and one channel are the existing extension point. A separate record would add a tag, a snapshot, and a parse path for one experiment's needs.
- **Both stay true-state.** The perceived `creatures` channel keeps exactly four fields — `alive`, `type`, `X`, `Y` — and excludes `damage` and `strength` even for the creature the player is actively fighting.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/combat-detection.md` | The discussion this plan follows |
| `../2_plans/creatures.md` | The creature array scan this extends |
| `gym/docs/references/game/ram.md` | The creature array layout — `strength` and `damage` slots |
| `docs/game/combat-model.md` | The strength-vs-damage combat model |
| `../../../agent/sandbox/command-latency/fighting-monster/README.md` | The experiment these fields serve |
