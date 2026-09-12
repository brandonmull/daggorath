# Extensibility

_See [overview.md](../../../docs/overview.md) for project context and architecture._

This plan makes the environment extensible for any future consumer, not just the trainer, and answers the questions in `../1_discussions/extensibility.md`. A consumer never extends — its need prompts the environment to add a fact. The plan does two things: makes the schema the extension point and adds a reporting cadence. Narrowing the perceived state stays the agent's job.

## The schema is the extension point

A fact is added by filing it into the field list (`FIELDS` in Python, `SCHEMA` in Lua); both sides pick it up automatically. The list is grouped by category — mode, position, light, torch, body, heart, wizard — each group named with a comment on both sides, so a new fact lands in its place and the ordering reads at a glance. Two existing fields move to keep the groups together (`display_function` into mode, `player_fainting` into body).

## Report every frame

A new flag, `report_every_frame`, is off by default — the environment reports only when something changes; turned on, it reports every frame. It applies to the numeric frame, not the world channels, which keep their own change gate. It lives on the operator's configuration and reaches the sampler the way the existing IPC settings do — an environment variable the plugin entry reads. The trainer keeps the default; a consumer that needs to watch timing turns it on.

## The perceived state stays whole

The environment always reports the full perceived state. Shaping it into the view a lesson needs — dropping channels, keeping only doors, isolating the nearest creature — is the agent's job, done imperatively in its own code. There is no reduction interface to support.

## Read state apart from commands

A consumer that wants state apart from its command uses `MameOperator`, where `send` and `recv` are already separate.

## Reference Documents

| Document | What it contains |
|---|---|
| `../1_discussions/extensibility.md` | The discussion this plan answers |
| `../3_decisions/state.md` | The state module and wire format as it stands |

