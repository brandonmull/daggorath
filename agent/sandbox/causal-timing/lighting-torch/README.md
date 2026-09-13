# Lighting a Torch

_Experiment 1 of [`causal-timing/`](../README.md) — the deterministic anchor._

## Goal

Play the two commands that light a torch, and watch the three moments for each. Because the outcome is known in advance, this is the experiment that checks the method itself: if the record does not show the torch's effect landing, then the method is wrong — not the game.

## Why it is the anchor

The player starts with a PINE TORCH in the backpack, so both commands are deterministic:

- `PULL LEFT TORCH` always has a torch to move from pack to hand.
- `USE LEFT` always lights the torch in hand.

The changed fields can be named before the run, so a failure is unambiguous. This is the experiment the second one cannot provide: a case where the expected answer is known, so the harness itself can be judged.

## Commands and schedule

| When | Command | Expect *matched* | Expect *changed* |
|---|---|---|---|
| frame 1100 | `PULL LEFT TORCH` | yes | the torch moves pack → hand: the `hands`/`pack` channels — and **no** light change |
| frame 2000 | `USE LEFT` | yes | the torch lights: `lit_torch` (true state) lights, then `effectiveLightPhysical` brightens |

The frames assume ~60 Hz and leave ~2.9 s of margin between boot and the first post. They are parameters to tune, not facts.

## Watched fields

The columns this experiment treats as an effect, chosen from the shared signal set in the parent:

- the `hands`/`pack` channels — the object moved.
- `lit_torch` (minutes, physical light) and `effectiveLightPhysical` — the torch lit.

Every other column is recorded but ignored here.

`PULL` is the interesting case: it changes only the holdings columns, never a scalar, so a diff that watched only scalars would report "nothing changed." This experiment reproduces that miss on purpose.

## The control

None is scheduled here — both commands are expected to change something. If either shows *matched* without *changed*, that is itself the finding (and the harness is at fault).

## What the trace should show

- Two *matched* events, each a few frames after its post.
- A *changed* event after each: holdings at `PULL`, light at `USE`.
- The offsets from post to *matched*, and from *matched* to *changed*, for both.

## Plan

When the shared harness is built, this folder adds only its schedule and this list of watched fields; the way state is read and analyzed stays in the parent. A first version can follow the example in `agent/sandbox/causal-diff/server.py`, which waits for a known outcome — except here we measure the wait instead of assuming it.

## Open questions

- Does `PULL`'s change land after the *matched* flag, or with it?
- Does `USE` light the torch in the frame the parser matches, or is there a lag while the light is recomputed?
- Does `effectiveLightPhysical` lag `torchPhysicalLight`, since the light is recomputed on the next display refresh?

## Running

Not built yet.
