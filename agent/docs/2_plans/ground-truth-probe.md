# Ground Truth Probe — Plan

_What this plan covers: one probe that verifies the state diff and the primitive-field choice against the game's known mechanics. What it does not cover: the causal chain itself — the representation, the stores, the contingency, the reasoning over it, and how the acting agent reads it — all of which remains open discussion in `../1_discussions/knowledge-and-reasoning.md`._

## Why the probe first

The causal chain is the goal, but it is not ready to build. The discussion that led here (`knowledge-and-reasoning.md`) left several questions open — what self-consistency concretely does, how reasoning over the chain is learned, how the value layer is represented, how overlapping masks unify, how the acting agent reads the store. Each of those is load-bearing for a real implementation, and none is settled.

The probe is the one step that does not wait on any of them. It needs no self-consistency, no reasoning, no value representation, no unification, no interface. It is just subtraction over a field list: does diffing the state before and after a command recover "light the torch" as one cause and two readouts, or as an undifferentiated three-field cluster?

The reason to check that first is that everything else stands on it. If the diff is noisy, or the primitive/derived split is wrong, then the causal chain cannot be built on top of it — no matter how the open questions are eventually answered. The probe is a foundation check: cheap, self-contained, and falsifiable, and it confirms or refutes the one assumption the rest of the work leans on.

The honest caveat: the probe validates the easy part. It does not move the hard questions — self-consistency, reasoning, the value layer — by an inch. Passing it means the foundation holds, not that the causal chain is near. The plan is scoped to the probe precisely so that "ready for the probe" is never mistaken for "ready for the causal chain."

The probe covers only the torch-lighting event. A full enumeration of primitive and derived fields across the whole state is out of scope here; it comes later, one case at a time, leaning on the split this probe confirms.

## The probe

Lighting a torch is a documented event, so it is known before any code runs what the diff *should* see: one cause and two readouts. The probe is a script that checks the diff sees that structure instead of a flat cluster.

The probe:

→ builds the environment
→ plays the scripted torch sequence — pull the pine torch, then use it
→ diffs the scalar fields before and after each command
→ reports, per command, which fields changed and to what

It is a falsifiable check, not the learner. It answers one question: does diffing the state over the right fields recover "light the torch" as one cause plus its readouts, or as an undifferentiated three-field cluster?

## Primitive vs derived

Lighting a torch changes three scalar fields, but they are not three independent causes:

- `torch_physical_light` — the cause: the torch's own light output, 0 before, N after
- `effective_light_physical` — a readout: visibility computed from the torch light, ambient, and geometry
- `torch_minutes` — a readout: the burn-down timer, started by the torch being lit

The disassembly is the authority for which is which; the probe confirms it empirically. The primitive fields are the diff scope; the derived readouts are what a naive diff would wrongly count as separate causes.

## Success criterion

The probe succeeds when the USE command's diff shows `torch_physical_light` going 0 → N as the single causal change, with `effective_light_physical` and `torch_minutes` recognized as derived readouts — not when the diff reports an unexplained three-bit cluster.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/knowledge-and-reasoning.md` | The reasoning this probe checks |
| `gym/docs/3_decisions/state.md` | The true-state schema the diff reads |
| `gym/docs/references/game/code.md` | The disassembly — which fields are cause vs readout |
