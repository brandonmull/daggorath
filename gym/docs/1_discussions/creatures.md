# Creature Detection — Discussion

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Open questions

- **Read atomicity.** Each byte read is atomic, but a 32-slot scan spans many instructions. The frame notifier runs at the frame boundary while the 6809 is halted, so a single-pass scan is assumed atomic — a torn snapshot would be a one-frame position glitch, noise the agent averages over. `gym/sandbox/read-atomicity/` will confirm.

## Reference

- Plan: `../2_plans/creatures.md`
