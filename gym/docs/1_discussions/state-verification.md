# State Verification — Discussion

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Status

**Not yet discussed.** This is a placeholder — it records the premise and the open questions; the discussion itself is still to be had.

## Premise

Poking a known value into RAM and asserting the sampler round-trips it — the `state-field-verification` approach — proves the sampler reads the right address, not that the address means what the RAM map claims. A stronger proof reproduces a gameplay situation that must cause a specific state change, and watches the field change accordingly: PULL LEFT TORCH must move the torch from the pack to a hand, so the hand pointer must become the torch's slot — if it does not, the understanding is wrong, not the test.

Three levels of evidence, in increasing strength:

- **Poke** (`state-field-verification`) — an address round-trips a value we wrote. Proves the sampler reads it; says nothing about what the game uses it for.
- **Observe** (`command-detection`) — an address changes in real play. Proves it is live; the change is whatever happened to happen.
- **Reproduce** — a forced situation must change an address to a predicted value. Proves the address means what we claim.

## Open questions

- **Which situations, for which fields.** A catalog of "situation → must-change field" pairs, starting with the deterministic ones (torch PULL/USE, EXAMINE, ATTACK) before the nondeterministic (combat, creatures).
- **The control.** The state just before the command versus just after — the same post-to-changed window the command-latency sandbox already measures.
- **Reproduce versus poke.** Whether reproduction replaces the poke sandbox or sits beside it — wiring is the poke's job, meaning is the reproduction's.
- **Transients.** Whether every-frame reporting is required to catch a one-frame change, or the change persists long enough to observe change-gated.

## Reference

- `../findings/ram-signals.md` — the addresses and their claimed meanings
- `../../sandbox/state-field-verification/README.md` — the poke-and-assert approach this contrasts with
- `../../sandbox/command-detection/README.md` — the observe-natural-transitions approach
- `../3_decisions/state.md` — the schema the new fields file into
