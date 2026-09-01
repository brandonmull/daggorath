# Daggorath

**A world that didn't exist.**

*Dungeons of Daggorath* (1982) is now a reinforcement-learning environment — and a brutally hard one. The game keeps no score at all. The dungeon is dark until you light a torch, and whatever you can't see, you hear. Every action is one of 806 typed commands, and nothing pays off quickly. Those are the conditions modern RL handles worst, and testbeds that pose them are scarce. That makes a game this old an unexpectedly useful place to train, and it's built for anyone to do it.

Getting there meant finishing a memory map others had started, reconstructing the game's combat math from its own code, and learning the hard way what an emulator tolerates when you instrument it at full speed.

## Quick start

Runs on Debian/Ubuntu Linux, or Windows via WSL. Run `./setup.sh` — it's interactive and tells you exactly what it's doing: it pauses before each step so you can approve or skip any of them, and it never does anything you haven't said yes to.

1. **Build MAME 0.289 from source.** The version matters — the packaged MAME (0.264) is too old for this environment. Skip this if you already have 0.289.
2. **Create the Python virtual environment** (`.venv`).
3. **Install the two packages** — `daggorath-gym` (the environment) and `daggorath-agent` (the trainer).
4. **Verify the game ROMs** (`coco3.zip`, `daggorath.zip`) — they ship with the repo. Verify-only: the script never downloads; it just confirms the files are intact.

Then:

```bash
.venv/bin/python -m daggorath_agent.train --watch
```

`--watch` opens the game window with sound so you can watch it train; leave it off to run silently. Saved weights land in `agent/checkpoints/`.

Prefer to do it by hand? The full manual steps are in the [environment's install guide](gym/README.md#installation).

## Status

The game boots and reports its state, and the training loop runs end to end. What isn't done:

- **No trained agent.** The reward is a first pass; no run has produced competent play.
- **No curriculum.** Staged rewards and command masking are still being scoped ([`agent/docs/plans/curriculum.md`](agent/docs/plans/curriculum.md)).

The environment's full issue list is in [`gym/README.md`](gym/README.md#known-issues).

## What makes this interesting

### What it took

MAME exposes the emulated machine's memory and a keyboard matrix, and nothing more — no notion of a player, a creature, or a wall. Turning that into signals an agent can act on took three things:

- **Meaning from a binary** — reading the community's disassembly to resolve the RAM fields its map left open: which addresses mean "you are here," "this is in front of you," "you just died." The combat model — the damage formula, both strength-vs-damage pools, and a shield bug in the original ROM — was reconstructed from the cartridge.
- **A transport the emulator survives** — 15 sandbox experiments established what MAME's embedded Lua actually tolerates: a FIFO for high-throughput state, a TCP socket for commands, no external dependencies, and reads gated so the game is never sampled mid-update.
- **Typing as an action space** — the agent has no controller. Every action is a typed phrase, dispatched only when a readiness signal found in RAM says the game will accept it.

The algorithm was never the hard part. The trainer just calls `step()` — all the work was making `step()` mean something.

### An interface worth building on

The environment was built against what a person training an agent actually needs:

| What a trainer needs | How it's served |
|---|---|
| A standard interface | A Gymnasium environment, so any RL library can attach; framework-specific adaptation stays in the trainer, not here |
| Learnable observations and actions | Structured spaces, not raw memory dumps |
| Actions that mean something | The game's own commands — a verb and an object — not keystrokes |
| Episodes that end correctly | The game's real death and win conditions, not a timer guess |
| Freedom to define the goal | The environment reports facts and returns reward `0.0`; the reward is yours to define |
| True state for the reward, without cheating the policy | Full state is available to whoever computes reward, but it never leaks into what the agent sees |
| Speed, and the ability to watch | Headless by default — no window, training runs in the background; `--watch` opens the window with sound |

The most important of these: the environment holds no opinion about what the agent should want. It reports what is true and returns reward `0.0`, so the objective belongs to whoever is training. Bring your own reward; nothing argues with you.

## Choose your door

### How the environment was built

The instrumentation: the RAM map, the 6809 disassembly, the MAME Lua plugin, and the findings from making an opaque machine observable. Start with the architecture overview, then the environment itself.

→ [`docs/overview.md`](docs/overview.md) · [`gym/README.md`](gym/README.md)

### The trainer as a worked RL example

An end-to-end PPO run against a real game: the reward wrapper, the observation wrapper, and a custom CNN+MLP feature extractor over a `Dict` observation space.

→ [`agent/README.md`](agent/README.md)

### Build on it

`daggorath-gym` is a distributable Gymnasium package, and reward is a wrapper — bring your own. The observation and action spaces are specified in the perception plan; the reward contract is in the reward plan.

→ [`gym/docs/plans/perception/plan.md`](gym/docs/plans/perception/plan.md) · [`gym/docs/plans/reward/plan.md`](gym/docs/plans/reward/plan.md)

