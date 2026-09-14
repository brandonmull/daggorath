# Causal Attribution

_What the agent is ultimately trying to learn — telling what it caused apart from what the world does on its own — and why that one need shapes the environment's reporting and the knowledge the agent keeps. Open discussion; it names the motivation the other threads hang from, and keeps the exchanges that named it._

The agent's deepest task is causal attribution: telling "I caused this" from "the world does this on its own." The three moments, the no-action control, and the frame reporting are not separate concerns — they are the two halves of that one need. This discussion names the need and argues why it matters. The shape of the knowledge it forces is in [`knowledge-representation.md`](knowledge-representation.md); the reporting it demands is in [`frame-reporting.md`](../../../gym/docs/3_decisions/frame-reporting.md).

## What is the agent trying to tell apart?

The motivation did not arrive all at once; it was first given the wrong name, and the correction is where the need appeared.

> **the first answer** — "The environment was making a temporal valuation it had no business making. It is the fact-versus-valuation line, extended from reward to time."
>
> **the objection** — "But what about the need to learn via inaction?"
>
> **the distillation** — "Causal attribution is the need, and the fact-versus-valuation line is only the rule that serves it. The agent has to be able to tell 'I caused this' from 'this happens on its own.'"
>
> **the confirmation** — "Exactly — causal attribution."

A principle is not a motivation. The fact-versus-valuation line names how the environment should behave; it does not name what the agent is trying to learn. The objection exposed the difference, and the need — causal attribution — is the deeper thing. The name also matters because it joins two threads that had been argued separately: once the goal is stated as attribution, the three moments and the no-action control stop reading as distinct open questions and read as two faces of one task.

## What are the two halves of causal attribution?

The inaction half almost looked like a second motivation, and the distinction had to be drawn.

> **the answer** — "Causal attribution has two halves. Action effects — what changed after the command, and when. Inaction dynamics — what moves while you do nothing, the baseline. They aren't two motivations; they're the same need from both sides. You can't attribute an effect to your action unless you know both what happened after you acted and what would have happened anyway."

Attribution is subtraction, and subtraction needs a baseline. "The torch moved because I pulled it" is a claim that only holds against the counterfactual — "the torch moved and I happened to be standing there." That counterfactual is the inaction half. In the knowledge the agent keeps, the two halves have two names: command edges — what an action caused — and world edges — what happens with no action at all.

## What makes the no-action half worth watching?

The baseline is not a bookkeeping detail; it is a whole face of the world the action-centric view hides.

> **the observation** — "A normal player can observe changes while being inactive. Understanding how things other than the player's character move and change in the game is just as important to learning."
>
> **the agreement** — "The action-centric model treats the world as static until you act. But the world isn't static — creatures pursue you, the torch burns down, the heart races, none of it waiting for your input. Watching all of it happen is how you learn the world's own rules, not just what your commands do."

What the agent does is only half of what there is to learn. The world has its own motion, and a learner that never watches while idle learns an environment that does not exist. This is the no-action control the knowledge docs had already flagged as an open question; naming it causal attribution's second half is what closes the loop. And the world never goes fully quiet — the baseline is the world's own motion, not a clean subtraction.

## What does causal attribution require of the environment?

If the two halves are to be observed, the environment has to report the record they depend on.

> **the requirement** — "Attribution needs time and stillness, and a change-gated channel gives neither. You see the creature move, but not that it held still for twelve frames first, and not how far apart its steps are. 'The world does this on its own' is precisely the knowledge change-gating throws away."

The environment's part is the complete temporal record — every frame, numbered, with what changed on it — and that part is argued on the environment side in [`frame-reporting.md`](../../../gym/docs/3_decisions/frame-reporting.md). The consumer's part is what to do with that record: how to group frames into a step, and whether "no action" is a command or just the absence of one — observe-only in the knowledge base, an action in the Gym step. Both are the consumer's choices, not the producer's. The two halves also leave two open questions behind: the settle signal — how to know a command finished — and false causation — how to catch a link labeled causal that later turns out wrong. And the command edges and world edges must be explicit — readable and chainable — so they cannot live in the weights: SB3 is model-free and holds no explicit model, so the edges live in the knowledge base, and SB3 learns only the value that ranks them.

## Reference

| Document | What It Contains |
|----------|-----------------|
| `knowledge-representation.md` | The shape of the knowledge this motivation forces — the three moments, the no-action control, false causation |
| `knowledge-and-reasoning.md` | Why that knowledge must live outside the weights |
| `sb3-capabilities.md` | Why the edges cannot live in the weights — SB3 is model-free and holds no explicit model |
| `../../../gym/docs/3_decisions/frame-reporting.md` | The environment-side reporting the temporal record demands |
| `../../../gym/docs/1_discussions/extensibility.md` | The two consumers the environment must serve |
| `../../sandbox/causal-timing/README.md` | The experiment measuring the three moments |
