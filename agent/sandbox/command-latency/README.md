# Command Latency

_Observe the three signals of a command — matched, written, executed — and their temporal relation, to decide how one training step should be defined._

The design argument behind it — what a transition is, and why the three moments matter — is in [`../../docs/1_discussions/knowledge-representation.md`](../../docs/1_discussions/knowledge-representation.md).

This sandbox is agent-side, not part of the environment. It nails down the basic unit the agent's experience is built from — the same job as its sibling [`../causal-diff/`](../causal-diff/README.md). It reads state through the environment's reporting — `MameOperator`, whose `recv()` reports each changed frame with its frame number — but what it measures belongs to the agent's knowledge, not to the game.

## Goal

Measure the three signals of a command and how far apart they are:

- **Matched** — the parser finishes matching the line. `command_parser_word_count` (0x0279) jumps from 0 when this happens.
- **Written** — the game writes its response to the command area: the echoed command, or `???` on rejection. `command_area_text` (screen-derived) carries this.
- **Executed** — the game runs the command handler to completion.

The measurement is the gap between *matched* and *executed*: when the command is recognized, how long until its effect lands — and is that gap always about the same, or unrelated? *Matched* is a RAM flag; *executed* has no flag — it is the effect, read off the state change — and the handler running in between is inferred, not observed. *Written* is a third signal, already on the wire, checked against the other two. Why that gap matters to the agent's knowledge is in the design doc linked above.

## What the code does today

- `gym/daggorath_gym/emulator.py` — `MameOperator` keeps `send` and `recv` separate, and the frame number advances every frame. That is the hook the sandbox uses to watch frames after a command.
- `gym/daggorath_gym/state.py` — `FIELDS` is a list of `StateField(name, offset, width, perceived)` grouped by category, and is the extension point: a new fact is filed into its category and picked up on both sides of the wire.
- All three signals ship: *matched* is the `command_parser_word_count` jump in the `consumption` category in `FIELDS` (`command_parser_matched_exactly`, `command_parser_matched`, `command_parser_word_count`, `where_to_print`); *written* is `command_area_text` (the command-area echo, decoded from screen pixels) and the derived `command_rejected` (`"???" in command_area_text`); *executed* is the state change.
- `agent/sandbox/causal-diff/server.py` — its probe settles with `_step_until_settled(env, obs, predicate)`, capped at `_SETTLE_STEPS = 100` no-op frames, waiting for a *command-specific* observable (hand holds torch / dungeon brightens). That is right for a probe checking a known answer, but a per-command predicate does not scale to 154 commands.

Neither `command_parser_word_count` nor `command_area_text` is certainly *executed*: the echo filling marks the command going in and the echo clearing marks the parser finishing with it — plausibly closer to "processing complete," but still not "state changed."

## The executed signal

Since the sandbox first ran, the executed moment has been found: `command_parser_position` (0x0211) snaps back to 0x02F1 once a command has run, even one that does nothing visible. Paired with the `???` the game prints (`command_rejected`) it separates executed from rejected. It is not on the wire yet; the full field entry is in [`../../../gym/docs/findings/ram-signals.md`](../../../gym/docs/findings/ram-signals.md).

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
| `fighting-monster/` | `ATTACK LEFT`, `ATTACK RIGHT` | opportunistic | The realistic case: the effect appears only when a creature is engaged, so the trace must be read, not predicted. |

If the anchor shows *changed* tracking *matched* by a small, consistent gap, and the opportunistic case shows *matched* **without** *changed* when nothing is engaged, then the three moments are separated and the step unit can be chosen.

## The shared core

**Reading the three signals.** Nothing in memory says "the handler ran," so *executed* has no flag — it is the effect, read off the state change. The other two can be read: the parser's word-table counter `command_parser_word_count` (0x0279) marks *matched*, and the command-area text `command_area_text` marks *written*. The handler running between them is inferred, not observed. Every frame records:

| Group | Columns | Witnesses |
|---|---|---|
| Consumption | `gameMode`, `commandParserMatched`, `commandParserMatchedExactly`, `commandParserWordCount`, `whereToPrint`, `commandParserPosition`, `comTextCursor` | matched (`commandParserWordCount`), executed (`commandParserPosition`), and the parser's progress |
| Display | `displayFunction` | the EXAMINE / LOOK view switch |
| Player | `atCellX`, `atCellY`, `atHeading`, `effectiveLightPhysical`, `playerStrength`, `m0221`, `heartBeatInterval` | movement, light, body |
| Holdings | `hands`, `pack` — the `O` channel's decoded identities | an object moved between pack and hand |
| Torch | `lit_torch` — the `O` channel's torch entry (minutes, light) | the torch lit, true state |
| Creatures | the `C` channel (`alive`/`type`/`X`/`Y`/`damage`/`strength`) | a hit or a death |

