# Frame Reporting

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The state channel is change-gated: it writes a record only when something differs from the last snapshot, and writes nothing at all while the game sits still. That hides the frame number and the still frames, which the agent needs to attribute causes — the argument is in [`../1_discussions/frame-reporting.md`](../1_discussions/frame-reporting.md). This plan changes the channel to report every frame.

The scope is the wire format and its two sides — the Lua sampler and `MameOperator`. The producer gains a frame marker and always writes one report per game frame; the reader parses the marker, skips empty frames, and returns the frame number alongside the state. The environment's `reset`/`step` unpack the pair.

Out of scope: the sandbox's frame-by-frame reader (a subclass that keeps empty frames rather than skipping them), the parser schema, and the step-unit choice. Those are separate plans.

## Build order

Each stage ships with a verification test, and each is gated on the one before:

1. **Producer.** The sampler writes the frame marker and change-gated content every frame. Verified by `tests/test_frame_reporting.py`, reading the raw FIFO bytes and checking the wire format.
2. **Reader.** `recv()` assembles a whole frame, skips empty ones, and returns `(frame_number, state)`. Gated on the producer test. Verified by a `recv()` test.
3. **Environment.** `reset`/`step` unpack the pair, keeping their outward behavior. Gated on the reader test. Verified by the existing `test_environment.py`.

## The wire format

Every game frame emits one report, in this order: a **frame marker** — the tag `F` followed by a 4-byte little-endian frame number, the sampler's own counter — then the **changed content** — the `S`/`B`/`T`/`M`/`C`/`O`/`H` records that differ from their snapshots, in their existing forms — and nothing else. A frame with no changes emits the marker alone.

The buffered reports are written and flushed once per reporting cadence, so a frame's content can never lag its marker. There is no end-of-frame tag: the next marker is the boundary, and the atomic flush is what keeps that boundary safe. An empty frame is the marker alone — five bytes.

## The producer

The sampler's `_onFrame` loses its `report_every_frame` branch and becomes uniform:

```
_onFrame()
    → samples the numeric frame, the command-area pixels, and the world channels, every frame
    → computes which of them changed against the snapshots
    → appends the frame marker and each changed record to the report buffer
    → flushes the buffer once the reporting cadence elapses
    → updates the snapshots
```

The `report_every_frame` field and the `REPORT_EVERY_FRAME` environment variable go away, and so does the `frame_sampling_rate` knob — the sampler always samples every frame. The snapshot comparison stays; it keeps the content change-gated even while the marker is every-frame.

The reporting cadence — how often the buffered reports are flushed — is `reporting_cadence`, defaulting to 1 (every frame). It is client-configurable: `IpcConfig.reporting_cadence` flows through the `REPORTING_CADENCE` environment variable to the plugin entry, which passes it to `beginWatching`.

A producer-only integration test, `tests/test_frame_reporting.py`, reads the raw FIFO bytes the sampler writes — not `recv` — and checks the wire format: an `F` marker on every frame, an advancing 4-byte little-endian frame number, empty frames as a marker alone, and change-gated content only between markers. It measures the frame rate over 10 s after the game starts and asserts the frame number advances at ~60 Hz.

## The reader

`MameOperator` gains the marker and returns the frame number alongside the state:

```
recv()
    → reads records, treating the next F marker as the frame boundary
    → assembles every content record of the frame into one state
    → skips empty frames (a marker with no content)
    → returns the frame number and the state for the next changed frame
```

`_RECORD_LENGTHS` gains the `F` tag at five bytes — the tag plus the 4-byte number — and the number is unpacked little-endian.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/frame-reporting.md` | The argument for every-frame reporting and the frame number |
| `../1_discussions/extensibility.md` | The open question this plan answers |
| `../3_decisions/ipc-hybrid.md` | The FIFO write path this plan changes |
| `../findings/ipc.md` | The blocking concern behind change detection |
