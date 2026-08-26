# Daggorath

Train a reinforcement-learning agent to play **Dungeons of Daggorath** (1982, Tandy TRS-80 Color Computer) — not in a toy grid, but in the real game, running in MAME on an emulated 6809.

## Choose your door

### Learn RL

See a working end-to-end PPO trainer — environment, reward wrapper, feature extractor, and a custom CNN+MLP observation pipeline — wired against a real game. Start with the trainer's design and the training plan.

→ [`agent/README.md`](agent/README.md)

### Play Daggorath

The game runs in MAME with a Lua plugin that samples RAM and dispatches keystrokes. Here's the emulated world: ROM setup, the plugin, and the original 6809 disassembly.

→ [`gym/README.md`](gym/README.md)

### Build on the library

The environment is a distributable Gymnasium package. Install `daggorath-gym` (and the trainer, `daggorath-agent`) and treat the game as a standard RL environment.

→ [`gym/README.md`](gym/README.md#installation)

## What makes this interesting

- **Fact vs. valuation** — the environment reports facts and returns reward 0.0; reward is a separate, agent-side opinion.
- **Fidelity over convenience** — a real MAME/6809 world, not a toy grid.
- **Mask, never shrink** — the curriculum stages via masking, so a run can resume on top of any earlier stage.

## Repo map

| Path | What it is |
|------|------------|
| `gym/` | `daggorath-gym` — the Gymnasium environment (MAME, the Lua plugin, state/commands/reward) |
| `agent/` | `daggorath-agent` — the PPO trainer (feature extractor, wrappers, checkpoints) |
| `NOTES.md` | Working notes — big-picture decisions across sessions |