**Reading safely.** The production plugin already gates on `displayFunction` and primes the keyboard itself, so the sandbox reads state through the environment and never touches raw RAM — the readiness crash is the environment's problem, not the sandbox's.

**Reading a run.** For each command, the analysis starts from the state just before it was posted. It then finds the first frame where *matched* is set, and the first frame where any watched field changes. That second one is the effect, and how far it is from the post is the measurement.

**Recording, then reading.** A session decides nothing while it runs: it records every changed frame's columns and every post. The interpretation — which columns count as a command's effect, where the echo appeared, where the parser matched — is a second pass over the written trace, so the same trace can be read again with a different field set.

**Repeating a session.** A session is one launch. The torch child is a fresh boot, and the game's opening state is deterministic; the fighting child resumes a saved state on the CoCo 2B. Either way, the same schedule replays from the same situation every time, and a run is several sessions whose spread of offsets is the variability.

**Why read through the environment.** The sampler writes a frame marker with its frame number on every frame a channel changed, and `FIELDS` is the extension point, so the sandbox reads frame by frame and asks for new facts (`command_parser_word_count`) through the environment rather than a plugin of its own.

## The experiments

Each child is planned in its own folder and states its own schedule, watched fields, control, and success criteria:

- [`lighting-torch/`](lighting-torch/README.md) — the deterministic anchor.
- [`fighting-monster/`](fighting-monster/README.md) — the opportunistic case.

They share the log format and the analysis described above; neither re-describes them. The first run's readings are in [`../../docs/findings/command-latency.md`](../../docs/findings/command-latency.md).

## Build order

The torch and perception refactor shipped first (see `gym/docs/3_decisions/perception.md`). What remains, in order:

1. **The observation wrapper.** Shipped — `frame_observation.py`'s `FrameObservation` reads `recv()`'s `(frame_number, state)` change list: one change per read, with the frame number and the gap since the last change. Shared, built before either child, and easy to duplicate by accident if not.
2. **The parser schema.** Shipped — `matched` is on the wire (`command_parser_word_count` and its companions, the `consumption` category).
3. **The shared harness.** Shipped — `harness.py`: one log format, one analysis, and the session loop that reboots between samples.
4. **`lighting-torch/`.** Shipped — the anchor, which records the torch sequence in three fresh sessions.
5. **`fighting-monster/`.** Shipped — the rotation schedule and its watched-field set, with the combat-detection fields now on the wire.
6. **Read the two traces together.** The answer comes from comparing them, not from either one alone.

## Success criteria

The sandbox succeeds when the traces answer these:

- Does a command that changes nothing still match? (If yes, matched ≠ changed is proven.)
- How many frames after the post does *matched* arrive, and how variable is it?
- How many frames after the post does *changed* arrive, and how does it relate to *matched*?
- For the torch, does `PULL` show as a change in the holdings columns only, with the light columns unchanged until `USE`? (This is the scalar-only-diff miss, reproduced.)
- For combat, is there a trace where an `ATTACK` changed a creature field, and how far after the post?

This is a measurement, not a pass or fail. What comes out is the timing, and whatever it says about the step unit.

## Settled questions

The two decisions that record these are [`frame-reporting.md`](../../../gym/docs/3_decisions/frame-reporting.md) and [`no-action-window.md`](../../../gym/docs/3_decisions/no-action-window.md).

- **Waiting for quiet.** The wait does not watch the fields go quiet. A command step waits for `command_parser_position` to leave idle and return; that round trip is the settle signal. A no-op step waits a fixed window instead.
- **Where the wait belongs.** In the environment's `step()`. The Lua sampler reports every frame, and the environment groups them and drops unchanged frames.
- **The no-action window.** One second, 60 frames, a fixed constant. A no-op drains the pre-step backlog and then collects 60 fresh frames.
- **Window length and confidence.** The window is fixed. An agent-chosen length was considered and deferred; a fixed window keeps the reward's time discount simple.

## Running

```bash
python agent/sandbox/command-latency/lighting-torch/run.py
python agent/sandbox/command-latency/fighting-monster/run.py
```

Both children run through `MameOperator` (the environment's plugin), so no `-pluginspath` wiring is needed — `MameOperator` already lists the project and MAME's system plugin directories. The torch experiment records three fresh sessions; each session boots the game, waits for live play, posts its schedule, and writes a trace to `logs/`. The fighting experiment first needs the by-hand saved state `monster-near` (see its README), then records three sessions that resume that state.



