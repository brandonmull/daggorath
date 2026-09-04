# Knowledge and Reasoning

_How the agent's mind should be organized — what knowledge is, where it lives, and how it produces action. This doc records the argument, not just its conclusions: the questions asked, the answers rejected and why, and the tensions that forced each move. Open discussion; nothing is decided, and several threads are left deliberately hanging._

## From a task to a question

This discussion did not start as philosophy. It began as a concrete task: implement the first curriculum course, a reward machine for lighting a torch — track the four-command recipe EXAMINE → PULL → LOOK → USE across five states (start / examined / held / looked / lit) detected from the true state, grading each transition +1.0 to light the torch, +0.1 per step, −0.1 for no advance, and compose it into the reward's existing layers.

The first crack appeared while discussing it. The EXAMINE step was never there because the game requires it — it does not; a torch can be pulled and lit without examining. It was there to build the *habit* of examining before acting. That turned the task inside out: the torch recipe was not the first lesson, the habit was. And the torch machine, it turns out, teaches the *form* of that habit — examine, then pull — but not its *substance* — act on what was learned — because the boot pack is fixed, so examining it reveals nothing new.

Then a question asked about equipping — *how does the desire to have something of use become part of an acting agent* — opened the floor, and the concrete task was left behind. Everything from there is the descent: desire is the value function; a toddler cannot reason without experience; experience must be captured as knowledge; knowledge cannot live in the weights; on down to a symbol being a discretized vector and learning being the act of drawing walls.

This doc records that descent. The course ordering that triggered it lives in `curriculum.md`; what follows is what the descent produced.

## What makes the agent want?

Equipping an object is driven by wanting it, and that wanting had never been explained. The curriculum had planned to reward equipping — a holdings potential over what the agent carries — but the question of what makes the agent want came first, and the exchange went like this:

> **the question** — "The act of equipping is driven by the desire to have something of use, in the first place. How does such a desire become encoded in an acting agent?"
>
> **the answer** — "In RL, desire isn't a primitive — it's the value function. V(s) is the expected discounted future reward from a state. The agent wants to hold a sword exactly when V(sword in hand) is greater than V(empty hand), and V is learned: the reward flows backward through the Bellman update — holding the sword is good because it precedes kills, which precede survival, which precede the win. So desire is derivative, the shadow of the item's downstream payoff cast backward. A holdings potential that rewards possession doesn't let that shadow form; it implants it — 'having is good,' not 'using is good.' If the agent holds a sword and stands still, the possession potential keeps paying with no kill ever occurring."
>
> **the agreement** — "That's exactly it. So, what options do we have for modifying the agent's reasoning?"

What "desire is the value function" means, mechanically: the agent has no separate wanting drive. It has V(s), a learned estimate of the expected future reward from each state, and wanting something is nothing other than V being higher in the states that have it than in the states that lack it. V is not programmed — it is built up one Bellman step at a time as actual rewards (a kill, a new cell, survival) propagate backward to the states that preceded them. So desire is a *prediction* the agent has learned — "holding this predicts reward" — never a value the designer injected. To reward possession would be to fake that prediction, and the agent would learn to hold things rather than use them.

## Reasoning comes from experience

The question of modifying reasoning was answered first with a list of levers, then overturned:

> **the levers** — "Reasoning is two learned functions — the policy and the value — and it can be touched through a few levers: constrain with the mask, inform with the observation, incentivize with the reward, lengthen the horizon, and stage them with the curriculum."
>
> **the observation** — "The problem with a toddler trying to reason is that, without experience, they haven't learned to predict outcomes."
>
> **the answer** — "Prediction is the *output* of experience, not the input to it. We can't modify reasoning that doesn't exist yet — we can only cause the experiences from which reasoning will grow. We arrange the experiences, and the reasoning is what those experiences grow into."

