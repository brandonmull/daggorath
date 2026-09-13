# Causal Diff

## Goal

Verify the state diff and the cause/effect split against the torch-lighting event's known mechanics: drive the real environment through `PULL LEFT TORCH` → `USE LEFT`, diff the perceived scalars and hand slots before and after each command, and confirm the `USE` diff recovers "light the torch" as one perceived effect (`effective_light_physical` rising) backed by a true-state cause (the lit torch's own light), with every other change reported as noise.

## Status

Built and passing.

## Approach

No RAM poking and no new Lua plugin: the driver uses the production `DaggorathEnv` exactly as the agent will. The perceived diff reads the observation's `scalars`; the primitive cause reads true state through `current_state` (the lit-torch object record).

1. Boot to live play; record the baseline — `effective_light_physical` is 0 (dungeon dark).
2. Send `PULL LEFT TORCH`; step no-op frames until a hand holds the torch (the perceived `hands` channel). Diff the hands — a hand now holds the torch — and the scalars, expecting no light change.
3. Send `USE LEFT`; step until the dungeon brightens (`effective_light_physical` goes above 0). Diff the scalars.
4. Classify each changed field as effect or noise; assert the success criteria.

## Expected values (Pine torch, ROM `ObjectSpecial` @ `DA84: 0F 0F 07 00`)

| Fact | Where | Before | After USE |
|---|---|---|---|
| `effective_light_physical` | perceived scalars | 0 | 7 — the single perceived effect |
| the lit torch's physical light | true state (`lit_torch[4]`) | 0 | 7 — the primitive cause |

The burn-down timer (`lit_torch[3]`, minutes) also flips 0 → 15 when the torch lights, but the probe treats it as noise — like the heartbeat and tiredness, it moves on its own as the minutes tick.

The perceived diff reads the `scalars` channel; the cause reads the true state's `lit_torch`. Perceived and true diverge here on purpose — the player sees the dungeon brighten, not the torch's own light number — so the probe checks both sides of that boundary.

## Success criteria

- After `PULL`, a hand holds the torch.
- After `USE`, the dungeon brightens: the `USE` diff shows `effective_light_physical` going 0 → N as the single effect.
- The true-state lit torch reports its physical light on (0 → 7), the primitive cause.
- The `PULL` diff shows no light change (the torch moves via the object channel, not the scalars).
- Unrelated fields that also change — the heartbeat, the tiredness, the burn-down timer — are reported as noise, not as failure.

## Running

```bash
python agent/sandbox/causal-diff/server.py
```