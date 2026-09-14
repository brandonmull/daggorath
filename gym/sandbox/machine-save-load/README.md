# Machine Save Load

_Freeze a running machine at a chosen moment and bring it back on demand — and show that it still takes commands when it returns._

A state is MAME's own save state: the whole emulated machine, not the game's progress. That is what makes it useful for a training setup — a lesson can begin at a chosen situation instead of replaying the steps that reach it.

Two experiments, because there are two ways to produce one, and they check each other:

- [`manual/`](manual/README.md) — a person plays and saves.
- [`scripted/`](scripted/README.md) — a plugin plays a scripted situation and saves.

A state saved by hand can be verified by the scripted check, which is what makes the manual route trustworthy rather than merely documented.

## What they share

- **The machine.** Both run on the CoCo 2B, because MAME marks every CoCo 3 driver's save states unsupported — the GIME chip implements no save or restore — and a state cannot cross between machines. `shared.py` holds the machine and the paths so neither launcher carries a copy.
- **The directory.** States land under `gym/.mame/state/coco2b/`, one file per name, and both `logs/` and `.mame/` are gitignored.
- **The proof of a load.** Emulated machine time is the address-free witness — a restored state carries its own, so it reads as the moment that was saved rather than as a fresh boot — and the game's own fields say whether the situation came back.

## Running

```bash
python gym/sandbox/machine-save-load/manual/run.py              # a person plays and saves
python gym/sandbox/machine-save-load/manual/run.py --autosave   # ...saving as the machine exits

python gym/sandbox/machine-save-load/scripted/run.py setup torch-walk
python gym/sandbox/machine-save-load/scripted/run.py verify torch-walk
```

Which machines can freeze at all, how a resumed state behaves, and what this means for starting an episode from a chosen situation are written up in [`../../docs/findings/machine-save-load.md`](../../docs/findings/machine-save-load.md).
