# Frame Reporting

_13 Sep 2026_

## Decision

The state channel writes an `F` marker — a 4-byte little-endian frame number — only on the frames where a channel changed, followed by the changed `S`/`B`/`T`/`M`/`C`/`O`/`H` records. A frame with no change writes nothing; the gap between consecutive frame numbers is the record of the still frames. `MameOperator.recv()` returns a `list[tuple[int, DaggorathState]]`, one entry per changed frame, and the environment's `reset`/`step` keep the latest state from that list. Liveness is the reader's 30-second read timeout; there is no heartbeat.

## Why

- **The frame number must come from the sampler.** A reader counts records, not time — from Python's seat, the frames a change-gated channel hides never existed. Only the sampler's counter ticks every frame, so only it can say which frame a change happened on.
- **Empty frames are dropped because the gap is the record.** The gap between consecutive numbers says "frames passed, nothing changed," so an explicit empty marker adds nothing. The frame notifier already guarantees completeness — it fires once per frame and counts the frame before any gate — so a missed frame would be a bug the marker could only detect, never prevent.
- **Change detection was about bytes, not frames.** The original objection was to rewriting the full ~154-byte state every idle frame. Content stays change-gated, and the frame number, written only on the frames that changed, costs next to nothing.
- **The reader is a pipe, not a judge.** It reports every change as `(frame_number, state)` and never decides a change is uninteresting — the consumer does. The environment keeps the latest state; the sandbox counts the gaps to measure stillness.
- **No heartbeat; the timeout is the liveness signal.** The empty marker's one remaining value was certainty against missed frames, which the notifier already provides. A stuck MAME surfaces as a `TimeoutError` from the reader's `_STATE_READ_TIMEOUT`.
- **The step unit is now settled.** The sampler still reports every changed frame and leaves the grouping to the step loop. The environment's `step()` waits for `command_parser_position` to leave and return to its idle value, then returns the perceived changes under `info["changes"]` and their frame numbers under `info["frames"]`. One step spans one command.

## What Changed

- `emulation/plugins/daggorath/state.lua` — writes the `F` marker only when a channel changed; flushes reports at `reporting_cadence`.
- `emulation/plugins/daggorath/init.lua` — reads `REPORTING_CADENCE` and passes `reporting_cadence` to `beginWatching`.
- `daggorath_gym/emulator.py` — `recv()` returns a list of changes; `IpcConfig.reporting_cadence`.
- `daggorath_gym/environment.py` — `step()` waits for `command_parser_position` to leave and return to idle, then returns the perceived changes (repeats dropped) under `info["changes"]` and frame numbers under `info["frames"]`.
- `tests/test_emulator.py` — producer test (frame-number gaps) and reader test (list of changes).
- `sandbox/torch-light/server.py` — consumes the list through a `_receive_latest_state` helper.