That overturning reframed the curriculum as an **experience schedule** — it stages which things the agent is *made to live through*, in order. The levers become tools for causing experience: the mask forces the procedure, novelty pays for the experience itself, the outcome reward labels it after the fact, and a precondition potential makes it reachable. The desire we want is the last thing to appear — after the agent has been made to examine, paid to look, and shown that use pays.

## Where does the experience go?

Experience must be captured as knowledge before it can be used for prediction, and that raises the question of where the knowledge lives. The answer was a redirection — knowledge does not live in the weights — and it is best kept in the exchange that produced it:

> **the purpose** — "My purpose for asking whether or not we could modify the agent's reasoning is that in order for experience to matter, it has to be captured as knowledge that can be utilized for predictions, which is basically what reasoning is."
>
> **the standard answer** — "That relocates the question to *where knowledge lives*. In this stack, knowledge lives in the weights — the policy and value functions are a compressed record of experience, and the forward pass is the prediction. Experience becomes knowledge through gradient descent, so modifying reasoning means modifying what the weights can represent, what experience gets captured, or how the weights are queried. But there is a hard constraint: the agent is Markov, and the pack is EXAMINE-gated. Its observation is the current frame only, so knowledge can only be keyed on facts present right now. During EXAMINE the pack is in the frame, so the agent can learn 'see sword, pull' — the immediate reflex works. But the moment the display flips back to LOOK, the pack vanishes, and with no memory there is nowhere for 'I have a sword in my pack' to live. The architecture can build a *reflex*, not a *belief*. That points at the real fork: recurrence, persistent observation, or accept the reflex. Which is the agent we're trying to build?"
>
> **the objection** — "I think the modern idea that knowledge lives in weights is a mistake. I think knowledge lives in a preliminary form that produces weights."

The last line is the turn this doc follows. The premise — not a conclusion — was overturned. A weight is a static, compiled number, a mapping from observation to prediction, and it cannot hold the specific, episodic knowledge that must survive a display change. So knowledge lives in a **preliminary, reusable form** — a durable structure that the weights are *produced from* and *operate on*, and that, combined with per-task or per-episode data, produces the actionable weights for that task.

Later, near the discussion of symbols, the reason the weights fail as a store was sharpened: knowledge captured in weights is **distributed** — "PULL moves pack→hand" is not stored anywhere you can point to; it is smeared across the whole network. So when the task changes, the gradient disturbs the facts entangled with the ones being changed, and the knowledge is overwritten rather than reused. The contrast the composability argument later runs on is local versus distributed: a symbol is discrete, has crisp identity, and composes by rules, while a weight is a coordinate in a continuous space with no meaning except through the other weights around it.

## What is knowledge, and what isn't it?

Knowledge does not live in the weights; it lives in a preliminary, reusable form — a durable structure the weights are produced from and operate on. Locating knowledge there still does not say what knowledge *is*, because knowledge sits among neighboring terms that are easily confused with it. Three observations forced those terms apart:

> **on memory** — "The term 'memory' is ambiguous with 'knowledge'. We have to be careful to explicitly categorize the things we're trying to remember that are somehow distinct from the more active concept of knowledge."
>
> **on causal structure** — "Causal structure is primary knowledge worth creating a foundation on. It should be orthogonal but related to all other knowledge, I believe. I don't think that causal structure makes up all there is to a world model, however."
>
> **on skill** — "A skill is something you can do well, which may or may not depend heavily on knowledge. … I could consider a skill to be something that is executed post-reasoning — what skill to employ is exactly the thing that is selected by reasoning."

They had to be told apart, and the line that separates most of them is generality:

- **Knowledge** — what is true *across* situations, durable and task-invariant. The reusable form.
- **Memory** — what is true *in this episode*, situated and transient. Memory is the data; knowledge is the structure that interprets it.
- **Causal structure** — the primary knowledge: what causes what (PULL moves pack to hand; USE lights a torch; light enables sight). It is orthogonal (decomposable into independent primitives) and related (the primitives compose into chains), and that composability is why it is the thing worth founding on.
- **World model** — broader than causal structure: dynamics plus state, beliefs, and utility. Causal structure is the spine; the rest is flesh.
- **Reasoning** — knowledge applied to memory, producing predictions and decisions.
- **Skill** — a procedural capability, executed after and selected by reasoning. Its weights are its implementation, not knowledge.

