# Fighting a Monster

_Experiment 2 of [`causal-timing/`](../README.md) — the opportunistic case._

## Goal

Play combat commands and watch the three moments, with the effect appearing only when a creature is actually engaged. Where the torch experiment predicts its effect, this one must read it — the realistic case for an agent that does not yet know what its commands do.

## Why it is opportunistic

`ATTACK` always matches — the parser recognizes it whether or not anything is there. Whether it *changes* anything depends on a creature being within reach. So this experiment has two outcomes to distinguish, and both are useful:

- a creature is engaged → the attack changes a combat field (*changed* fires).
- nothing is engaged → the attack matches and changes nothing (the control).

The maze is deterministic (`gym/docs/findings/deterministic-maze.md`) and level 1 spawns creatures at fixed positions, but they move and pursue, so an encounter within the window is likely, not guaranteed.

## Commands and schedule

| When | Command | Expect *matched* | Expect *changed* |
|---|---|---|---|
| frames 2800–6000, every ~90 | `ATTACK LEFT`, `ATTACK RIGHT`, `MOVE` in rotation | yes | only when a creature is engaged: `m0221` (a hit taken), `playerStrength` (a kill), `creatureCount` (a death), `nearCreatureDamage` (a hit landed) |

~90 frames ≈ 1.5 s, giving each command room to finish before the next. The `MOVE` in the rotation seeks an encounter.

## Watched fields

- `m0221`, `playerStrength` — the player's side of combat (took a hit, gained a kill).
- `creatureCount`, `nearCreatureType`, `nearCreatureDY`, `nearCreatureDX`, `nearCreatureStrength`, `nearCreatureDamage` — the creatures' side.
- `atCellX`, `atCellY`, `atHeading` — movement, so a `MOVE` that changes a cell is not mistaken for a combat change.

Every other column is recorded but ignored here.

## The control

The `ATTACK` with nothing in range is the control the parent asks for: it should match and change nothing. The trace should show at least one, ideally many, alongside any that connect.

## What the trace should show

- Many *matched* events, one per attack.
- *changed* on some attacks (the ones that connected) and not others (the control).
- The post-to-*changed* offset for the connecting attacks — is it comparable to the torch's, or does combat resolve over more frames?

## Plan

When the shared harness lands, this folder gains only its schedule and this watched-field declaration. If encounters prove unreliable within the window, a refinement is to let the schedule *seek* combat — read the nearest creature and attack toward it — rather than firing blindly.

## Open questions

- Do the level-1 creatures reliably reach the player within the window, or must the schedule seek them?
- Does combat resolve in one frame after the match, or over several (the creature's reply, the next heart update)?
- Does `ATTACK` with nothing in range still set `perfectMatch`? (This is the matched ≠ changed proof.)

## Running

Not built yet.
