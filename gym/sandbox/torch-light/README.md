# Torch Light

## Goal

Verify the torch ↔ light relationship end-to-end by *playing* the torch commands through the real command channel — `PULL LEFT TORCH` (take the Pine torch from the backpack), then `USE LEFT` (light it) — and checking that the torch and light RAM fields update as the game's own tables prescribe.

## Status

Built and passing.

## Approach

No RAM poking and no new Lua plugin: the driver uses the production `MameOperator` (command socket + state FIFO + screen decode) exactly as the agent will.

1. Boot to live play; record the initial state (torch fields all 0 — no lit torch).
2. Send `PULL LEFT TORCH`; read the command-area text until the echo appears (confirms the command was typed and accepted).
3. Send `USE LEFT`; read until the lit torch's physical light goes non-zero (confirms the torch lit).
4. Read until `effective_light_physical` reaches its recomputed value, then assert.

The player always starts with a Pine torch in the backpack (grammar: "a backpack containing a PINE TORCH and a WOODEN SWORD"), so the procedure is deterministic.

## Expected values (Pine torch, ROM `ObjectSpecial` @ `DA84: 0F 0F 07 00`)

| Field | Before | After USE |
|---|---|---|
| `lit_torch` minutes | 0 | 15 (14 if a minute ticked) |
| `lit_torch` physical light | 0 | 7 |
| `lit_torch` magic light | 0 | 0 |
| `effective_light_physical` | 0 | 7 |
| `effective_light_magical` | 0 | 0 |
| `ambient_light_physical` | 0 | 0 |
| `ambient_light_magical` | 0 | 0 |

The torch's fields are object data — the `O` record's lit-torch entry (class, proper, reveal, minutes, physical light, magic light) — not scalars. The three leaving 0 before USE and filling in after is the proof the sampler followed the now-non-zero `torchPtr` to the lit torch object.

## Success criteria

- The command area echoes `PULL LEFT TORCH` and `USE LEFT` (no `???`).
- After `USE LEFT`, the lit-torch record's minutes, physical light, and magic light match the Pine torch values, and `effective_light_physical` rises to 7.

## Running

```bash
python sandbox/torch-light/server.py
```
