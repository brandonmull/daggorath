# Scripted

_Experiment of [`machine-save-load/`](../README.md) — a plugin plays a scripted situation and saves it._

## Goal

Can a named state be produced and resumed without a person at the keyboard? The fight experiment needs a setup that is awkward to play into every time — a creature next to the player, mid-encounter — and a scripted state makes that setup instant and identical from run to run.

## Status

Passing. `setup` plays the situation and writes a named state; `verify` loads that state and reports the same facts.

## Approach

The whole experiment is the plugin, `init.lua`. It posts phrases straight to natkeyboard and reads the game's RAM itself, so it imports nothing from the environment and nothing in the environment had to change. The addresses it reads come from `docs/references/game/ram.md`.

The plugin primes the keyboard with a Return at frame 300 to leave the demo loop, waits for the play screen, then walks a sequence of phrases — judging each one's expected change as it lands — and finally calls `machine:save(<name>)`. It refuses to save when a step did not play out, because a state that is not the situation you asked for is worse than no state.

`verify` launches with `-state <name>` and reports the emulated machine time along with the same fields.

`run.py` launches MAME, watches the plugin's report for its closing line, and stops the machine. The plugin path is the sandbox folder, since that is the directory holding the plugin folder; a plugin whose manifest says `start` begins whether or not `-plugin` names it, so any other manifest on that path is named to `-noplugin`.

## What each step must change

| Step | Expected change |
|---|---|
| `PULL LEFT TORCH` | `hands` goes from `0,0` to the torch's address — the left hand takes it |
| `USE LEFT` | the torch lights: minutes 15, physical light 7, and the dungeon's visible light `0 → 7` |
| `MOVE`, three times | the cell advances one column per move |

A lit torch then reads as an empty hand: the game tracks a burning torch through the torch pointer, not the hand pointer.

## Success criteria

- `setup` writes `<state directory>/coco2b/<name>.sta`, and refuses when a step does not land.
- `verify` reports the saved moment's machine time, not a fresh boot's, and the same fields.
- Two names coexist, so one session can hold several situations.

## Caveats

- A state belongs to the MAME build that wrote it and to the machine that wrote it.
- Reports land in `logs/`, alongside the manual experiment's.

## Running

```bash
python gym/sandbox/machine-save-load/scripted/run.py setup torch-walk
python gym/sandbox/machine-save-load/scripted/run.py verify torch-walk
```
