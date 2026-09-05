# The Causal Diff

## One cause, the rest noise

Lighting a torch has a single primitive cause — `torch_physical_light` (0 → 7). The burn-down timer `torch_minutes` flips 0 → 15 at the same instant but then ticks down on its own, so it is noise, not a readout to assert — the same bucket as the heartbeat and tiredness. The once-assumed readout `effective_light_physical` is not part of the event at all.

## Channels, not just scalars

A diff over the nineteen scalar fields misses the event's first step. PULL moves the torch from pack to hand, and that change lives only in the `hands` channel — `[0xFF, 0xFF] -> [29, 0xFF]`, PINE TORCH revealed as specifier 29 — not in any scalar. The probe reported "no scalar fields changed" and lost the step. The causal diff must span the perceived channels — hands, pack, objects — not just the scalars.
