# Fighting a Monster

_Experiment 2 of [`command-latency/`](../README.md) — the opportunistic case._

## Goal

Play combat commands and watch the three moments, with the effect appearing only when a creature is actually engaged. Where the torch experiment predicts its effect, this one must read it — the realistic case for an agent that does not yet know what its commands do.

## Why it is opportunistic

`ATTACK` always matches — the parser recognizes it whether or not anything is there. Whether it *changes* anything depends on a creature sharing the player's cell. So this experiment has two outcomes to distinguish, and both are useful:

- a creature is engaged → the attack changes a combat field (*changed* fires).
- nothing is engaged → the attack matches and changes nothing (the control).

An encounter is set up by hand instead of left to the opening maze. [`../../../../gym/sandbox/machine-save-load/`](../../../../gym/sandbox/machine-save-load/) shows how to freeze a moment on the CoCo 2B; a person plays to a position one or two cells from a monster and saves, and the run resumes that state before the attacks. The encounter is then near-guaranteed rather than likely.

## Commands and schedule

| When | Command | Expect *matched* | Expect *changed* |
|---|---|---|---|
| frames 600–3000, every ~200 | `ATTACK LEFT`, `ATTACK RIGHT` in rotation | yes | only when a creature is engaged: `player_strength` (a kill), `creature_alive` (a death), `creature_damage` (a hit landed) |

The window starts at frame 600, after the load settle the machine-save-load findings measured (a command posted the instant a state resumes lands hundreds of frames late; about ten seconds of quiet fixes it). The monster reaches the player's cell on its own, and the two attacks alternate without a `MOVE`.

## Watched fields

- `creature_damage` (a hit landed) and `creature_alive` (a death) — decoded from the `C` channel's per-slot fields, shipped by `gym/docs/2_plans/combat-detection.md`. `creature_strength` rides the same record for grading how hard a hit was, but is not watched: it does not move when a hit lands.
- `player_strength` — a kill, the reward the game pays in strength.
- `m0221` is recorded but not watched. It tracks how exerted the player is: a weapon swing raises it by the swing's cost before the hit or miss is decided, a creature's hit raises it, and recovery lowers it. That mix makes it a poor hit signal, but it does mark that a weapon attack ran.

Every other column is recorded but ignored here.

## The control

The `ATTACK` with nothing in range is the control the parent asks for: it should match and change nothing. The trace should show at least one, ideally many, alongside any that connect.

## What the trace should show

- Many *matched* events, one per attack.
- *changed* on some attacks (the ones that connected) and not others (the control).
- The post-to-*changed* offset for the connecting attacks — is it comparable to the torch's, or does combat resolve over more frames?

## Plan

Built. `run.py` declares the rotation schedule and the watched-field reading; the recording, the session loop, and the analysis live in the parent's `harness.py`. The schedule loads the by-hand state `monster-near` on the CoCo 2B — the only machine that can load a state — and the environment's own `daggorath` plugin samples it exactly as it does a fresh boot.

## Questions answered

The two questions this experiment opened are answered in [`../../../docs/findings/command-latency.md`](../../../docs/findings/command-latency.md): combat resolves about 19 frames after the match, and an attack with nothing in range still matches while changing nothing.

## Running

Save the encounter first, by hand:

```bash
python gym/sandbox/machine-save-load/manual/run.py
```

Play to a position one or two cells from a monster, then at the console prompt type:

```
manager.machine:save("monster-near")
```

Then record the attacks:

```bash
python agent/sandbox/command-latency/fighting-monster/run.py
```

Traces land in `agent/sandbox/command-latency/logs/fighting-monster-<session>.log`.
