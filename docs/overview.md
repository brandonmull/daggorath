# Project Overview

_A newcomer-friendly explanation of what we're building and why._

---

## What Is This Project?

We're training an AI to play **Dungeons of Daggorath**, a 1982 text-adventure / dungeon-crawler game for the TRS-80 Color Computer. The game runs inside **MAME**, an emulator that simulates the original hardware — including a Motorola 6809 CPU running at ~0.89 MHz (yes, megahertz, singular).

MAME lets us attach **Lua scripts** that run alongside the emulated machine. These scripts can read the emulated RAM (to see what's happening in the game) and inject keystrokes (to control the game). On the other side, a **Python** program communicates with MAME over a hybrid IPC bridge and presents everything as a standard **Gymnasium** environment (the same interface used by OpenAI Gym for reinforcement learning).

```
┌─────────────────────────────────────────────────────────────┐
│                      Python (our code)                      │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ emulator.py  │   │  state.py    │   │ environment.py │  │
│  │ IPC bridge   │   │ deserialize  │   │ Gymnasium Env  │  │
│  │              │   │ game state   │   │ step()/reset() │  │
│  └──┬───────┬───┘   └──────▲───────┘   └────────────────┘  │
│     │       │              │                                 │
│     │ FIFO  │ TCP          │ typed attributes               │
│     │ write │ socket       │ (obs.heart_rate, obs.at_cell_x)│
│     │       │ (port 15001) │                                 │
├─────┼───────┼──────────────┼─────────────────────────────────┤
│     │       │              │                                 │
├─────┼───────┼──────────────┼─────────────────────────────────┤
│     │       ▼              │                                 │
│     │  ┌──────────────────────────────┐                      │
│     │  │      MAME (emulator)         │                      │
│     │  │  ┌────────────────────────┐  │                      │
│     │  │  │  Lua plugin (daggorath) │  │                      │
│     │  │  │  - init.lua (entry)    │  │                      │
│     │  │  │  - state.lua           │  │                      │
│     │◄─┼──│    (writes state FIFO) │  │                      │
│     │  │  │  - commands.lua        │  │                      │
│     │  │  │    (reads command TCP) │  │                      │
│     │  │  └────────────────────────┘  │                      │
│     │  │  ┌────────────────────────┐  │                      │
│     │  │  │  Emulated CoCo 3        │  │                      │
│     │  │  │  - 6809 CPU             │  │                      │
│     │  │  │  - 16-64K RAM           │  │                      │
│     │  │  │  - Daggorath cartridge  │  │                      │
│     │  │  └────────────────────────┘  │                      │
│     │  └──────────────────────────────┘                      │
└─────┼────────────────────────────────────────────────────────┘
      │ state FIFO (/tmp/daggorath-state)
      │ tagged records on change (S / T / B)
```

## Key Design Choices

- **Hybrid IPC** — a named pipe (FIFO) for game state (MAME → Python, high-throughput write-only) and a TCP socket on port 15001 for commands (Python → MAME, low-throughput read-only). The state channel uses standard Lua `io.open("w")` to bypass `emu.file`'s fragility under sustained write load; the command channel stays on `emu.file("r")` which is documented as stable and provides the non-blocking reads that FIFOs can't do. See `gym/docs/findings/ipc.md` for the evaluation of alternatives.
- **No external Lua dependencies** — MAME ships its own embedded Lua interpreter. LuaRocks packages cannot be loaded. All Lua scripts use only MAME's built-in APIs and the standard Lua `io` library.
- **Raw byte wire format** — no JSON on either channel. Compact, fast, and avoids serialization overhead on the emulated CPU.
- **Change detection, not frame-by-frame** — the state channel emits a record only when something meaningful changes (numeric state or command-area text), not every frame. Identical frames are dropped in Lua against a snapshot.
- **Flyweight pattern** — shared schema objects on both sides, per-change value objects. Schema defines the contract once; instances are light.

## Perception Principles

These govern what the agent perceives — the answer to "what does the player perceive, and how faithfully do we reproduce it."

### Perception must carry the world.

> Position + heading + body state, with no walls, no creatures, no goal, reduces to a random walk with a sparse death penalty.

Perception has to give the agent something to act on. Self-state alone — position, heading, body — leaves nothing to navigate toward, avoid, or seek: no gradient, no goal, nothing to learn. The trainable core is the *world* (the maze, the creatures, the light) plus self-state. How fairly the agent's access to that world mirrors a real player's is a later curriculum concern, not a prerequisite for the first working environment — act first, fairness later. The reasoning is recorded in [`perception`](../gym/docs/3_decisions/perception.md).

### Perception vs. proprioception.

World state — creatures, floor objects, walls, light — is perception-gated: the agent gets only what sight and sound convey. Self state — strength, heart, exertion, carried weight, hands, pack, torch-in-hand — is full precision. The argument: the player knows their own body through experience even without a display, and RL agents conventionally read their own internal state; only the outside world is ever hidden from them.

### Hidden vs. imprecise.

Gate what the player *cannot* know (a creature's hitpoints, a threat around the corner). Give precision for what the player knows only *imprecisely* (their own strength, their racing heart, the torch's remaining life). "Not displayed as a number" is not "not known" — the game teaches strength through kill efficiency, so the player knows it without seeing it.

### The environment owns true state; the observation is sensory.

The environment holds true state regardless — reward is computed on it by an agent-side wrapper, and termination is reported by the environment — whether or not the agent observes it. Whether a self-state number also appears in the observation is a courtesy, not a necessity; the open question for any such signal is "who is responsible for knowing it — the environment or the agent?"

### "Cell," not "room."

The maze is a uniform 32×32 grid of cells. The game has no rooms — only halls (the renderer cannot draw a 2×2 block of open cells). Use "cell" for a grid position; never "room."

### The curriculum is the bridge.

Environment-provided conveniences — a memory buffer, a sound→source association, a strength number — are provisional scaffolding for capabilities that conceptually belong to the player, and hence to the agent. Expose them now to make training tractable; the curriculum removes them in later stages, so the agent learns the capability itself.

## Naming Conventions

### All names come from the plan docs — never improvise.

The plan documents name every constant, function, class, and variable. Use those exact names. If you think a name could be shorter or different, ask first.

### Prefer fully-worded terminology.

Domain terms have specific multi-word names defined in the plans ("command phrase", "command word", "command index", "command socket"). Never drop the qualifying word — a "phrase" on its own is ambiguous, "command phrase" is precise. This applies everywhere: constant names, function names, local variables, docstrings, comments. If the plan calls it `_build_command_phrases`, don't shorten it to `_build_phrases`. If a comment describes "62 phrases", write "62 command phrases". The qualifier is not redundant — it distinguishes our domain concept from generic programming terms.

### Constants use UPPER_SNAKE_CASE on both sides.

Lua uses `local` for privacy, Python uses a `_` prefix. The root names are identical: `COMMAND_WORDS` on both sides, `_COMMAND_WORDS` in Python. Every constant that exists on one side must exist on the other with the same name (modulo the `_` prefix for Python privacy).

### `socket`, never `sock`.

### Multi-word names follow adjective-then-noun order.

`stateSocket`, not `socketState`. `commandPort`, not `portCommand`.

## Documentation Structure

Project docs follow a two-phase design pipeline:

| Phase | Directory | Description |
|-------|-----------|-------------|
| **Plans** | `gym/docs/2_plans/` | Pre-build design specifications — what we intended to build |
| **Decisions** | `gym/docs/3_decisions/` | Implemented concepts — the decision and its reasoning |

Two further categories sit beside the pipeline: **findings** (`gym/docs/findings/`) — hard-won discoveries from reverse-engineering — and **references** (`gym/docs/references/`) — external source material from the game manual, disassembly, and hardware docs.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `gym/docs/2_plans/deployment.md` | Deployment — registration: making the environment discoverable via `gymnasium.make` |
| `gym/docs/2_plans/creatures.md` | Creature detection — knowns, unknowns, and open questions |
| `gym/docs/2_plans/objects.md` | Object detection — knowns, unknowns, and open questions |
| `gym/docs/2_plans/sound.md` | Sound — the auditory observation channel |
| `gym/docs/2_plans/events.md` | Events — the deferred event channel and its candidate catalog |
| `gym/docs/2_plans/cpp-port.md` | C++ port — replacing the MAME backend with a faithful port |
| `gym/docs/3_decisions/state.md` | State module — the reported state and its wire format |
| `gym/docs/3_decisions/commands.md` | Commands module — the 154 phrases and the factored action space |
| `gym/docs/3_decisions/screen.md` | Screen reading — command-area pixel decode |
| `gym/docs/3_decisions/navigation.md` | Navigation — maze decode and line-of-sight |
| `gym/docs/3_decisions/perception.md` | Perception — the gated observation channels |
| `gym/docs/3_decisions/deployment.md` | Deployment — the gym/agent package split |
| `gym/docs/3_decisions/plugin-conversion.md` | MAME plugin conversion |
| `gym/docs/3_decisions/ipc-hybrid.md` | Hybrid IPC — FIFO state channel + TCP command channel |
| `gym/docs/3_decisions/gc-autounsubscribe.md` | Saving notifier subscriptions to prevent GC auto-unsubscribe |
| `gym/docs/3_decisions/readiness-gating.md` | Gating RAM reads on `displayFunction == 0xCE66` before sampling |
| `gym/docs/3_decisions/roms-in-repo.md` | ROMs stay in the repo — verify-only, never download |
| `gym/docs/findings/ipc.md` | IPC transport evaluation — FIFO vs TCP vs Unix sockets |
| `gym/docs/findings/ram-signals.md` | RAM signal catalog — readiness and command-acceptance signals |
| `gym/docs/findings/memory-reads.md` | Safe RAM reads + segfault debugging in MAME Lua |
| `gym/docs/findings/deterministic-maze.md` | Deterministic maze — the dungeon is fixed by a per-level seed table in ROM |
| `docs/portfolio.md` | Portfolio positioning — the value claim and the README's binding rules |
| `docs/game/combat-model.md` | The strength-vs-damage combat model and the sound proximity channel |
| `docs/game/commands.md` | Original game manual + ROM-derived command grammar, object tables, incantation words |
| `gym/docs/references/game/ram.md` | Memory map — every known RAM address and what it stores |
| `gym/docs/references/game/code.md` | Full 6809 disassembly of the game |
| `gym/docs/references/coco/hardware.md` | CoCo hardware reference |
| `gym/docs/references/mame/setup.md` | Emulator architecture notes, lite MAME build plans |
| `gym/sandbox/README.md` | Sandbox validation: TCP sockets, natkeyboard delivery, command buffering |
| `gym/README.md` | Project overview, milestones, setup instructions |