Read against the list, the line shows itself. Knowledge is what is true *across* situations, and memory is what is true *in this episode* — the general and the specific, which is exactly the generality the claim names. Causal structure sits on the general side, since it is the primary knowledge; the world model is broader only because it admits the specific — the state, the beliefs, the utility of one situation. Reasoning is the bridge that applies the general to the specific, and skill is not knowledge at all, executed only after reasoning has chosen it.

## How knowledge produces action

Knowledge lives in a preliminary, reusable form — not in the weights. That answered *where* knowledge lives, but not *how* that form produces behavior. The how was the next question, and it led to a refinement that gave the conversation its shorthand:

> **the refinement** — "I really think of knowledge as some preliminary, reusable form that can be combined with some other set of learned data to produce actionable weights, per task."

That shorthand — knowledge plus data produces actionable weights — was then doing three jobs at once — "actionable weights" quietly meant a **plan**, a **policy**, or literally **weights** — and the three candidate mechanisms each produced a different one.

The torch chain was the shared ground — EXAMINE reveals the pack, PULL moves the torch to hand, USE lights it, light reveals the dungeon. The three candidate models each held that chain in a different place:

**Rules-as-knowledge.** The chain is a set of explicit rules (a transition relation) held outside any network. Reasoning composes them: from the goal *light*, chain backward — light needs USE on a held torch, which needs PULL, which needs the torch in pack. The plan EXAMINE → PULL → LOOK → USE falls out, inspectable. The catch: the rules must be written or learned.

**World-model-as-knowledge.** The chain is a learned transition model — a network separate from the policy, trained to predict PULL → torch in hand, USE → light, light → sight. Reasoning is rollout: from *dark, torch in pack*, the agent imagines PULL then USE and sees light → sight → new cells. The policy is produced by training inside those imagined rollouts, so the same model, given a different reward, trains *equip* without re-learning the dynamics.

**A goal-conditioned value.** The chain is compressed into one value/policy V(s, g). For g = light, V rises as the torch moves pack → hand → lit; conditioning on the goal produces the behavior. Cheap and reusable, but the causal structure lives inside the policy's weights.

Then the collapse happened through a series of objections:

> **the objection** — "I don't think these are mutually exclusive options. Some hybrid combination of them might produce the best model. As far as your premise that learning symbolic rules from raw experience is hard, or more generally that rule-learning is expensive, I don't implicitly agree with you."
>
> **the second objection** — "I don't see the big contention between model a and model b except for when and how the knowledge is encoded."
>
> **the question** — "Why do those two models have to be encoded differently (symbolic vs weights)?"
>
> **the answer** — "They don't have to be. What I had treated as one axis was two welded together — source (who encodes, human or agent) and form (how it is represented, rules or weights)."

The result: rules-as-knowledge and world-model-as-knowledge are the *same architecture* — a world model plus a reasoning step over it — differing only in *when and how* the knowledge is encoded. That is a spectrum, not a fork. The real fork is **explicit world model plus reasoning vs. implicit policy** — model-based vs. model-free. And "symbolic vs. weights" split into two independent axes, source and form, whose four cells are all viable — the bottom-left (the agent learns rules) included.

## What makes the causal chain compose?

Causal structure is composable — its links chain into sequences. What actually makes two links compose was tested against the torch-lighting chain:

> **the request** — "Let's consider our notion of 'composable' here by inspecting our concrete example of the causal chain for torch lighting, and seeing if we can discover the hidden attributes behind each link that actually make them 'composable' with one another."

Each link was recorded by what it reads and what it writes:

