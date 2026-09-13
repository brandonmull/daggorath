# Combat Detection — Discussion

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Is the "near creature" a fact to ship, or a fact to derive?

The causal-timing sandbox's second experiment, [`fighting-monster`](../../../agent/sandbox/causal-timing/fighting-monster/README.md), must tell a connecting attack from a miss. Its watched fields name a "near creature" — `nearCreatureType`, `nearCreatureDY`, `nearCreatureDX`, `nearCreatureStrength`, `nearCreatureDamage` — but the environment ships no such fact. This is the question of whether to add it, and where it would come from.

The disassembly answers the "where" first. The attack command keeps no fixed "near creature" register; it calls `GetCreatureAt` on the player's cell and, if a creature is there, fights it. So the "near creature" is just the creature slot at the player's cell, and its type, position, strength, and damage are the ordinary array slots (`type` slot + 13, `X`/`Y` slots + 15/16, `strength` slot + 0, `damage` slot + 10).

The creature record already ships type and position, so `nearCreatureType` / `nearCreatureDY` / `nearCreatureDX` are derivable from the `C` record and the player's cell. What it does not ship is `strength` and `damage` — deliberately, because the player gets no health bar. A death is still visible (alive → dead), but a hit that does not kill is not: nothing on the wire moves when damage rises. That is exactly the miss the experiment must catch, because its control is "an attack with nothing in range changes nothing," and its test is "an attack that connects changes a combat field."

So the question narrows to strength and damage: are they worth shipping as true-state facts, so a non-lethal hit is observable, or does the experiment make do with the death signal alone?

## Open questions

- **Which fields.** Is `damage` (slot + 10) alone enough to say "a hit landed," or is `strength` (slot + 0) also needed — and does the experiment care how hard the hit was?
- **Where.** Extend the `C` record with two more bytes per slot, or ship a separate record for the engaged creature alone?
- **Perceived or true-state.** Strength and damage are the player's no-health-bar facts, so they would be true-state — but confirm the boundary holds for the creature the player is actively fighting.

## Reference

- Plan: `../2_plans/combat-detection.md`
- `gym/docs/references/game/ram.md` — the creature array layout and `creatureCounts`
- `gym/docs/references/game/code.md` — `GetCreatureAt`, the attack path, and the kill path
- `docs/game/combat-model.md` — the strength-vs-damage combat model
- `../../../agent/sandbox/causal-timing/fighting-monster/README.md` — the experiment this feeds
