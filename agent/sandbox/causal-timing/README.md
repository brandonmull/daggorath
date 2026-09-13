# Causal Timing

_Observe the three moments of a command — matched, executed, changed — and their temporal relation, to decide how one training step should be defined._

The design argument behind it — what a transition is, and why the three moments matter — is in [`../../docs/1_discussions/knowledge-representation.md`](../../docs/1_discussions/knowledge-representation.md).

This sandbox is agent-side, not part of the environment. It nails down the basic unit the agent's experience is built from — the same job as its sibling [`../causal-diff/`](../causal-diff/README.md). It reads RAM through a MAME plugin, but what it measures belongs to the agent's knowledge, not to the game.

## Goal

Measure the three moments of a command and how far apart they are:

- **Matched** — the parser recognizes a complete command. `perfectMatch` (0x027B) flags this.
- **Executed** — the command's handler runs.
- **Changed** — the game state actually differs as a result.

The measurement is the gap between *matched* and *changed*: when a command is recognized, how long until the state actually changes — and is that gap always about the same, or unrelated? *Matched* can be read from memory; *executed* and *changed* cannot, so the sandbox measures them. Why that gap matters to the agent's knowledge is in the design doc linked above.

## What the code does today

- `gym/daggorath_gym/environment.py` — `step()` sends one command (or a no-op), calls `recv()` **once**, and returns. Its comment names the follow-up: *"Wait-for-settle (perfectMatch on the wire)."*
- `gym/daggorath_gym/emulator.py` — `recv()` blocks for the **next** record (sequential, not latest), reconstructing unchanged channels from last-known values.
- `gym/emulation/plugins/daggorath/state.lua` — records are **change-gated** and sampled every frame (`frame_sampling_rate = 1`), so one command whose effect spans N frames yields up to N records.
- `perfectMatch` is **not on the wire**: the 19 `FIELDS` in `state.py` do not include it. What is shipped is `command_text` (the command-area echo, decoded from screen pixels) and the derived `command_rejected` (`"???" in command_text`).
- `agent/sandbox/causal-diff/server.py` — its probe settles with `_step_until_settled(env, obs, predicate)`, capped at `_SETTLE_STEPS = 100` no-op frames, waiting for a *command-specific* observable (hand holds torch / torch lit). That is right for a probe checking a known answer, but a per-command predicate does not scale to 154 commands.

Two candidate general signals exist, and neither is certainly "changed": `perfectMatch` (a RAM flag, not on the wire) and `command_text` (an echo, screen-derived). The echo filling marks the command going in and the echo clearing marks the parser finishing with it — plausibly closer to "processing complete," but still not "state changed."

## How the problem divides

It is the same question asked twice — *for this command, when did it match, and when did the state change?* So the sandbox is one shared harness with two sets of parameters, not two separate experiments. Everything the two commands have in common lives here; only what differs lives in a child folder.

```
causal-timing/
├── README.md            this document — the shared framing, the harness, and the division
├── lighting-torch/      experiment 1 — the deterministic anchor
└── fighting-monster/    experiment 2 — the opportunistic case
```

Three things are shared, and belong to neither child alone:

- **The observation method** — how *matched* and *changed* are read from RAM each frame, and how a run is logged.
- **The signal set** — the columns every frame records. Each child then *declares* which of those columns count as an effect for it (its watched fields).
- **The analysis** — for each posted command, the frame offset to *matched* and to *changed*, and the latency summary.

Each child contributes exactly three things, and nothing else:

- **A command schedule** — which phrases, posted at which frames.
- **A watched-field set** — which signal columns, when they change, count as that command's effect.
- **A control** — a command in the schedule that should match and change nothing, proving matched ≠ changed.

The two children exist because the question has two cases that behave differently, and the first validates the harness while the second tests it where the answer is not known in advance:

| Child | Commands | Effect is… | Why it is here |
|---|---|---|---|
| `lighting-torch/` | `PULL`, `USE` | known and deterministic | The anchor: the changed fields can be named in advance, so a wrong trace means the *method* is wrong. |
| `fighting-monster/` | `ATTACK`, `MOVE` | opportunistic | The realistic case: the effect appears only when a creature is engaged, so the trace must be read, not predicted. |

If the anchor shows *changed* tracking *matched* by a small, consistent gap, and the opportunistic case shows *matched* **without** *changed* when nothing is engaged, then the three moments are separated and the step unit can be chosen.

## The shared core

