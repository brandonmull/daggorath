# Daggorath

**A world that didn't exist.**

*Dungeons of Daggorath* (1982) is now a reinforcement-learning environment — and a brutally hard one. The game keeps no score at all. The dungeon is dark until you light a torch, and whatever you can't see, you hear. Every action is one of 806 typed commands, and nothing pays off quickly. Those are the conditions modern RL handles worst, and testbeds that pose them are scarce. That makes a game this old an unexpectedly useful place to train, and it's built for anyone to do it — not just its author.

Getting there meant finishing a memory map others had started, reconstructing the game's combat math from its own code, and learning the hard way what an emulator tolerates when you instrument it at full speed.

## Quick start

Requires Linux, macOS, or WSL; Python 3.12; MAME 0.289; and the CoCo 3 + Daggorath ROMs. MAME is built from source and the ROMs are placed by hand — see [`gym/README.md`](gym/README.md#installation).

```bash
source .venv/bin/activate
pip install -e gym
pip install -e agent
python -m daggorath_agent.train --watch
```

`--watch` opens the MAME window with sound, so you can watch the agent act as it learns; drop it to train headless. Checkpoints land in `agent/checkpoints/`.

## Status

The environment runs: MAME boots the game, the Lua plugin streams state, and the training loop executes end to end. What isn't done:

- **No trained agent.** The reward is a first pass; no run has produced competent play.
- **No curriculum.** Staged rewards and command masking are designed but not built ([`agent/docs/plans/curriculum.md`](agent/docs/plans/curriculum.md)).
- **No `gymnasium.make("Daggorath-v0")`.** The environment is constructed directly.

The environment's full issue list is in [`gym/README.md`](gym/README.md#known-issues).

## What makes this interesting

### An interface worth building on

Getting an agent to play once is a demo. Whether anyone else can use the result is a design question, so the environment was built against what a person training an agent actually needs:

| What a trainer needs | How it's served |
|---|---|
| A standard API, so existing tooling attaches | A Gymnasium `Env`; framework-specific adaptation (torch has no `uint16`) stays in the trainer, not the environment |
| Spaces that are learnable, not raw bytes | A `Dict` observation and a `MultiDiscrete([26, 31])` action space |
| Actions that express the game, not keystrokes | Factored **template × object** — a verb and a thing; syntactically invalid pairs are no-ops |
| Correct episode boundaries | Termination read from the game's own death test, not a proxy |
| To decide the objective themselves | The environment returns reward `0.0`; reward is a swappable wrapper |
| True state for reward, without cheating the policy | A `current_state` property — never through `info` or the observation |
| Throughput, and the ability to watch | Headless by default; `--watch` opens the window with sound |

The one that matters most is the fifth. The environment holds no opinion about what the agent should want — it reports what is true and returns `0.0`, so the objective belongs to whoever is training. Bring your own reward; nothing argues with you.

Two needs are still unmet: environment registration and seeding (see [Status](#status)).

### What it took

MAME exposes the emulated machine's memory and a keyboard matrix, and nothing more — no notion of a player, a creature, or a wall. Turning that into signals an agent can act on took three things:

- **Meaning from a binary** — reading the community's disassembly to resolve the RAM fields its map left open: which addresses mean "you are here," "this is in front of you," "you just died." The combat model — the damage formula, both strength-vs-damage pools, and a shield bug in the original ROM — was reconstructed from the cartridge.
- **A transport the emulator survives** — 15 sandbox experiments established what MAME's embedded Lua actually tolerates: a FIFO for high-throughput state, a TCP socket for commands, no external dependencies, and reads gated so the game is never sampled mid-update.
- **Typing as an action space** — the agent has no controller. Every action is a typed phrase, dispatched only when a readiness signal found in RAM says the game will accept it.

The payoff is a 311-line trainer. Everything else exists so those 311 lines can call `step()`.

### Decisions worth arguing about

- **Reward the margin, not heart rate** — the game's iconic heartbeat is a trap: attacking raises the same exertion counter that being hit does, so penalizing a racing heart would punish the fighting that wins. Reward tracks `strength − exertion`, the game's own death test.
- **Mask, never shrink** *(planned)* — the curriculum will gate commands by masking, never by resizing the action space, so the policy head survives every stage and `--resume` chains them.

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

