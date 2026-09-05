# Ground Truth Probe — Plan

## Purpose and scope

The goal down the line is an agent that understands cause and effect in the game — that taking the torch from your pack and lighting it is what lets you see. That understanding has to rest on something, and the most basic something is this: when you act in the game and then look at what changed, can you actually tell what happened?

This probe answers that question for one case, the one we can check against a known answer. It runs the real game, lights a torch, and asks whether a plain before-and-after comparison recovers the truth — one thing caused it, two things followed — or just a jumble of unrelated changes.

The scope is deliberately small. This is about lighting a torch and nothing else. It saves nothing for later, and it builds none of the understanding the agent will eventually need — that work is still open elsewhere. Passing it proves only that the foundation holds, not that anything has been built on it.

## Success criterion

The bar is simple, and worth stating up front. Lighting a torch is a two-step story — take it out of the pack, then light it — and the probe has to catch both steps. In the second, it must be able to point at the torch's light coming on and say "that's the cause," and at the timer starting and say "that just followed from it."

And one thing is allowed to be messy. The game is alive even when the player stands still — the heart beats, the body tires. Those changes are fine; the probe can notice them and let them pass.

Three checks, in order:

- After pulling the torch out, a hand holds it.
- After using the torch in hand, the torch's light is on.
- Changes that happen on their own — the heartbeat, tiredness — are ignored.

## Strategy

The plan is to act out the story and watch it happen. Run the real game, take the torch out of the pack, light it, and compare the game's state before and after each step. The comparison is plain subtraction: which of the numbers changed, and by how much.

Only a small set of numbers matters — the ones about the player and their immediate situation: where they are, how they're doing, how well they can see. Everything else in the game — the maze, the creatures, the objects on the floor — is left out of the comparison. And the comparison looks at what the player perceives, not at the game's hidden truth; for these particular numbers the two happen to be the same, but the distinction is the whole point — the agent learns from what it sees, and it's judged on what's actually true.

Lighting a torch changes three of those numbers, and a careless reading would call it three separate causes. The probe's job is to see through that: one number is the cause — the torch's own light coming on — and the other two are computed by the game from it — how well you can see now, and how long the torch has left. We already know which is which because we've read the game's code; the probe's job is to confirm that reading, not to discover it.

One of the three lags behind. The torch's light and the countdown timer both flip the instant it lights, but how well you can see doesn't change until the game next redraws the screen, a frame or two later. So the probe doesn't wait a fixed amount of time and hope; it waits for each number to reach the value it's supposed to reach.

## Technical details

The probe is one Python script on nothing but the environment's public surface — `DaggorathEnv`, the perceived observation, the command API (`derive_command_index` and `DaggorathCommand.phrase`), and the `FIELDS` schema — with numpy for the array types.

It reads two perceived channels. `scalars` is a uint16 array holding the nineteen `FIELDS` in schema order, read by field name through `_FIELD_INDEX`, a name → position map built from `FIELDS`. `hands` is a uint8 array of two slots: `0xFF` for an empty hand, otherwise the held object's specifier index.

The factored action space is verb form (0–25) × object specifier (0–30). `_find_action` scans it with `derive_command_index` and `DaggorathCommand.phrase` to recover the factored action for a phrase; `_find_noop_action` returns the first syntactically invalid pair — INCANT with a non-ring — which maps to no command, so the step advances a frame without acting. The scripted actions resolve to verb form 23 with object specifier 5 (PULL LEFT TORCH), verb form 11 with object specifier 0 (USE LEFT), and verb form 25 with object specifier 0 (the no-op).

`_PRIMITIVE_FIELDS` and `_DERIVED_FIELDS` are tuples of field names — the former holding torch_physical_light, the latter effective_light_physical and torch_minutes — and `_TORCH_FIELDS` is their concatenation. `_SETTLE_STEPS` caps each settle wait at 100 no-op frames.

The flow of `main()`:

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

`main()` returns 0 on pass and 1 on fail.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/knowledge-and-reasoning.md` | The reasoning this probe checks — the diff, the three-part unit, the deferred contingency |
| `gym/docs/3_decisions/state.md` | The true-state schema the diff reads |
| `gym/docs/references/game/code.md` | The disassembly — which fields are cause vs readout, and where effective light is recomputed |
