# Perceived Creatures — Discussion

_How the agent should present the creatures it perceives: what the 32-slot channel names, why its order is arbitrary, and what canonical shape reduces that arbitrariness. This records the argument that reached the plan in `../2_plans/perceived-creatures.md`._

## What does the 32-slot channel actually name?

The channel looked settled until its shape was read closely, and the reading raised the question of what a slot stands for. The exchange established the flaw and the payoff of fixing it:

> **the observation** — "A different instance of the same monster will make the channel data appear differently."
>
> **the answer** — "Slot index is instance identity, not semantic identity. One spider in my cell reads differently depending on whether it occupies slot 3 or slot 19, and the policy has to learn that slot order is meaningless."

A slot is a position in the game's creature array, not a property of the monster. The same kind of creature can sit at any of the 32 slots, so one situation permutes across the rows and the policy is forced to learn an ordering that carries no meaning.

## What should replace the 32-slot layout?

The flaw prompted a first proposal for the channel's shape. The exchange previewed the benefit and the fork the proposal opened:

> **the proposal** — "I think maybe the creature channel of the perceived state should be limited to 8 slots and show monsters in order of appearance."
>
> **the doubt** — "First, what order of appearance means. If it's first-seen time, the environment becomes stateful. If it's a stateless sort instead, the order is recomputed each frame. Second, the cap needs a drop policy."

Eight slots matches the pack and floor-object caps, but "order of appearance" has two readings: a temporal order that needs memory of what was seen first, or a stateless order that is recomputed from the visible set each frame.

## What orders the compressed channel?

The temporal reading was set aside in favor of the simplest stateless order. The exchange named what that order actually is:

> **the proposal** — "We just insert visible monsters to perceived channel in order of index."
>
> **the answer** — "Packing the visible creatures into 8 slots in array-index order is a compression of the current channel, not a reordering. The ordering key is still the game's arbitrary slot index, so the cross-episode permutation problem stays."

Index order is the 32-slot channel with the empty rows removed. It shrinks the surface, but it inherits the arbitrary slot index as its ordering key, so the same situation still permutes across episodes.

## What does index order preserve?

A claim about continuity had to be corrected before the next step was clear. The exchange separated what index order preserves from what it does not:

> **the objection** — "It doesn't stay. The same monster with a different index shows up at the top of the list, and different monsters show up in the same order as originally perceived."
>
> **the correction** — "The array index is stable within one level until death, but that's instance identity, not monster identity. Index order is just the current 32-slot channel with the empty slots removed; the visible survivors keep their relative array order."

Within one level a creature keeps its slot, but across levels and sessions the same kind of creature can take any slot. Index order preserves the relative order of the currently visible set, not a stable name for any one monster.

## What makes an ordering canonical?

With identity ruled out, the question turned to what would make the order stable. The exchange produced the ordering that settles it:

> **the proposal** — "We need a canonical ordering. Let's always list the most dangerous monster at top, still in index order per type."
>
> **the agreement** — "Danger rank is a function of type, which is stable, so a knight always sits above a spider regardless of the array indices. Index then breaks ties only within a type, and same-type creatures are interchangeable."

Sorting by danger first, then by index within a type, gives an order that is stable by type across episodes. The index tie-break only orders instances that are interchangeable anyway, so its arbitrariness carries no semantic difference.

## What counts as danger?

Danger had to be defined before the ordering could be built. The exchange found the definition already present in the game:

> **the question** — "Oh, the game has its own power ranking? Let's just use that as a proxy for danger, as long as the ordering is stable somehow by type."
>
> **the answer** — "The type token itself is the game's ranking. The level-spawn loop walks from 0x0B down to 0x00, start with most powerful, so higher token means more powerful. Sort visible creatures by type descending, then by array index ascending within a type."

The type token is the game's own power ordering, so no new table is needed. Descending token order puts the Wizard at the top and the Spider at the bottom; the scorpion's strength inversion is accepted as part of the game's ranking.

## Where does the ordering belong?

The ordering was settled as a shape, and then its ownership was corrected. The exchange placed it on the agent's side of the boundary:

> **the correction** — "Since this is a matter of perception, it should be the job of the agent to construct the shape and order of information. The environment should still report which monsters are perceived using the 32-slot channel; the agent should modify this shape and contents to reduce permutation."

The environment keeps reporting the honest, slot-aligned perceived channel. Compacting it to eight slots and sorting it by danger is a shaping of information for the policy, which is the agent's concern — the same boundary `perception-shaping.md` draws for every channel.

## Reference

- Plan: `../2_plans/perceived-creatures.md`
- `perception-shaping.md` — the agent-side shaping boundary this follows
- `../../../gym/docs/2_plans/creatures.md` — the creature array and the 12-type catalogue
- `../../../gym/docs/3_decisions/perception.md` — the environment's perceived state, the objective whole
- `../../../docs/game/combat-model.md` — the strength-vs-damage model and type strengths
