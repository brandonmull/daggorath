# Machine Save Load

MAME can freeze a running machine and bring it back, but not on the machine the environment trains on. The CoCo 3 cannot save states at all. The CoCo 2B can, and once resumed it behaves like the training machine for everything we measure.

## The training machine cannot freeze

MAME reports `savestate="unsupported"` for every CoCo 3 model — `coco3`, `coco3h`, `coco3p` — because the CoCo 3's GIME chip implements no save or restore, and one unsupported device marks the whole driver. Nothing around that helps. Saving from the menu does nothing, and `-autosave` writes no file, because it is not its own mechanism — it is the same one applied at exit ("automatically restore state on start and save on exit for supported systems"). A five-second headless run with `-autosave` and a state directory came out empty.

So there is no way to freeze a moment on the training machine: not by hand, not on exit, not at startup.

## The CoCo 2B can, and behaves like the training machine

| Machine | Save states | Unthrottled |
|---|---|---|
| `coco` (CoCo 1/2) | supported | untested — its ROM set is not in the repo |
| `coco2b` (CoCo 2B) | supported | 5467% |
| `coco2bh`, `cocoh` (HD6309) | supported | untested — a different CPU would move the timing anyway |
| `coco3` (NTSC), `coco3h`, `coco3p` (PAL) | unsupported | 6553% (`coco3`) |

The CoCo 2B is about 20% slower to emulate than the CoCo 3, which does not bind while MAME is throttled to real time, and the game runs at the same 60 Hz on both — Daggorath is a CoCo 1/2 cartridge, and the CoCo 3 runs it in legacy mode. What matters more is that a settled CoCo 2B answers like the training machine: a command was matched at about ten frames per character and its effect landed zero or one frame after the match, the same relationship the torch run measured on the CoCo 3.

The cartridge itself carries no CoCo 3 compatibility tag, so it attaches to any of these machines. The `h` models replace the CPU with an HD6309 and `coco3p` runs PAL at 50 Hz, so both would invalidate the timing figures the project has already measured; they are not candidates for anything we time.

## Freezing and resuming by name

`machine:save(<name>)` freezes the running machine into `<state directory>/<machine>/<name>.sta`, and `-state <name>` loads one at startup. Those are MAME's own calls — one Lua-side and scheduled, the other a launch flag — and together they are enough to keep several situations side by side, which is what a lesson setup needs.

`-autosave` was the first proof that freezing works at all: it writes `auto.sta` as the machine exits and restores it on the next start, so quitting is the save. It is the coarser tool — one unnamed slot, written only on exit — and nothing is built on it now.

The in-game menu works, but not as a way to name a state. **Tab** both opens it and hands it the keyboard — which is not obvious, because MAME disables its UI controls for machines with an emulated keyboard — and its **Save State** entry saves into fixed slots. A name comes from the Lua call instead: `machine:save(<name>)`, typed by hand at MAME's console plugin (`-console`) or called by a plugin.

## A resumed state is live at once, and needs a moment

A state frozen in live play resumes live: the sampler reported on frame 4, where a fresh boot shows the demo loop for hundreds of frames first. It is not immediately receptive, though — a command posted the instant the state came back matched 416 frames late, with the machine still busy and the plugin's own keyboard priming in flight. Ten seconds of quiet and the same command behaved normally.

A load in the middle of a session behaved the same way: the machine came back to the saved moment with the game still running afterwards, which is what a launch flag cannot do.

A consumer that loads a state and then posts should settle first; one that only asks "does it still take a command" can post at once and ignore the offset.

## Reaching these calls

`machine:save` and `machine:load` are Lua-side, so something has to be running inside MAME to call them. Three routes, and what each taught us:

- **A plugin, but only one per path.** `-plugin` is an enable list, not a filter: every plugin on the path whose manifest says `start` begins, whether or not it is named. So a plugin path must hold one plugin, or the rest have to be named to `-noplugin`, which takes a comma-separated list. The environment's path holds only `daggorath`, so it was never bitten; the sandbox shares `gym/sandbox` with its siblings and silences them by name.
- **MAME's console plugin, which is a terminal Lua REPL**, enabled with `-console` — its own manifest says `start: false`, so the flag is what starts it. It takes `machine:save(<name>)` and `machine:load(<name>)` typed by hand while the game runs in the window, which makes it the only by-hand route that names a state and the only one that loads without restarting.
- **A scripted play must prime the keyboard.** The game sits in a demo loop until a key arrives: a Return at frame 300 leaves it, and the play screen is live by frame 725. A script that waits for the play screen without priming waits forever.

## A lit torch reads as an empty hand

`hands` (`0x021D`/`0x021F`) goes empty at the moment the torch lights, and `torchPtr` (`0x0224`) takes the torch over, carrying its minutes and its physical light. A reader watching only the hand pointers sees the torch disappear as it was lit — which is what happened the first time the load check ran against a lit dungeon.

## What it means for the project

The environment trains on `coco3`. Episode-start states are a `coco2b` capability, so a lesson that begins from a chosen situation — the unit the curriculum is built from — needs either the CoCo 2B or save/restore support for the GIME inside MAME.

There is also a gap between the sandbox and the environment that the sandbox does not close: it can call `machine:save` because it *is* a plugin, while the environment drives MAME from Python and has no way to ask for a save at a chosen moment. Starting a session from a state is the easier half — the operator would pass `-state` and `-state_directory` on its launch — but it would have to run on a machine that can load states, which the CoCo 3 cannot.

## Reference

| Document | What It Contains |
|---|---|
| [`../sandbox/machine-save-load/README.md`](../../sandbox/machine-save-load/README.md) | The sandbox that measured this, and how to run it |
| [`../references/mame/lua-core.md`](../references/mame/lua-core.md) | `machine:save`, `machine:load`, `driver.supports_save` |