```
EXAMINE        writes  state:     display_function ← EXAMINE
               writes  knowledge: known_pack ← {torch, sword}
PULL(torch)    reads   state:     torch.location == pack
               writes  state:     torch.location ← hand
USE(torch)     reads   state:     torch.location == hand
               writes  state:     effective_light_physical ← 7
sight          reads   state:     effective_light_physical > 0
               writes  knowledge: known_cells ← corridor(light, position)
```

> **the finding** — "PULL → USE composes because PULL writes torch.location ← hand and USE reads torch.location == hand — the same named variable, written then read. USE → sight composes the same way, on effective light. But EXAMINE → PULL does not: EXAMINE writes display_function and known_pack, while PULL reads torch.location. There is no shared variable. EXAMINE's write is to what the agent knows; PULL's read is from what the game is."

> **the distinction** — "So the chain is really two kinds of link on two substrates. Action links — PULL, USE — write state fluents, facts about the game, and compose mechanically: a write of X satisfies a later read of X. Perception links — EXAMINE, sight — write knowledge fluents, facts about what the agent has seen, and compose only through reasoning: the agent selects the next action because of what it now knows. The hidden attribute behind any composable link is that it is a relation over named variables — which it reads, which it writes — and the kind of variable decides how the composition happens."

Then, when the distinction felt too compressed, it was restated plainly:

> **the plain version** — "A fluent is just a named fact about the situation, like 'where the torch is' or 'how much light.' A link reads some facts and writes others. Most links connect because they touch the same fact — PULL changes 'torch location,' and USE cares about 'torch location,' so they snap together. But EXAMINE doesn't touch 'torch location' at all; it changes what the agent can see. So EXAMINE connects through the agent's knowing, not through the game's state."

That is why EXAMINE leads the recipe: it is the perception link — the one that writes the knowledge fluent, the known pack, that the first action link needs.

## Does composability demand symbols?

Unstructured weights do not compose — they entangle and forget. Symbols compose by construction. But the property that makes symbols compose is *locality* (each fact is a unit nothing else touches), and weights can have that too if factorized into modules. So the real axis is **monolithic vs. modular**, not symbolic vs. weights.

But there is a catch: composition is *matching interfaces*, and weights have no type — so composable weights must be wrapped in discrete interfaces, and those interfaces are symbols. That conclusion was challenged twice:

> **the challenge** — "What's stopping us from constructing a system that constructs sets of weights that remain separate from one another and are still composable with one another?"
>
> **the answer** — "Nothing fundamental. The precise price is that composition is matching interfaces, and weights have no type — so the interfaces, and the composer that chains the modules, are then symbolic anyway. The symbolic level didn't disappear; it relocated to the scaffolding."

> **the request** — "Let's try to imagine a translation from symbols to weights that would lead them to be composable. And let's aim for a generalized solution that doesn't require hard-coded rules over symbols — I mean brittle, pre-programmed interfaces. Using some generalizable form of weights (number sets) whose fairly uniform attributes don't require constant maintenance of proper interfacing like symbols would."
>
> **the translation** — "A fluent becomes a subspace of one shared latent vector; a value becomes a region inside that subspace; a rule becomes a learned transformation that moves the region and leaves the other subspaces alone; composition becomes plain function composition; interface matching becomes geometry; non-interference becomes disentanglement. And the uniformity is the real advantage: everything is a vector, so everything already has the same type, so composition is always well-typed — the type system is the vector space itself. But the cost: the semantics must now be learned, and learned semantics compose only approximately. 'Leaves the other subspaces alone' is only approximately true; a novel composition can leak or fail. Symbols compose exactly, always; vectors compose usually, approximately. So the brittleness doesn't vanish — it relocates, from interfaces maintained by hand to geometry maintained by gradient."

The symbolic level is unavoidable for the *scaffolding* (interfaces and composition), even when the *content* is weights.

## What is a symbol, really?

The symbol was defined in two moves — first the human advantage of naming, then the abstraction of a cell wall:

