# Causal Diff

## Goal

Verify the state diff and the primitive-field choice against the torch-lighting event's known mechanics: drive the real environment through `PULL LEFT TORCH` → `USE LEFT`, diff the perceived scalars and hand slots before and after each command, and confirm the `USE` diff recovers "light the torch" as one primitive cause, with every other change reported as noise.

## Status

Built and passing.

## Approach

No RAM poking and no new Lua plugin: the driver uses the production `DaggorathEnv` exactly as the agent will, reading the perceived observation (never `current_state`).

1. Boot to live play; record the baseline — `torch_physical_light` is 0 (no lit torch).
2. Send `PULL LEFT TORCH`; step no-op frames until a hand holds the torch (the perceived `hands` channel). Diff the hands — a hand now holds the torch — and the scalars, expecting no torch field to change.
3. Send `USE LEFT`; step until the torch lights (`torch_physical_light` goes above 0). Diff the scalars.
4. Classify each changed field as cause or noise; assert the success criterion.

## Expected values (Pine torch, ROM `ObjectSpecial` @ `DA84: 0F 0F 07 00`)

| Field | Before | After USE |
|---|---|---|
| `torch_physical_light` | 0 | 7 — the single primitive cause |

The burn-down timer (`torch_minutes`) also flips 0 → 15 when the torch lights, but the probe treats it as noise — like the heartbeat and tiredness, it moves on its own as the minutes tick.

The diff reads the *perceived* scalars, not true state. Perceived and true are identical here — they are the player's own frame, shipped ungated — but perceived is the substrate the causal chain will build on, and the boundary keeps learning on the perceived side and valuation on the true side.

## Success criteria

- After `PULL`, a hand holds the torch.
- After `USE`, the torch's light is on: the `USE` diff shows `torch_physical_light` going 0 → N as the single cause.
- The `PULL` diff shows no torch-field change (the torch moves via the object channel, not the scalars).
- Unrelated fields that also change — the heartbeat, the tiredness, the burn-down timer — are reported as noise, not as failure.

## Running

```bash
python agent/sandbox/causal-diff/server.py
```