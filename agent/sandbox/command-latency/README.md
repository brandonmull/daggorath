# Command Latency

_Observe the three signals of a command — matched, written, executed — and their temporal relation, to decide how one training step should be defined._

The design argument behind it — what a transition is, and why the three moments matter — is in [`../../docs/1_discussions/knowledge-representation.md`](../../docs/1_discussions/knowledge-representation.md).

This sandbox is agent-side, not part of the environment. It nails down the basic unit the agent's experience is built from — the same job as its sibling [`../causal-diff/`](../causal-diff/README.md). It reads state through the environment's reporting (`MameOperator` with `report_every_frame`), but what it measures belongs to the agent's knowledge, not to the game.

## Goal

Measure the three signals of a command and how far apart they are:

- **Matched** — the parser finishes matching the line. `perfectMatch` (0x027B) flags this.
- **Written** — the game writes its response to the command area: the echoed command, or `???` on rejection. `command_text` (screen-derived) carries this.
- **Executed** — the game actually executes the command and the state changes as a result.

The measurement is the gap between *matched* and *executed*: when the command is recognized, how long until its effect lands — and is that gap always about the same, or unrelated? *Matched* is a RAM flag; *executed* has no flag — it is the effect, read off the state change — and the handler running in between is inferred, not observed. *Written* is a third signal, already on the wire, checked against the other two. Why that gap matters to the agent's knowledge is in the design doc linked above.

## What the code does today

- `gym/daggorath_gym/emulator.py` — `MameOperator` keeps `send` and `recv` separate, and `IpcConfig(report_every_frame=True)` makes the sampler write a numeric frame every frame, not only on change. That is the hook the sandbox uses to watch frames after a command.
- `gym/daggorath_gym/state.py` — `FIELDS` is a list of `StateField(name, offset, width, perceived)` grouped by category, and is the extension point: a new fact is filed into its category and picked up on both sides of the wire.
- `perfectMatch` is **not yet on the wire**: the sixteen `FIELDS` do not include the parser's flags. What is shipped is *written* — `command_text` (the command-area echo, decoded from screen pixels) and the derived `command_rejected` (`"???" in command_text`) — and *executed*, the state change.
- `agent/sandbox/causal-diff/server.py` — its probe settles with `_step_until_settled(env, obs, predicate)`, capped at `_SETTLE_STEPS = 100` no-op frames, waiting for a *command-specific* observable (hand holds torch / dungeon brightens). That is right for a probe checking a known answer, but a per-command predicate does not scale to 154 commands.

Of the three signals, *written* and *executed* are on the wire; *matched* is not. Neither `perfectMatch` nor `command_text` is certainly *executed*: the echo filling marks the command going in and the echo clearing marks the parser finishing with it — plausibly closer to "processing complete," but still not "state changed."

## How the problem divides

It is the same question asked twice — *for this command, when did it match, and when did the state change?* So the sandbox is one shared harness with two sets of parameters, not two separate experiments. Everything the two commands have in common lives here; only what differs lives in a child folder.

```
command-latency/
├── README.md            this document — the shared framing, the harness, and the division
├── lighting-torch/      experiment 1 — the deterministic anchor
└── fighting-monster/    experiment 2 — the opportunistic case
```

Three things are shared, and belong to neither child alone:

- **The observation method** — how *matched* and *changed* are read from the environment each frame, and how a run is logged.
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

**Reading the three signals.** Nothing in memory says "the handler ran," so *executed* has no flag — it is the effect, read off the state change. The other two can be read: the parser's recognition flag `perfectMatch` (0x027B) marks *matched*, and the command-area text `command_text` marks *written*. The handler running between them is inferred, not observed. Every frame records:

| Group | Columns | Witnesses |
|---|---|---|
| Consumption | `gameMode`, `perfectMatch`, `foundMatch`, `numWords`, `whereToPrint`, `nextToParse`, `comTextCursor` | *matched*, and the parser's progress |
| Display | `displayFunction` | the EXAMINE / LOOK view switch |
| Player | `atCellX`, `atCellY`, `atHeading`, `effectiveLightPhysical`, `playerStrength`, `m0221`, `heartBeatInterval` | movement, light, body |
| Holdings | `hands`, `pack` — the `O` channel's decoded identities | an object moved between pack and hand |
| Torch | `lit_torch` — the `O` channel's torch entry (minutes, light) | the torch lit, true state |
| Creatures | the `C` channel (`alive`/`type`/`X`/`Y`), plus the engaged creature's `damage`/`strength` | a hit or a death |

**Reading safely.** The production plugin already gates on `displayFunction` and primes the keyboard itself, so the sandbox reads state through the environment and never touches raw RAM — the readiness crash is the environment's problem, not the sandbox's.

**Reading a run.** For each command, the analysis starts from the state just before it was posted. It then finds the first frame where *matched* is set, and the first frame where any watched field changes. That second one is the effect, and how far it is from the post is the measurement.

**Why read through the environment.** `report_every_frame` makes the sampler write a frame every frame, and `FIELDS` is the extension point, so the sandbox can read frame-by-frame and ask for new facts (`perfectMatch`) without a plugin of its own.

## The experiments

Each child is planned in its own folder and states its own schedule, watched fields, control, and success criteria:

- [`lighting-torch/`](lighting-torch/README.md) — the deterministic anchor.
- [`fighting-monster/`](fighting-monster/README.md) — the opportunistic case.

They share the log format and the analysis described above; neither re-describes them.

## Build order

The torch and perception refactor shipped first (see `gym/docs/3_decisions/perception.md`). What remains, in order:

1. **The observation wrapper.** A `FrameObservation` over `MameOperator` with `report_every_frame=True` — one frame per read, with a frame counter. Shared, built before either child, and easy to duplicate by accident if not.
2. **The parser schema.** Add the command-consumption fields (`perfect_match` and its companions) per `gym/docs/2_plans/command-consumption.md`, so *matched* is on the wire.
3. **The shared harness.** One log format and one analysis, built before either child.
4. **`lighting-torch/`.** The anchor runs first, because if the harness cannot show a *known* effect landing after a *known* match, nothing later can be trusted.
5. **`fighting-monster/`.** Reuses the harness unchanged; its watched fields need the combat-detection fields per `gym/docs/2_plans/combat-detection.md`.
6. **Read the two traces together.** The answer comes from comparing them, not from either one alone.

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

Not built yet. When the harness lands, both children run through `MameOperator` (the environment's plugin), so no `-pluginspath` wiring is needed — `MameOperator` already lists the project and MAME's system plugin directories.



