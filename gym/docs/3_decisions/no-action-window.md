# No-Action Window

_17 Sep 2026_

## Decision

A step now receives frames one of two ways. A command step discards the pre-command backlog, then collects frames until `command_parser_position` completes its round trip: it leaves idle when the game starts typing and returns when the handler finishes. A no-op step drains the backlog, then collects exactly 60 fresh frames, one second of game time. Both return the distinct perceived changes under `info["changes"]` with frame numbers under `info["frames"]`.

## Why

- The sampler used to report only changed frames, so Python could not count still frames; a fixed window had to be inferred from the gaps between changes. Reporting every frame gives Python a ticker it can count directly.
- The two step kinds stop differently. A command's end is an event, the position returning to idle. A no-op's end is a duration, 60 frames. One receive method cannot serve both, so the step picks by what it sent.
- The backlog between steps is not part of either step. A command drops frames before the typing begins; a no-op drains to the newest frame before counting. Without that, think-time motion would leak into the change set.

## What Changed

- `emulation/plugins/daggorath/state.lua` — reports every frame in full, no dedup.
- `daggorath_gym/emulator.py` — `recv()` returns one entry per frame.
- `daggorath_gym/environment.py` — `_receive_until_settled` for commands, `_receive_for_window` for no-ops, and `_WAIT_FRAMES` = 60.
- `tests/test_emulator.py` — producer and reader tests assert every frame is reported.

## Reference Documents

| Document | What it contains |
|---|---|
| `frame-reporting.md` | The every-frame wire protocol this window depends on |
| `../../../agent/sandbox/command-latency/README.md` | The "no-action window" open question this answers |
