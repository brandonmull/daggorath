# Daggorath

**A world that didn't exist.**

*Dungeons of Daggorath* (1982) is now a reinforcement-learning environment — and a brutally hard one. The game keeps no score at all. The dungeon is dark until you light a torch, and whatever you can't see, you hear. Every action is one of 154 command phrases, and nothing pays off quickly. Those are the conditions modern RL handles worst, and testbeds that pose them are scarce. That makes a game this old an unexpectedly useful place to train, and it's built for anyone to do it.

Getting there meant finishing a memory map others had started, reconstructing the game's combat math from its own code, and learning the hard way what an emulator tolerates when you instrument it at full speed.

## Carved above the entrance

> To all who would enter: the gate stands open, but the depths are still unmapped.

The game boots and reports its state, and the training loop runs end to end. What isn't done:

- **No trained agent.** The reward is a first pass; no run has produced competent play.
- **No curriculum.** Staged rewards and command masking are still being scoped ([`agent/docs/plans/curriculum.md`](agent/docs/plans/curriculum.md)).

The environment's full issue list is in [`gym/README.md`](gym/README.md#known-issues).

## Outside the entrance

### Step inside

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

### Read the stone

The reverse-engineering: how the game was made observable and controllable from the outside. Start with the overview, then the environment itself.

→ [`docs/overview.md`](docs/overview.md) · [`gym/README.md`](gym/README.md)

### Train at the fire

The training, end to end: how the environment becomes an agent that plays. One runnable example, from what the agent sees to what it does.

→ [`agent/README.md`](agent/README.md)

### Forge your torch

`daggorath-gym` is a distributable package, and the reward is yours to bring. The interface and the reward are documented in the decision docs.

→ [`gym/docs/decisions/perception.md`](gym/docs/decisions/perception.md) · [`gym/docs/decisions/reward.md`](gym/docs/decisions/reward.md)

## What the dark hides

### What it took

MAME exposes the emulated machine's memory and a keyboard matrix, and nothing more — no notion of a player, a creature, or a wall. Turning that into signals an agent can act on took three things:

- **Meaning from a binary** — the game offers no labels for its own state, so its own code was read to learn what its memory holds: where you are, what's in front of you, what creatures are near, how much light you have left, how close your heart is to bursting.
- **A transport the emulator survives** — getting state out and commands back in took fifteen experiments. Several approaches crashed or froze the emulator outright; the one that stuck streams continuously and never reads at the wrong moment.
- **Commands as an action space** — the agent has no controller. It issues the game's own command phrases — "attack left," "get left torch" — and only when the game is ready to accept them.

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