> **the synthesis** — "The advantage humans have is that they can turn their vague, vector-like knowledge into symbols that then become easy to hang specialized knowledge on (interfaces that constrict proper use). It's called naming things."

From that: **naming is the bridge.** A symbol is not knowledge; it is an *address* into knowledge — lossy compression of a region of the vector space, and the loss is what makes it crisp enough to compose. The two levels form a cycle: learn in vectors, name, hang specialized knowledge on the names, re-name when they go stale.

> **the abstraction** — "Let's drop the notion that words and names actually matter for a second and consider the concept of a symbol more abstractly. It's really just some highly localized representation of something, discrete from everything else. It's kind of like a cell wall or something."
>
> **the answer** — "A symbol, reduced all the way down, is a bounded unit of representation — a region with a boundary separating it from everything else. The word was never the point; the boundary was. The boundary does three jobs: localize, isolate, mediate. And the cell metaphor changes the question, because cell membranes aren't declared — they self-assemble; a lipid bilayer forms on its own, nobody draws it. So the crux stops being 'symbols vs. weights' and becomes: can a representation grow its own boundaries, or must they be imposed from outside? Weights are a continuous medium with no inherent boundaries; symbols are boundaries imposed by declaration. The open question is a third thing — boundaries that emerge from the representation itself."

## A symbol's boundaries: drawn or grown?

A symbol is a bounded unit; its boundary is a wall. The question became which walls are drawn and which grow:

> **the objection** — "It doesn't make sense to draw 'all' the walls ourselves. That would leave no room for learning. You might as well just write a program."
>
> **the answer** — "Drawing all the walls is writing a program — no room left for learning. So the division of labor has to be drawn at a different level: we draw the substrate — the lipids, the base representation the walls form on; the wall-forming mechanism — the physics and chemistry that let boundaries self-assemble; and the world's interface — observation, action, reward, dictated by the game. What we don't draw are the membranes — the actual walls, the symbols. Those have to emerge. Learning is the act of drawing walls."

The final move followed from it: drawing all the walls is writing a program — no room left for learning. What we draw is only the **substrate**, the **wall-forming mechanism**, and the **world's interface**; the walls themselves grow. **Learning is the act of drawing walls.**

## A symbol is a grown boundary

**A symbol is a discretized vector — a bounded region of representational space, grown by discretization, composed through its boundary.** The reusable form is the set of walls the agent grows; what we build is the chemistry and the curriculum that make the right walls grow.

## The causal chain

The descent reached "knowledge lives in a preliminary form that produces weights," but not what that form is. The answer began as a concrete proposal and was sharpened through the exchange:

> **the premise** — "The basic premise starts with causal detection. We need a method for computing a cause/effect, which I believe should be done by diffing game state. Consider the difference in game state before and after a torch is lit. Also, consider that the agent needs memory of action to result."

The diff is the raw material, but "action → result" is too thin: a command's effect depends on the state it was issued in, so the record is really precondition, command, effect. The first reduction turned the diff itself into something indexable:

> **the reduction** — "What if this was reduced to a simple vector of zeros and ones, like a mask that indicates the parameters involved in change, and what if you somehow paired that with the indexes representing action? This at least is some kind of representation, right?"

It is — the mask is the **footprint** of an action, the answer to "what does this command touch?" But a mask says *what* changed, never *how*, and the attempt to fold direction into the mask ran into the state's mixed types:

> **the question** — "Would it be noisy to let the mask encode three values {-1, 0, 1}?"

For token fields — the inventory slots that hold a torch or a sword — "direction" is an artifact of the index ordering, not a fact; for the clock fields that move on their own, it is uncorrelated with the command. So the sign belongs in the **value**, not the mask:

> **the synthesis** — "The change representation needs to be able to determine 'how' a parameter changed (direction, magnitude) in addition to 'what' changed. Ditto for precondition. The reason is that a bit mask acts to quiet noise and can be used to index different classes of change/precondition."