**Reading the three moments.** Nothing in memory says "the handler ran," so *executed* can't be read directly. Only the two ends can: the parser's recognition flag `perfectMatch` (0x027B) marks *matched*, and a difference in the state marks *changed*. *Executed* is whatever happens between them, guessed from the gap. Every frame records:

| Group | Columns | Witnesses |
|---|---|---|
| Consumption | `gameMode`, `perfectMatch`, `foundMatch`, `numWords`, `whereToPrint`, `nextToParse`, `comTextCursor` | *matched*, and the parser's progress |
| Display | `displayFunction` | the EXAMINE / LOOK view switch |
| Player | `atCellX`, `atCellY`, `atHeading`, `effectiveLightPhysical`, `playerStrength`, `m0221`, `heartBeatInterval` | movement, light, body |
| Holdings | `hands`, `pack` — the `O` channel's decoded identities | an object moved between pack and hand |
| Torch | `lit_torch` — the `O` channel's torch entry (minutes, light) | the torch lit, true state |
| Creatures | `creatureCount`, `nearCreatureType`, `nearCreatureDY`, `nearCreatureDX`, `nearCreatureStrength`, `nearCreatureDamage` | a change in combat |

**Reading safely.** Both children follow the same rule (`gym/docs/findings/ram-signals.md`): read `displayFunction` (0x02B2) **first**, and read no other memory until the game is live (`0xCE66` for LOOK, `0xD495` for EXAMINE). Reading memory before the machine finishes booting crashes MAME outright. They share the boot sequence too: wait a fixed number of frames, press CR CR to leave the demo loop, and only then start posting commands.

**Reading a run.** For each command, the analysis starts from the state just before it was posted. It then finds the first frame where *matched* is set, and the first frame where any watched field changes. That second one is the effect, and how far it is from the post is the measurement.

**Why read RAM directly.** Both children read memory rather than going through the Python environment, because the environment sends neither `perfectMatch` nor every frame — it only sends a record when something changes, so it cannot show *when* inside a command the state moved.

## The experiments

Each child is planned in its own folder and states its own schedule, watched fields, control, and success criteria:

- [`lighting-torch/`](lighting-torch/README.md) — the deterministic anchor.
- [`fighting-monster/`](fighting-monster/README.md) — the opportunistic case.

They share the log format and the analysis described above; neither re-describes them.

## Build order

Nothing is built yet — this is a scaffold of structure and plans. The division above gives the order of work:

1. **The shared harness first.** One observation method and one log format, designed before either child, so both use it unchanged. This is the piece that is easy to duplicate by accident and should not be.
2. **`lighting-torch/` second.** The anchor runs first, because if the harness cannot show a *known* effect landing after a *known* match, no later result can be trusted.
3. **`fighting-monster/` third.** Reuses the harness unchanged; only its schedule and watched fields differ.
4. **Read the two traces together.** The answer comes from comparing them, not from either one alone.

## Success criteria

The sandbox succeeds when the traces answer these:

- Does `perfectMatch` fire on a command that changes nothing? (If yes, matched ≠ changed is proven.)
- How many frames after the post does *matched* arrive, and how variable is it?
- How many frames after the post does *changed* arrive, and how does it relate to *matched*?
- For the torch, does `PULL` show as a change in the holdings columns only, with the light columns unchanged until `USE`? (This is the scalar-only-diff miss, reproduced.)
- For combat, is there a trace where an `ATTACK` changed a creature field, and how far after the post?

This is a measurement, not a pass or fail. What comes out is the timing, and whatever it says about the step unit.

## Open questions

- **The exact signal.** If `perfectMatch` isn't reliable, is the command echo (when `command_text` clears) better — and worth sending over the wire?
- **Waiting for quiet.** Is "stop once the watched fields sit unchanged for a few frames" a workable rule? How many frames? A trace can be re-read with a smaller field set to see whether it goes quiet while the clocks keep ticking.
- **Where the wait belongs.** In the environment, in a wrapper, or in the Lua plugin (which could send a record when a command is consumed)?
- **The no-action window.** A no-action step has no `perfectMatch`, so its window has to be a fixed length. How long should it be, next to a command's?
- **Window length and confidence.** Should the window shrink as the agent grows more sure of a cause? A window that changes length makes the reward's time discount harder to reason about — does that matter in practice?

## Running

Not built yet. When the shared harness lands, both children run from it; the plugin's `-pluginspath` must list the sandbox directory plus MAME's system plugins directory (since `boot.lua` lives there — see `daggorath_gym/paths.py`).



