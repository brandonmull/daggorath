# State Field Verification

## Goal

Prove the production `state.lua` sampler retrieves the new state fields from the right addresses, with the right byte order, and that the torchPtr dereference actually follows the pointer. Fields under test here: `m0221` (`0x0221`), the two ambient-light components (`0x0226:0x0227`), and the lit-torch entry's special data (`minutes` / `physical_light` / `magic_light`, read through `torchPtr` `0x0224:0225` into the `O` record). `effective_light` is verified separately in `torch-light/` (it is recomputed by the game, not directly pokable).

## Status

Built and passing.

## Approach

Rather than re-implement the sampler, the plugin `require`s the production `daggorath/state` module unmodified and points its output at a log file (the module's `beginWatching` accepts any file handle with `:write`/`:flush`). The plugin then:

1. Auto-primes the keyboard at frame 300 (demo→live transition).
2. On the first frame of live play (`displayFunction == 0xCE66`), pokes known values into RAM:
   - `torchPtr` → one slot past `nextObjSlot` (a free object slot)
   - torch minutes = 100, physical light = 7, magic light = 3 (at `torchPtr + 6/7/8` — the lit-torch entry's special data)
   - `ambient_light_physical` = 1, `ambient_light_magical` = 2 (`0x0226:0x0227`)
   - `m0221` = 0x0A0B (`0x0221:0x0222`)
3. The production sampler reads those values on the following frame and writes tagged records.

The Python server decodes the records with the production `DaggorathState` deserializer and asserts each poked value round-trips.

## Success criteria

- The lit-torch record reports `minutes == 100`, `physical_light == 7`, `magic_light == 3` — the torchPtr dereference reads the right offsets.
- `ambient_light_physical == 1`, `ambient_light_magical == 2`, and `m0221 == 0x000A` are observed — direct addresses and big-endian→little-endian byte order are correct.

The torchPtr-equals-zero case (the lit-torch entry reads 0xFF identity and zero light) is covered by a fresh boot: with no torch lit, `torchPtr == 0` and the entry already reports that (confirmed in a live sample, not re-run here).

## Running

```bash
python sandbox/state-field-verification/server.py
```