That is the mask/value split: a sparse vector whose mask is the index and whose value is the content. And a cause is incomplete without the state it acted on, so the full unit is a triple — precondition, action, effect. The triple is the first thing that composes: PULL writes "torch in hand"; USE reads "torch in hand" and writes "torch lit." The after-value of one effect is the precondition of the next. That stitching is the chain.

## How does the agent detect causation?

The diff answers what changed; it does not answer what *caused* it, when the world moves on its own. The turn to neuroscience was the search for how that attribution is done:

> **the turn** — "I think we need to inspect neuroscience to inspire a model that more closely mimics human ability to detect causation."

The answer, across the literature, is one statistic: humans do not learn "B followed A"; they learn whether B happens more when they do A than when they do not — the contingency ΔP = P(effect | cause) − P(effect | ¬cause), framed as an **intervention**: the cause is something you *do*, not something you watch. That turned exploration into a loop:

> **the loop** — "What we need to do is let the agent randomly choose actions until something significant changes in state, then have the agent experiment with those actions over again to build its sense of causation?"

And the control side of the same statistic fell out of the same idea:

> **the control** — "We can use the same concept to help the agent determine what changes are not caused by their actions by having it experiment with no-action and see what changes. Anything it finds that it has no effect over, we can create some sort of inhibitors in our model."

The no-action experiment is the ¬cause term: doing nothing is not-doing every action at once, so one passive step estimates the base rate for every candidate cause simultaneously. The fields that change under no action are the world's, not the agent's — the **inhibition mask** that keeps them out of the chain. Prediction error is the learning signal; the cognitive map is the storage.

## Knowledge is symbolic; reasoning is learned

The chain is knowledge, but building it and using it are not the same thing, and the exchange that fixed that boundary began as a pushback:

> **the pushback** — "It's just that there should be some part of the model that is 'learning' how to make causal inferences and 'learning' how to reason over them. This indicates a neural network for at least some portion of that work."

The earlier conclusion — knowledge lives outside the weights — had been read too broadly, as "everything must be hand-coded." The correction restores three tiers: **knowledge is symbolic structure; reasoning over it is a learned process; the policy is learned skill.** The mask, the value, the triple stay symbolic, because a symbol's value is that it can be *operated on* — matched, chained, unified, inspected. The chain must be readable — one can look at it and see "USE TORCH lights the torch" — or the exercise collapses back into weights. What is learned is the *reasoning*: judging which candidate edges are real causes and which are confounds, selecting which are relevant now, choosing which to chain toward a goal. The network reads the chain, judges it, and plans with it — it never writes it.

## Learning without ground truth

A learned reasoner needs a training signal, and the search for one ran into a wall:

> **the question** — "What trains the reasoner?"
>
> **the answer** — "Learning to make correct causal inferences needs a signal for 'correct,' and we don't have ground-truth causation — the agent is supposed to discover it. The only workable signal is self-consistency."
>
> **the gloss** — "Reward the reasoner for making the symbolic chain predictive of future observation. A reasoner that trusts real edges and rejects confounds produces a chain that forecasts what happens next; a bad one does not. The network is trained to keep the knowledge honest, not fed external truth."
>
> **the agreement** — "Yep, self-consistency is the only way because there is no ground truth. That's exactly what I was thinking."

Self-consistency, then, is a stability check over the evidence the chain has already gathered, not a forecast. Each edge accumulates many instances — the same precondition and action, observed again and again — and the reductive process asks whether those instances agree:

- a field that changes the same way every time → real effect, keep it
- a field that changes sometimes and not others → noise, prune it
- an edge whose whole effect scatters → no stable cause behind it, drop the edge

The direction is retrospective — pruning the past, never forecasting the future — which is why "predict what the agent observes next" was the wrong description, and why forecasting was already rejected along with the world model.

