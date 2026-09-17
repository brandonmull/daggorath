# Combat Detection

_16 Sep 2026_

## Decision

The creature record (`C`) gains two true-state fields per slot: `damage` (slot + 10) and `strength` (slot + 0), each two bytes little-endian on the wire. A slot now ships eight bytes, the four perceived fields (`alive`, `type`, `X`, `Y`) first, then `damage` and `strength`. Both stay true-state: the player never sees a creature's hitpoints or raw strength, so the perceived `creatures` channel keeps its four fields.

`damage` is the decisive field. It rises when a hit lands, which is the "changed" the fighting-monster experiment watches. `strength` is the creature's max hitpoints and also the kill reward, so a trace reading can grade how hard a hit was, damage moved against strength, without re-deriving it from the type token.

## Why

- **A non-lethal hit must be observable.** A death is visible (alive → dead), but a hit that does not kill moves nothing on the four-field record. The experiment's control is "an attack with nothing in range changes nothing," and its test is "an attack that connects changes a combat field." `damage` is the field that changes.
- **Extend the `C` record, not a separate record.** The single-pass scan and one channel are the existing extension point. A separate engaged-creature record would add a tag, a snapshot, and a parse path for one experiment's needs.

## What Changed

- `emulation/plugins/daggorath/state.lua` — `_sampleCreatures` reads `damage` and `strength` after the four perceived fields.
- `daggorath_gym/state.py` — `CREATURE_FIELDS` 4 → 8, `CREATURE_BYTES` 128 → 256; `decode_creatures` returns the 8-field slots, and `as_perceived` keeps the first four.

## Reference Documents

| Document | What it contains |
|---|---|
| `../1_discussions/combat-detection.md` | The discussion this follows |
| `../references/game/ram.md` | The creature array layout, the `strength` and `damage` slots |
| `../../../docs/game/combat-model.md` | The strength-vs-damage combat model |
| `../../../agent/sandbox/command-latency/fighting-monster/README.md` | The experiment these fields serve |
