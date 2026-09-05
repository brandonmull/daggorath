# Ground Truth Probe — Plan

## Purpose and scope

The goal down the line is an agent that understands cause and effect in the game — that taking the torch from your pack and lighting it is what lets you see. That understanding has to rest on something, and the most basic something is this: when you act in the game and then look at what changed, can you actually tell what happened?

This probe answers that question for one case, the one we can check against a known answer. It runs the real game, takes the torch out and lights it, and asks whether a plain before-and-after comparison recovers each step — the torch in hand, then its light on — or just a jumble of unrelated changes.

The scope is deliberately small. This is about lighting a torch and nothing else. It saves nothing for later, and it builds none of the understanding the agent will eventually need — that work is still open elsewhere. Passing it proves only that the foundation holds, not that anything has been built on it.

## Success criterion

The bar is simple, and worth stating up front. Lighting a torch is a two-step story — take it out of the pack, then light it — and the probe has to catch both steps. In the second, it must be able to point at the torch's light coming on and say "that's the cause."

And everything else is allowed to be messy. The game is alive even when the player stands still — the heart beats, the body tires, the torch's timer ticks down. Those changes are fine; the probe can notice them and let them pass.

Two checks, in order:
1. After pulling the torch out, a hand holds it.
2. After using the torch in hand, the torch's light is on.

## Strategy

The plan is to act out the story and watch it happen. Run the real game, take the torch out of the pack, light it, and compare the game's state before and after each step. The comparison is plain subtraction: what changed, and by how much.

Only a small part of the state matters — the numbers about the player (where they are, how they're doing, how well they can see) and what they're holding. Everything else — the maze, the creatures, the objects on the floor — is left out. And the comparison looks at what the player perceives, not at the game's hidden truth — the agent learns from what it sees, and it's judged on what's actually true.

Lighting a torch changes one number that matters — the torch's own light coming on — and a careless reading would mistake every change in the diff for its own cause. The probe's job is to see through that: one number is the cause, and the rest — the heartbeat, the tiredness, the torch's timer — are noise it notices and lets pass. We already know which is which because we've read the game's code; the probe's job is to confirm that reading, not to discover it.

## Technical details

The probe is one Python script on nothing but the environment's public surface — `DaggorathEnv`, the perceived observation, the command API (`derive_command_index` and `DaggorathCommand.phrase`), and the `FIELDS` schema — with numpy for the array types.

It reads two perceived channels. `scalars` is a uint16 array holding the nineteen `FIELDS` in schema order, read by field name through `_FIELD_INDEX`, a name → position map built from `FIELDS`. `hands` is a uint8 array of two slots: `0xFF` for an empty hand, otherwise the held object's specifier index. Both channels are diffed before and after each command, so the PULL step's change — a hand now holding the torch — shows in the report, not just the USE step's scalar change.

The factored action space is verb form (0–25) × object specifier (0–30). `_find_action` scans it with `derive_command_index` and `DaggorathCommand.phrase` to recover the factored action for a phrase; `_find_noop_action` returns the first syntactically invalid pair — INCANT with a non-ring — which maps to no command, so the step advances a frame without acting. The scripted actions resolve to verb form 23 with object specifier 5 (PULL LEFT TORCH), verb form 11 with object specifier 0 (USE LEFT), and verb form 25 with object specifier 0 (the no-op).

`_PRIMITIVE_FIELDS` is a one-field tuple holding torch_physical_light, the single cause; there is no derived field, because the burn-down timer is noise. `_SETTLE_STEPS` caps each settle wait at 100 no-op frames.

The flow of `main()`:

```
main()
    → builds the environment headless
    → resets and reads the baseline; the torch must be unlit
    → plays PULL LEFT TORCH
        → sends the command through the environment's step
        → advances frames until a hand holds the torch
        → checks that a hand holds the torch
    → plays USE LEFT
        → sends the command through the environment's step
        → advances frames until the torch lights
        → checks that the torch's light is on
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
    → returns cause or noise

_hand_slots()
    → reads the hands channel
    → returns the two slot values, with 0xFF for an empty hand

_hand_holds_torch()
    → reads the hands channel
    → returns true when either hand slot is not the empty sentinel

_torch_lit()
    → returns true once the torch's light is on

_action_phrase()
    → returns the command phrase for a factored action, for the report

_step_until_settled()
    → steps the environment with the no-op action
    → returns the first observation that satisfies the predicate
    → or stops at the step cap or the read timeout

_report_command()
    → prints the factored action and its phrase
    → then any changed hand slot, before → after
    → then each changed scalar field — name, before → after, and classification — in schema order
    → or prints that no scalar field changed
```

`main()` returns 0 on pass and 1 on fail.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/knowledge-and-reasoning.md` | The reasoning this probe checks — the diff, the three-part unit, the deferred contingency |
| `gym/docs/3_decisions/state.md` | The true-state schema the diff reads |
| `gym/docs/references/game/code.md` | The disassembly — the single primitive cause, torch_physical_light |
