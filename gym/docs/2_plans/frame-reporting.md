# Frame Reporting

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The state channel is change-gated: it writes a record only when something differs from the last snapshot, and writes nothing at all while the game sits still. That hides the frame number and the still frames, which the agent needs to attribute causes — the argument is in [`../1_discussions/frame-reporting.md`](../1_discussions/frame-reporting.md). This plan changes the channel to report every frame.

The scope is the wire format and its two sides — the Lua sampler and `MameOperator`. The producer gains a frame marker and always writes one report per game frame; the reader parses the marker, skips empty frames, and returns the frame number alongside the state. The environment's `step` keeps its outward behavior.

Out of scope: the sandbox's frame-by-frame reader (a subclass that keeps empty frames rather than skipping them), the parser schema, and the step-unit choice. Those are separate plans.

## The wire format

Every game frame emits one report, in this order: a **frame marker** — the tag `F` followed by a 4-byte little-endian frame number, the sampler's own counter — then the **changed content** — the `S`/`B`/`T`/`M`/`C`/`O`/`H` records that differ from their snapshots, in their existing forms — and nothing else. A frame with no changes emits the marker alone.

The whole report is written and flushed once per frame, so a frame's content can never lag its marker. There is no end-of-frame tag: the next marker is the boundary, and the atomic flush is what keeps that boundary safe. An empty frame is the marker alone — five bytes.

## The producer

The sampler's `_onFrame` loses its `report_every_frame` branch and becomes uniform:

```
_onFrame()
    → samples the numeric frame, the command-area pixels, and the world channels
    → computes which of them changed against the snapshots
    → writes the frame marker with the current frame number
    → writes each changed record
    → flushes once
    → updates the snapshots
```

The `report_every_frame` field and the `REPORT_EVERY_FRAME` environment variable go away; the plugin entry stops reading and passing them. The snapshot comparison stays — it is what keeps the content change-gated even while the marker is every-frame.

## The reader

`MameOperator` gains the marker and returns the frame number alongside the state:

```
recv()
    → reads records until it reaches a frame that carried content
    → skips empty frames
    → returns the frame number and the state for the next changed frame
```

`_RECORD_LENGTHS` gains the `F` tag at five bytes — the tag plus the 4-byte number — and the number is unpacked little-endian. The environment's `reset` and `step` unpack the pair and ignore the number; their outward behavior — send, read the next change, return it — is unchanged. The tests that call `recv` directly unpack the pair too, and the every-frame test is rewritten to assert the heartbeat and the advancing frame number.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../1_discussions/frame-reporting.md` | The argument for every-frame reporting and the frame number |
| `../1_discussions/extensibility.md` | The open question this plan answers |
| `../3_decisions/ipc-hybrid.md` | The FIFO write path this plan changes |
| `../findings/ipc.md` | The blocking concern behind change detection |
