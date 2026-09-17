# No-Action Window

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

A no-op step is a factored action that sends no command. Today it advances one change and returns an empty change set. This plan gives it a window instead: the step waits one second of game time and returns the world's perceived changes over that window, in the same `info["changes"]` and `info["frames"]` shape a command step returns. That window is the inaction baseline the attribution work needs, and it answers the "no-action window" open question in the command-latency sandbox.

The scope is the no-op path of `step()` only. The command path already waits for its command to settle and stays as it is. The action space stays as it is: a no-op is still a syntactically invalid pair that sends nothing.

## The window

One second is 60 frames at the game's 60 Hz. It is a constant, not a parameter; letting the agent choose the length is a later question.

The no-op step collects every frame the sampler reports across the window, collapses them to the distinct perceived states, and returns those under `info["changes"]` with the frame where each began under `info["frames"]`. The observation is the last perceived state, exactly as a command step returns.

## Counting frames

The sampler reports every frame, so the step counts frames directly. The no-op drains the backlog that accumulated since the previous step, reads the newest frame number as its start, and then collects exactly 60 fresh frames. There is no gap inference and no slop.

## Where it lands

In `environment.py`: a `_WAIT_FRAMES` constant holding 60, a `_receive_for_window` method that drains the backlog and then collects exactly 60 fresh frames, and the no-op path of `step()` calls it instead of advancing one change. The deduplication reuses `_dedupe_perceived`.

## Reference Documents

| Document | What it contains |
|---|---|
| `../3_decisions/frame-reporting.md` | The command half of the step contract this plan completes |
| `../1_discussions/extensibility.md` | The MameOperator continuous stream, the alternative for a longer baseline |
| `../../../agent/sandbox/command-latency/README.md` | The "no-action window" open question this plan answers |