But stability alone does not tell a real cause from a reliable confound — a field that changes every step regardless of the action is stable but not caused. So the stability must be measured **interventionally**: does the effect hold under the action and not under no-action; the action in the triple is what separates a cause from a coincidence. And stability needs a pressure toward compression, or the chain keeps every field that merely co-occurs; the network's limited capacity is that pressure — its bottleneck is what forces the chain to keep the few stable causes rather than the noise.

## The two networks

The preceding section described the network as a reader that never writes the chain — a framing that was then challenged:

> **the framing** — "The network reads the chain and returns reasoning decisions — it never writes the chain. The symbolic layer stays the ground truth the network reasons about."
>
> **the first try** — "I don't know about 'the' network not being the author of the chain. I believe there should be separate networks for helping to construct the chain vs read the chain."
>
> **the correction** — "My fault. I think that constructing the chain vs read the chain is a misnomer. What's really going on is there needs to be a network for reading the knowledge base to construct a chain, at least. I'm not sure how we handle reasoning over the chain though. That is where I think there should be a separate network if any."

The two networks fall out of two different timescales. **Consolidation** reads the accumulated raw observations and distills the clean chain from them — offline, in the background. **Execution** uses the chain at action time — online.

Execution must stay a **symbolic search with a learned heuristic**, not a network that reasons wholesale. Backward chaining over the chain is exact and inspectable; the network only ranks which edge to try first. If it emits plans directly, the chain was decoration.

This is where the discussion currently stops — the two networks and self-consistency are named but not yet planned.

## Answers rejected

The argument records what was abandoned along the way, because each rejection fixed a boundary:

- **A world model** — "What if we used a temporal series of conditions (with changes maybe) plus an action to train a model that predicts effect?" It dissolves the noise and bootstrapping problems outright, but it is prediction, not knowledge: it cannot be read, chained, or transferred, and it does not compose outside its training distribution. It answered a different question.
- **Knowledge as input to a model** — "What if we augmented the model's input with causal chain knowledge — after selecting a relevant subset from the knowledge base that is." Selecting the relevant edges is the entire hard problem; if the selection is learned attention the reasoning is back in the weights, and if it is symbolic matching a planner already exists and the predictor is redundant. Knowledge-as-input keeps the encoding and throws away the manipulability.
- **A mini-network per mask** — "Crazy, vague idea: what if we created a mini neural network per mask?" A real architecture, but it makes the network the *author* of the knowledge content — the one thing that must stay symbolic — and it overfits the sparse instances a single mask accumulates.
- **A powerset lattice** — "I was thinking of organizing the index in layers, starting with a single parameter." Correct and elegant, but premature: the flat index is the lossless raw record, and all overlap reasoning is a later inference pass over it. Merging early destroys the evidence that would have shown which field was noise.

## Open questions

- **Goal production.** A goal is itself a symbol — a name pointing at the region of the world model to reach. Goal-production is a special case of symbol-production; the open part is *what selects which region to name* — where the wanting comes from, once the possession-potential answer is rejected.
- **Emergent boundaries.** Can a representation reliably grow its own walls, or must discretization be imposed?
- **The curriculum consequence.** If learning is drawing walls, the curriculum stages the experiences that grow the right walls in the right order — what "examine before you act" (`curriculum.md`) becomes.
- **Self-consistency, concretely.** The chain must prune noise and false predictors, but the mechanism — how stability across instances is measured, what separates a stable cause from a reliable confound — is described, not settled.
- **Reasoning over the chain.** Knowledge is symbolic and reasoning is learned, but the consolidation/execution split is named without a plan, and how reasoning learns without ground truth is open.
- **The value layer.** The mask indexes what changed and the value carries how, but the value's form — direction, magnitude, typed token identity — and how an effect's after-value becomes the next precondition, are open.
- **Unifying overlapping masks.** The flat index is lossless by design; the inference that merges near-duplicate masks into one event is deferred.
- **The acting agent's interface to the chain.** The knowledge store is the acting agent's "goto," but how the policy reads precondition-matched action/effect affordances and acts on them is open.
