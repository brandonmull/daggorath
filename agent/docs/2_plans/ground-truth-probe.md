# Ground Truth Probe — Plan

_What this plan covers: one probe that verifies two things about the torch-lighting event against the game's known mechanics — the **state diff**, and the **primitive-field choice**. The state diff is subtraction over the perceived state before and after a command: which fields changed, and to what. The primitive-field choice is the split of those changed fields into one cause and the readouts computed from it. What this plan does not cover: the causal chain itself — the representation, the stores, the contingency, the reasoning over it, and how the acting agent reads it — all of which remains open discussion in `../1_discussions/knowledge-and-reasoning.md`._

## Why the probe first

The causal chain is the goal, but it is not ready to build. The discussion that led here (`knowledge-and-reasoning.md`) left several questions open — what self-consistency concretely does, how reasoning over the chain is learned, how the value layer is represented, how overlapping masks unify, how the acting agent reads the store. Each of those is load-bearing for a real implementation, and none is settled.

The probe is the one step that does not wait on any of them. It needs no self-consistency, no reasoning, no value representation, no unification, no interface. It is just subtraction over a field list: does diffing the state before and after a command recover "light the torch" as one cause and two readouts, or as an undifferentiated three-field cluster?

The reason to check that first is that everything else stands on it. If the torch structure cannot be recovered from the diff, or the primitive/derived split is wrong, then the causal chain cannot be built on top of it — no matter how the open questions are eventually answered. The probe is a foundation check: cheap, self-contained, and falsifiable, and it confirms or refutes the one assumption the rest of the work leans on.

The honest caveat: the probe validates the easy part. It does not move the hard questions — self-consistency, reasoning, the value layer — by an inch. Passing it means the foundation holds, not that the causal chain is near. The plan is scoped to the probe precisely so that "ready for the probe" is never mistaken for "ready for the causal chain."

The probe covers only the torch-lighting event. A full enumeration of primitive and derived fields across the whole state is out of scope here; it comes later, one case at a time, leaning on the split this probe confirms.

## The state diff

