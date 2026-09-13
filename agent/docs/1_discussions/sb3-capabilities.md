# SB3 Capabilities

_What Stable-Baselines3 can and cannot learn natively, and where that leaves the knowledge the agent must hold outside the weights. Open discussion; it records the constraints rather than re-deriving them._

Stable-Baselines3 is model-free reinforcement learning. That one fact constrains everything the agent can learn from it, and the constraints are worth recording once so they are not reasoned through again. The need SB3 fails to meet is causal attribution: the command edges and world edges the agent must hold, argued in [`causal-attribution.md`](causal-attribution.md), are exactly what a model-free learner cannot hold. What follows is what SB3 learns, how it handles the world's own motion and memory, what it leaves out, and the one correction about the signal that actually drives its policy.

## What does SB3 actually learn?

The first question was whether SB3 can learn about the world independent of the agent's actions.

> **the question** — "Is SB3 capable of learning about things not related to action?"
>
> **the answer** — "Partially. Model-free reinforcement learning learns two things — a policy and a value function. It learns value, not a model of the world. It never learns what happens next, with or without an action."

Model-free means there is no transition model anywhere in the algorithm. The agent learns what to do and how good each state is, but never the world's own rule for what follows what. That absence is the single constraint the rest of this discussion hangs from.

## What does SB3 do with the world's own motion?

If there is no world model, the world's autonomous motion can only reach the learner through the value function.

> **the answer** — "Only as a scalar gut-feeling. The value function learns that a creature near is bad, but it cannot be read — you cannot ask why — and it cannot be separated — 'the torch moved because I pulled it' and 'the torch burned down on its own' collapse into the same value. It is not a fact you can chain."

Memory is the same story. SB3 offers it two ways — an LSTM hidden state through `RecurrentPPO`, or a fixed stack of recent frames through `VecFrameStack` — but both are memory in service of the value and policy, and the LSTM's hidden state is exactly the "knowledge in the weights" the knowledge docs reject. It remembers, but it does not hold a statement.

## What does SB3 leave out?

The gap is the temporally extended action — a command whose effect lands frames later, with the agent still steering in between.

> **the wish** — "There must be support for associating an action with a sequence of state changes after it. Think of a jump, where you keep steering in the air."
>
> **the answer** — "The proper solution is the options framework — an action with a duration and a termination condition. An option of length k collects reward discounted by γ^k, so time is explicit again. SB3 has none of it natively, and its `step()` returns a single fixed-shape observation, never a variable-length series. The fix lives at the environment boundary: the environment runs the option to completion, and SB3 sees a flat policy over options."

And that is the differentiability crux. The knowledge base is a symbolic search, and a policy-gradient algorithm needs a differentiable action — so the search cannot be the policy. SB3 can learn the value the search uses to rank, but the search itself stays outside the network.

## What signal actually drives the policy?

The last correction is about the value itself, because "go toward good, away from bad" sounds like a use of the value and is not.

> **the idea** — "Consider both positive and negative value as strong signals, and respond differently — go toward the positive, away from the negative."
>
> **the correction** — "That is already how SB3 works, through the advantage, not the value. The value says whether a state is good; the advantage says whether an action is better than average — signed, and its magnitude is the strength. The value is the baseline, subtracted out."

So the policy was never reading the value's sign. It reads the advantage — signed, with magnitude as the step size. Any desire to make the absolute value a separate strong signal is a new intrinsic reward, a choice about the objective rather than an improvement to it.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `knowledge-and-reasoning.md` | Why knowledge must live outside the weights — the line these limits press against |
| `knowledge-representation.md` | The shape of that outside knowledge — experience and causal edges |
| `causal-attribution.md` | The motivation that exposes SB3's limits |
| `../3_decisions/feature-extractor.md` | The one extension already made — a custom feature extractor |
| `../3_decisions/observation-wrapper.md` | The uint16 → int32 adaptation SB3's torch conversion forces |
