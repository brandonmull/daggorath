# Torch Lighting — Course 1

_First course in the curriculum — see the [syllabus](README.md) for the ladder._

## Purpose

The first thing a competent agent must do is light a torch. The raw reward cannot teach this: a fresh agent in the dark has no gradient toward the four-command recipe that produces light. This course replaces that sparse signal with a dense, per-step reward machine — a finite state that tracks which step of the recipe the agent is on, and grades each command as correct or wrong.

## The recipe

Lighting a torch is four commands, in order:

```
EXAMINE → PULL LEFT/RIGHT TORCH → LOOK → USE LEFT/RIGHT
```

EXAMINE reveals the pack; PULL moves the torch from pack to a hand; LOOK returns to the dungeon view; USE on the torch hand lights it. The terminal fact is `effective_light_physical > 0`.

## The reward machine

Five states, each detected from the true state the reward wrapper reads (`current_state`), and advanced by the state transition:

| State | Detection | Advances on |
|---|---|---|
| start | dark (`effective_light_physical == 0`), torch in pack, not examining | `display_function` flips to EXAMINE |
| examined | `display_function == EXAMINE` | a torch moves pack → hand |
| held | torch in a hand | `display_function` flips back to LOOK |
| looked | `display_function == LOOK`, torch in hand | light turns on |
| lit | `effective_light_physical > 0` | — (course complete) |

The machine grades by progress: the transition that advances to the next state pays the step reward; any transition that does not advance (a wrong command, or the correct command repeated) pays the step penalty. The command is inferred from its effect on the state — the machine never reads keystrokes.

## Magnitudes

Terminal ≫ step — lighting the torch is the objective, so it is the big reward; each correct step is a modest nudge, never a catastrophe:

| Signal | Value |
|---|---|
| lit the torch | +1.0 |
| advanced a step | +0.1 |
| did not advance | −0.1 |

## Where it lives

A `TorchRewardMachine` in `daggorath_agent/reward.py`, added to the `DaggorathReward` layers already there (survival, advance, novelty). It is the first course in the curriculum ladder and is active only during this course.

## Success test

From a cold, dark start — torch in the pack, no light, not examining — the agent reliably walks the four-command recipe and ends with the torch lit. The bar is reliability: the recipe becomes the default behavior, not an occasional accident.
