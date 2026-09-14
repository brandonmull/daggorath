# Manual

_Experiment of [`machine-save-load/`](../README.md) — a person plays and saves._

## Goal

Can a state be produced by hand, without a plugin or a script? This is the fallback for a situation too fiddly to script, and it needs nothing from us except the launch and the state directory.

## Status

Waiting on a by-hand save. The console route is in place; the menu route was tried and works, but saves into slots rather than names.

## Approach

`run.py` opens MAME windowed on the CoCo 2B with the state directory pointed at the project's, the Lua console enabled, and no plugin at all — nothing should be posting keystrokes of its own while a person plays. Press any key to leave the demo loop, play to the situation you want, then type at the console prompt in the terminal:

| Typed at the console | What it does |
|---|---|
| `manager.machine:save("name")` | freezes the current moment under that name |
| `manager.machine:load("name")` | brings that moment back, mid-run |

The console is the route to use because the name is the point: it is the only by-hand route that can both name a state and bring one back without restarting.

The other two routes are weaker. MAME's own menu (**Tab**, then **Save State**) works — Tab both opens it and hands it the keyboard — but it saves into fixed slots, so there is no naming. And `--autosave` writes `auto.sta` as the machine exits: one slot, restored on the next start, no naming at all.

## Success criteria

- A session writes a state under a name of the player's choosing, and the launcher lists it.
- The scripted check resumes it: `scripted/run.py verify <name>` reports the saved moment's machine time and the same fields, which is what proves the by-hand route worked.

## Running

```bash
python gym/sandbox/machine-save-load/manual/run.py
python gym/sandbox/machine-save-load/manual/run.py --autosave
```
