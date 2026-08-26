# Daggorath — Working Notes

Scratchpad for big-picture decisions, continued across sessions. Not a spec.

## Settled

One `daggorath` repo holds two packages, side by side at the root:

- `gym/` → the `daggorath-gym` distribution, imported as `daggorath_gym`
- `agent/` → the `daggorath-agent` distribution, imported as `daggorath_agent`

The environment/trainer split survives as an *import* boundary — `daggorath_gym`
imports only gymnasium+numpy — not a folder or repo boundary. The repo root was
hoisted so the whole workspace is the project, and git history was preserved
(the agent was never its own repo, so it entered as new files).

Both packages install editable from the root: `pip install -e gym`, then
`pip install -e agent`.

## Audiences / front doors

One core, several audiences. The root `README.md` gives each a labeled door
rather than picking a winner:

1. **Learn RL** — the trainer as a worked example.
2. **Play Daggorath** — the emulated game world.
3. **Build on the library** — `daggorath-gym` as an installable environment.

## Portfolio positioning

The project doubles as a portfolio piece for AI/systems engineering. The
reviewer reads for *judgment calls*, not wiring. Candidate "spine" decisions
that demonstrate strategic thinking:

1. Fact vs. valuation (env reports facts; reward is a swappable opinion)
2. Mask, never shrink (curriculum uses masking so `--resume` chains)
3. Reward the margin, not heart rate (exertion rewards combat, not a penalty)
4. Fidelity over convenience (real MAME/6809 world, not a toy grid)

Open: which one (or cluster) leads the narrative.

## Next

Settle the portfolio-spine pick.
