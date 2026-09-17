# Frame Reporting

_13 Sep 2026_

## Decision

The state channel writes an `F` marker — a 4-byte little-endian frame number — every frame, followed by the frame's full content records (`B`, `M`, `C`, `O`, `H`). The Python reader dedups unchanged frames. `MameOperator.recv()` returns a `list[tuple[int, DaggorathState]]`, one entry per frame, and the environment's `reset`/`step` keep the latest state from that list. Liveness is the reader's 30-second read timeout; there is no heartbeat.

## Why

- **The frame number must come from the sampler.** A reader counts records, not time. Only the sampler's counter ticks every frame, so only it can say which frame a change happened on.
- **Every frame is reported so the reader can count time.** Reporting the marker every frame gives Python a real ticker. The environment counts frames directly for the no-op window instead of inferring them from gaps between changes.
- **Dedup happens in Python.** The sampler reports the frame's full content every frame, and the reader drops unchanged frames. The change gate moved off Lua, where it hid the ticker, onto Python, where the environment already dedups perceived states.
- **The reader is a pipe, not a judge.** It reports every frame as `(frame_number, state)` and never decides a frame is uninteresting. The environment dedups and groups.
- **No heartbeat; the timeout is the liveness signal.** A stuck MAME surfaces as a `TimeoutError` from the reader's `_STATE_READ_TIMEOUT`.
- **The step unit is now settled.** The sampler reports every frame, and the step loop groups them. The environment's `step()` waits for `command_parser_position` to leave and return to its idle value for a command, or waits a fixed window for a no-op, then returns the perceived changes under `info["changes"]` and their frame numbers under `info["frames"]`.

## What Changed

- `emulation/plugins/daggorath/state.lua` — writes the `F` marker and the frame's full content every frame; flushes reports at `reporting_cadence`.
- `emulation/plugins/daggorath/init.lua` — reads `REPORTING_CADENCE` and passes `reporting_cadence` to `beginWatching`.
- `daggorath_gym/emulator.py` — `recv()` returns a list of frames, one entry per frame; `IpcConfig.reporting_cadence`.
- `daggorath_gym/environment.py` — `step()` waits for the command to settle or the no-op window, then returns the deduped perceived changes under `info["changes"]` and frame numbers under `info["frames"]`.
- `tests/test_emulator.py` — producer test (every frame reported) and reader test (list of frames).
- `sandbox/torch-light/server.py` — consumes the frame list.
