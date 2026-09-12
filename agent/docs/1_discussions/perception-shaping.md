# Perception Shaping

_How the agent turns the environment's full perception into the view a lesson needs. This is open discussion, not a plan — it keeps the exchanges that produced it, and the parts still undecided._

The environment reports the player's perception as a six-channel Dict — scalars, hands, pack, creatures, objects, map. What the agent does with that, before the feature extractor, is the question this records.

## Does the environment reduce the perceived state, or report it whole?

The first instinct was a reduction interface on the environment itself — a keep-list the environment would apply as it built the observation.

> **the objection** — "I don't like the way we've implemented keep_fields. The environment should always output the full list of perceived fields, and the agent should use a wrapper preconfigured with a keep-list to do the filtering."
>
> **the constraint** — "The keep-list should be uniform with the full perceived state. It should not depend on how the full perceived state is extracted from the true state."

The environment reports the player's perception whole. Whatever the agent narrows it to is the agent's business, and it must be expressed in the perceived state's own terms, not the extraction's.

## Is the perceived state a flat list of facts?

Uniformity suggested a flat structure, and the doubt surfaced it.

> **the doubt** — "Isn't the perceived state a flat structure? I guess maybe it's not."

It isn't. Six heterogeneous channels — a nineteen-value scalar vector, two small specifier vectors, a 32×4 creature table, an 8×3 object table, and a 2×32×32 map. Only the scalars are a flat list of facts; the map alone is a hundred times their size. So there is no single flat shape to filter over.

## Can a declarative interface express the shaping?

The heterogeneity made a declarative interface look hard, and then the harder question: even if it could be built, could it say what the agent wants?

> **the realization** — "Since the perceived state is a bit more complex than I expected, perhaps it's not so easy to create a declarative interface for reducing it."
>
> **the proposal** — "An imperative interface provides greater control: a developer could dictate that they want monsters perceived but only the most dangerous monster directly in front of them, or the map but only the doors."
>
> **the decision** — "We need an imperative interface. Declarative would get too complex; a developer selects whole channels via imperative code."

A declarative partial schema can only subset — it keeps some fields and child properties of what is already there. The agent's real need is derivation — a transformed view like "only the doors" or "the nearest monster" — and derivation is code. So there is no reduction interface; shaping is the agent's imperative concern.

## Open questions

- Where does shaping live — a wrapper, the feature extractor, or a per-lesson component?
- Is a lesson's shaped view shared or one-off?
- Does the declarative "partial schema" idea return once the perceived state's schema is made explicit?
- How does shaping compose with the curriculum's staged lessons?

## Reference

- `../3_decisions/feature-extractor.md`, `../3_decisions/observation-wrapper.md` — the existing imperative pieces
- `../concepts.md` — Dict observations and feature extractors
- `../../../gym/docs/3_decisions/perception.md` — the environment's perception, the objective whole
- `../../../gym/docs/2_plans/extensibility.md` — the "perceived state stays whole" plan note
