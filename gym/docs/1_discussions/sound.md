# Sound — Discussion

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Open questions

- **Heartbeat audibility.** When does `hearHeart` clear — fainting, death, or never? Not traced.
- **Effect internals.** Each of the 23 sound routines is a small waveform program; their shapes are irrelevant if cues are derived, but they are not catalogued.
- **`m0261` semantics.** Identified as the volume register (was `??` in the RAM map), but its exact interaction with the DAC writes is not traced.
- **Corridor gate.** The disassembly appears to gate the approach sound to a 2-cell corridor (`min(|dx|,|dy|) ≤ 2`), but this contradicts lived experience of hearing creatures off-axis. Needs a sandbox to determine when approach sounds actually fire — a *separate experiment* from the navigation module's line-of-sight, in its own sandbox subfolder.

## Reference

- Plan: `../2_plans/sound.md`
