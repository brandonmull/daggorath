# Daggorath — Working Notes

Scratchpad for big-picture decisions, continued across sessions. Not a spec.

## Monorepo direction

Replace the two-repo structure (`daggorath-gym` + `daggorath-agent`) with one
`daggorath` repo holding both packages — no sync burden. The environment/
trainer split survives because it is an *import* boundary (`daggorath_gym`
imports only gymnasium+numpy), not a folder boundary.

Open:
- repo name and package naming
- distribution: is `daggorath_gym` still a standalone installable library?
- git history: fresh vs. graft one repo onto the other (user handles git)

## Audiences / front doors

One core, several audiences, each wants a different first impression:
RL novices (learn), Daggorath fans (the game), library consumers (pip install).

Open: which gets the top of the README?

## Portfolio positioning

The project doubles as a portfolio piece for AI/systems engineering. The
reviewer reads for *judgment calls*, not wiring. Candidate "spine" decisions
that demonstrate strategic thinking:

1. Fact vs. valuation (env reports facts; reward is a swappable opinion)
2. Mask, never shrink (curriculum uses masking so `--resume` chains)
3. Reward the margin, not heart rate (exertion rewards combat, not a penalty)
4. Fidelity over convenience (real MAME/6809 world, not a toy grid)

Open: which one (or cluster) opens the README?

## Next

Settle the front-door decision, then the monorepo layout and distribution.