# Frame Reporting

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The state channel is change-gated: it writes a record only when something differs from the last snapshot, and writes nothing at all while the game sits still. That hides the frame number and the still frames, which the agent needs to attribute causes — the argument is in [`../1_discussions/frame-reporting.md`](../1_discussions/frame-reporting.md). This plan changes the channel to number every changed frame.

The scope is the wire format and its two sides — the Lua sampler and `MameOperator`. The producer gains a frame marker and writes one report per changed frame; the reader parses the marker and returns a list of changes, one entry per changed frame. The environment's `reset`/`step` keep the latest state from the list.

Out of scope: the parser schema and the step-unit choice. Those are separate plans.

## Build order

Each stage ships with a verification test, and each is gated on the one before:

1. **Producer.** The sampler writes the frame marker and change-gated content on every changed frame. Verified by `tests/test_emulator.py`, reading the raw FIFO bytes and checking the wire format.
2. **Reader.** `recv()` returns a list of changes, one entry per changed frame — a changed frame as `(frame_number, state)`; an empty frame yields no entry, and its presence shows as a gap between consecutive frame numbers. Gated on the producer test. Verified by a `recv()` test in `tests/test_emulator.py`.
3. **Environment.** `reset`/`step` keep the latest state from the list, keeping their outward behavior. Gated on the reader test. Verified by the existing `test_environment.py`.

## The wire format

Every changed frame emits one report, in this order: a **frame marker** — the tag `F` followed by a 4-byte little-endian frame number, the sampler's own counter — then the **changed content** — the `S`/`B`/`T`/`M`/`C`/`O`/`H` records that differ from their snapshots, in their existing forms — and nothing else. A frame with no changes emits nothing.

The buffered reports are written and flushed once per reporting cadence, so a frame's content can never lag its marker. There is no end-of-frame tag: the next marker is the boundary, and the atomic flush is what keeps that boundary safe. An empty frame emits nothing — the gap between its neighbours' frame numbers is the record of it.

## The producer

The sampler's `_onFrame` loses its `report_every_frame` branch and becomes uniform:

```
_onFrame()
    → samples the numeric frame, the command-area pixels, and the world channels, every frame
    → computes which of them changed against the snapshots
    → when anything changed, appends the frame marker and each changed record to the report buffer
    → flushes the buffer once the reporting cadence elapses
    → updates the snapshots
```

The `report_every_frame` field and the `REPORT_EVERY_FRAME` environment variable go away, and so does the `frame_sampling_rate` knob — the sampler always samples every frame. The snapshot comparison stays; it keeps the content change-gated, and now the marker is change-gated too.

The reporting cadence — how often the buffered reports are flushed — is `reporting_cadence`, defaulting to 1 (flush every report). It is client-configurable: `IpcConfig.reporting_cadence` flows through the `REPORTING_CADENCE` environment variable to the plugin entry, which passes it to `beginWatching`.

A producer test in `tests/test_emulator.py` reads the raw FIFO bytes the sampler writes — not `recv` — and checks the wire format: an `F` marker on every changed frame, an advancing 4-byte little-endian frame number with gaps where empty frames were skipped, and change-gated content only between markers. It measures the frame rate over 10 s after the game starts and asserts the frame number advances at ~60 Hz.

## The reader

`MameOperator` turns the wire into a list of changes:

```
recv()
    → reads records, treating the next F marker as the frame boundary
    → returns a list of changes, one entry per changed frame
    → a changed frame yields (frame_number, state); an empty frame yields nothing, and the gap in frame numbers marks it
```

The reader reports every change — each as the new state — and drops the frames where nothing changed, never aggregating; an empty frame shows only as the gap between the frame numbers on either side of it. The consumer decides: the environment keeps the latest state, the sandbox counts the gaps to measure timing. `_RECORD_LENGTHS` gains the `F` tag at five bytes — the tag plus the 4-byte number — and the number is unpacked little-endian.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/frame-reporting.md` | The argument for every-frame reporting and the frame number |
| `../1_discussions/extensibility.md` | The open question this plan answers |
| `../3_decisions/ipc-hybrid.md` | The FIFO write path this plan changes |
| `../findings/ipc.md` | The blocking concern behind change detection |