The diff is subtraction over the nineteen numeric fields of the state between a before-state and an after-state, reported as two things: which fields changed, and each changed field's before → after. Everything beyond the player's own frame — the maze, creatures, the objects in hand, in the pack, and on the floor, holes and ladders — is outside the diff; the probe diffs the nineteen numeric fields only. The diff reads the *perceived* state, not the true state; for these nineteen fields the two are identical (they are the player's own frame, always known), but perceived is the substrate the causal chain will build on, and it keeps the boundary clean: the reward reads true state, learning reads perceived state.

Two timing terms need pinning down. **Before** is the state read immediately before a command is sent. **After** is the state read once the command's effect has settled — once each field of interest has reached its predicted value — not "one frame later"; the torch effect spreads over a few frames, so a fixed one-frame "after" would cut it short (see "Delayed changes").

The diff is expected to carry noise. Some fields move on their own — the heartbeat, exertion, the torch's own countdown — independent of any command. The probe does not try to filter them; the machinery that will is deferred to the causal chain. So the diff may show extra changed fields, and those are reported, not failed. "Noise" has two senses: fields changing on their own is expected and harmless; the diff only fails when the torch fields themselves do not change as the game's own code predicts — when the structure cannot be recovered.

## The primitive-field choice

Lighting a torch changes three numeric fields, and they are not three independent causes:

- `torch_physical_light` — the cause: the torch's own light output, 0 before, N after.
- `effective_light_physical` — a readout: how well the player can see, recomputed by the game as the ambient light plus the torch's power, not written by USE directly.
- `torch_minutes` — a readout: the burn-down timer, started by the torch being lit, then ticking down on its own.

The game's own code is the authority for which is which; the probe confirms it empirically. Confirming empirically means the observed diff matches that split: these three torch fields appear as the event's structure, `torch_physical_light` goes 0 → N as the one cause, and the two readouts take values consistent with being derived from it. A naive diff would count all three as separate causes; the probe's job is to show one cause and two readouts instead.

## The probe

Lighting a torch is a documented event, so it is known before any code runs what the diff should see: one cause and two readouts. The probe is a script — `agent/sandbox/ground-truth-probe/server.py`, run as `python agent/sandbox/ground-truth-probe/server.py` — that checks the diff sees that structure instead of a flat cluster. It is a sandbox experiment, not a package module: a one-off check that mirrors the gym package's own sandbox convention rather than joining the training harness.

```
main()
    → builds the environment headless
    → resets and reads the baseline; the three torch fields must be unlit
    → plays PULL LEFT TORCH
        → reads the before-state
        → sends the command through the environment's step
        → advances frames until a hand holds the torch
        → reads the after-state, diffs, reports — expecting no field change
    → plays USE LEFT
        → reads the before-state
        → sends the command through the environment's step
        → advances frames until the burn-down timer starts
        → advances frames until the effective light catches up to the torch's own light
        → reads the after-state, diffs, reports
    → classifies each changed field as cause, readout, or noise
    → asserts the success criterion
    → prints the report and returns pass or fail
```

The probe reads what the player perceives — the numeric fields and the held objects — never the true state or RAM addresses. The action is recorded as the index the probe issued, looked up rather than hardcoded; the wait action is one that sends no command yet still advances a frame. The module's constants and helpers are specified in "Technical details" below.

## Technical details

The probe is a Python script built only on the environment's public surface: `DaggorathEnv` (the Gymnasium environment), the perceived observation, the command API (`derive_command_index` and `DaggorathCommand.phrase`), and the `FIELDS` schema from `daggorath_gym.state`, with numpy providing the array types.

It reads two perceived channels. `scalars` is a uint16 array holding the nineteen `FIELDS` in schema order, read by field name through `_FIELD_INDEX`, a name → position map built from `FIELDS`. `hands` is a uint8 array of two slots: `0xFF` for an empty hand, otherwise the held object's specifier index.

The factored action space is verb form (0–25) × object specifier (0–30). `_find_action` scans it with `derive_command_index` and `DaggorathCommand.phrase` to recover the factored action for a phrase; `_find_noop_action` returns the first syntactically invalid pair — INCANT with a non-ring — which maps to no command, so the step advances a frame without acting. The scripted actions resolve to verb form 23 with object specifier 5 (PULL LEFT TORCH), verb form 11 with object specifier 0 (USE LEFT), and verb form 25 with object specifier 0 (the no-op).

`_PRIMITIVE_FIELDS` and `_DERIVED_FIELDS` are tuples of field names — the former holding torch_physical_light, the latter effective_light_physical and torch_minutes — and `_TORCH_FIELDS` is their concatenation. `_SETTLE_STEPS` caps each settle wait at 100 no-op frames.

The helpers, and what each does:

```
_find_action()
    → walks the factored action space
    → returns the first pair whose command phrase matches the given phrase

_find_noop_action()
    → returns an invalid pair that sends no command

_scalar()
    → reads one field by name from the scalars channel

_scalar_values()
    → reads the scalars channel
    → returns every field name with its value

_diff_scalar_fields()
    → takes a before and an after field map
    → returns each changed field with its before and after values

_classify_field()
    → takes a field name
    → returns cause, readout, or noise

_hand_holds_torch()
    → reads the hands channel
    → returns true when either hand slot is not the empty sentinel

_torch_lit()
    → returns true once the burn-down timer is above 0

_effective_light_settled()
    → returns true once the effective light equals the torch's own light

_action_phrase()
    → returns the command phrase for a factored action, for the report

_step_until_settled()
    → steps the environment with the no-op action
    → returns the first observation that satisfies the predicate
    → or stops at the step cap or the read timeout

_report_command()
    → prints the factored action and its phrase
    → then each changed field — name, before → after, and classification — in schema order
    → or prints that no scalar field changed
```

`main()` builds the environment headless (window off, sound off), runs the scripted sequence, and returns 0 on pass, 1 on fail.

## Delayed changes

Exactly one field of interest is delayed. `torch_physical_light` and `torch_minutes` arrive together, promptly — the moment USE lights the torch, both jump in the same frame group. `effective_light_physical` trails by a frame or two, because the game recomputes it only when it next redraws the screen, not when USE runs.

The probe handles the delay by waiting for each field to reach its known value, not for a fixed span of time. Each wait stops as soon as the field shows the expected value, so the probe cannot miss the change by stopping too early or too late. The only field it must wait for is `effective_light_physical`; the other two are already present when the timer first starts. The timer's continued countdown after that is just the field ticking on its own, not part of the effect.

## What the probe does not capture

The probe does not record the three-part unit — precondition, action, effect — and does not store anything for later analysis. Its action is known — it sent it; its before and after states are read, diffed, then discarded; its precondition ("torch in hand") is observed only to settle PULL — a hand now holding the torch — never diffed, because it is one of the held objects, outside the nineteen numeric fields. Capturing states continuously and building the causal chain from them is the deferred work the discussion leaves "named but not yet planned." The probe is a one-shot check of one ingredient — the diff of one documented event — not the first rung of that capture pipeline.

## Success criterion

The probe succeeds when the USE diff shows `torch_physical_light` going 0 → N (N above 0) as the single cause, with `effective_light_physical` and `torch_minutes` recognized as readouts — the former equal to `torch_physical_light` afterward, the latter above 0 — and no changed field classified as anything but cause, readout, or noise. It fails when the torch structure cannot be recovered: the three fields do not change as predicted, or `torch_physical_light` does not read as the single cause. It does not fail because unrelated fields also changed on their own.

The PULL diff must show no torch-field change — moving the torch from pack to hand changes the held objects, which the diff does not see — confirming the torch is not lit until USE.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/knowledge-and-reasoning.md` | The reasoning this probe checks — the mask/value split, the triple, the deferred contingency |
| `gym/docs/3_decisions/state.md` | The true-state schema the diff reads |
| `gym/docs/references/game/code.md` | The disassembly — which fields are cause vs readout, and the display-refresh recompute of effective light |
