# Knowledge Representation

_How the agent holds knowledge: experiences, beliefs, questions, and plans, and how it reasons over them to act. This is an open discussion, not a plan. It follows [`knowledge-and-reasoning.md`](knowledge-and-reasoning.md), which argues why knowledge should live outside the weights; this doc describes the shape that knowledge takes, and the parts still undecided. It keeps the exchanges that produced it, not just the conclusions._

It needs to be asked how knowledge would be utilized by a running agent to reason about its course of action. A running agent is always answering one question: what do I do next? The torch chain shows how it answers. The agent wants light, which is a fact, `effective_light > 0`. It asks what action makes that fact true. Answer: USE on a held torch. Then it checks the precondition of that action: do I hold a torch? That is another fact, and it's false. So it asks the same question about that fact: what makes "torch in hand" true? Answer: PULL on a torch in the pack, and that one is already true. The search stops, and the plan is PULL then USE.

That is the entire move, repeated: name a fact you want, find the action that writes it, check that action's preconditions, recurse on any precondition that's missing. It's the backward chaining the docs already name. If that's how the agent uses its knowledge, the knowledge has to be shaped for exactly that move.

## Vocabulary

- **Fact** — a name bound to a value, like torch location being hand. Facts are the shared vocabulary: beliefs read and write them, and two beliefs join on the same fact.
- **Mask** — the selection over the full fact list, which facts a belief reads and which it writes. It is what the belief is indexed by, not the facts themselves.
- **Experience** — the raw record of one step: what the situation was, what the agent did, and the changes that followed, in order.
- **Question** — an investigation still in progress: the anomaly that sparked it, the hypotheses being tested, and the evidence gathered so far. It persists, going dormant once it settles into beliefs.
- **Belief** — a settled causal claim: in this situation, this action produces this effect. Each effect carries a value written and a confidence.
- **Plan** — a path of beliefs from a situation to a goal: a precondition, a series of actions, and an expected outcome, each step with its own expected outcome.
- **Judgment** — the learned matching that decides whether a situation satisfies a belief's precondition, and whether an expected outcome materialized.
- **Value** — the content a fact carries: what an effect writes, and what a precondition matches.
- **Confidence** — how reliable a belief is, derived from the evidence its question holds.

## Experiences

**An experience is the lossless record of one step: the situation, the action, and the changes that followed.**

Learning requires a faithful record of each step, and any filtering at record time risks losing the fact that later turns out to matter. So an experience should be lossless: the situation, the action, and the changes that followed, kept as an ordered sequence of frames. The world's own motion belongs in the record, since telling it from the agent's effects is the learner's job, not the recorder's. Experiences accumulate append-only; archiving old ones is a later concern.

An early figure tried to draw how experiential knowledge is represented, and it packed three layers, the data, the process, and the judgment, into one picture.

![Experiential knowledge representation](knowledge-representation-experiential.jpg)

Pulled apart, the three layers are:

| Layer | What it is | In the figure |
|---|---|---|
| Representation | the data: situations, actions, effects | the boxes and arrows |
| Capture | how the data gets made: runs, lessons, waiting for the game to settle | the ellipses and the divide-the-lesson rule |
| Valuation | the agent's judgment: causal or not, progress or setback | the pills |

The first layer is the data itself, and it is what an experience is. A run of play is a graph: each node is a situation the agent saw, each arrow an action and what changed. The basic unit has three parts: the situation, what the agent sees before acting; the action, one command; the effect, what changed, which facts differ afterward and how.

An action leaves a fact behind, and there are two kinds. A world fact is something that changed in the game, pulling the torch moves it to the hand, written by actions like PULL and USE. A knowledge fact is something the agent now knows, that the pack holds a torch, written by actions that reveal, like EXAMINE, or by sight. World facts connect directly, one action writes and the next reads; knowledge facts connect through reasoning, because the agent acts on what it has learned.

```
When it comes to experiential knowledge, the structure of the effect data should obviously be a mere sequence of frames. However, causal knowledge is supposed to be more structured than that, encapsulating the belief about the nature of the relationship between a cause and its effects.
```

```
Experiences would definitely grow unbounded without cleanup of some kind. Archiving seems like the right answer. I wouldn't worry about compression for now though. In fact, maybe archiving can be held off while we're developing our POC.
```

```
Good call. The POC model is: experiences accumulate append-only, no archiving, no compression. Archiving is a known future task, not a POC concern.
```

```
Experience records what happened. Its effect is a sequence of frames, because that's all the environment reports and all the agent should trust before it has drawn any conclusions. Order and timing, no belief.
```

```
Experiences are the evidence, flat ordered append-only sequences.
```

```
Experience stays in SQLite: it's flat, append-only rows.
```

<p align="center">· · ·</p>

The full state is noisy, the heart beats and the torch burns down, and most of it has nothing to do with the lesson at hand. So a lesson should name a scope, the facts it cares about, and drop everything else before comparing situations. The reduction acts like attention, focusing the learner on the facts that matter.

```
I think the perceived state needs to be reduced, per lesson, to avoid noise and allow quicker development of causal knowledge. Constraining perception this way is effectively the same as giving the model attention. For my immediate purposes I will hand-pick the parameters, but I believe the technique can be automated.
```

```
One consequence of doing things this way is that we will have to conceive a solution for combining knowledge from lessons, such that the resulting knowledge is in terms of the full field set.
```

The combination is not simple, because a lesson ignores some facts on purpose, and an ignored fact may have been hiding a real influence. Two scopes overlap when they share a fact:

```
torch lesson scope   [1, 1, 1, 0, 0]   facts {0,1,2}
sight lesson scope   [0, 0, 1, 1, 1]   facts {2,3,4}
overlap              [0, 0, 1, 0, 0]   fact {2}: effective light
```

Both lessons learned beliefs keyed to fact 2, so merging them must reconcile what each claims about effective light.

## Beliefs

**A belief is the claim that a situation and an action produce an effect.**

To choose its next action, the agent must know what each action does, and a fact or an action alone cannot say. The claim that binds them, in this situation this action produces this effect, is the belief. The situation is part of the belief's identity, since USE with a torch is not USE with a flask. The effect is a series of changes, not one, and each change carries a value and a confidence. The facts the belief reads and writes are the shared vocabulary that joins it to other beliefs.

```
I'm glad you recognize this like I do. When you say situation + action are the key, it makes me wonder how well SQL would support a compound key partially based on vectors. This is one more reason I am drawn to using a vector database.
```

```
I think the awkwardness dissolves once we split what I lumped together, because the reasoning move actually makes two different queries, not one.
```

```
The first is exact: which edges write fact F? That's an inverted index from fact to edges, and it's the backbone of backward chaining. It's set membership, not vectors. Any store handles it.

The second is: which edges' preconditions does my current situation satisfy? That one is why the situation looked like it belonged in the key. But satisfying a precondition is not equality, and that's the real point. A precondition holds when each fact it names has a value in the current state and that value passes the condition. That's a containment test, not a key lookup. You can't serve it with a compound key at all, vector or not. You index edges by the facts they read, then test the candidates' values.

So "situation + action is the key" was the wrong word. What gets keyed, for telling one edge from another, is the action plus the structure of the precondition, meaning which facts it reads. That structure has a canonical form, a sorted list of fact ids, and it's discrete. It keys fine in SQL. The values aren't part of the key; they're what gets tested at matchtime.

That leaves the vector instinct pointed at the wrong operation. Vector databases do similarity: which of these is closest to this one. The agent's runtime question is satisfaction: does this condition hold. Those are different, and conflating them costs something real. If the situation becomes an embedding, matching goes approximate and the chain stops being readable. The docs are emphatic that the chain must stay readable, that you can look at an edge and see "USE lights the torch." That one property is what the whole approach exists for.

Where vectors genuinely fit is consolidation, the other timescale. Grouping many experiences into "situations like this" is a similarity problem, and an embedding may be exactly how near-duplicate situations become one edge. That's where sqlite-vec belongs, the hybrid the store plan already anticipated. So the leaning is right, but pointed at the wrong end: the key stays symbolic, and the similarity lives in the offline pass that generalizes experience into edges.
```


```
When I visualize drawing the relationship from an action to its effects, given a precondition, I see various potential structures (ask me about them). As such, we could think of the unit more like a molecule than an atom.
```

```
The correction is apt, and it captures something my word missed. An atom has no internal structure, but the edge does. It has parts: the precondition facts, the action, the ordered effect steps, and bonds between them, the order of the series. It also bonds with other edges by a shared fact. "Molecule" says both things at once: the unit is the smallest thing that composes, and it's already a composite inside. I'll adopt it.
```

```
You said you see various structures when you draw the relationship from an action to its effects. I want to see them. What shapes do you see?
```

```
Legend: --> means causes; ~> marks the alternative branch of a choice; a lower or rightward arm means later in time.

1. Both, unordered — A causes B and A causes C; both fire, order carries no information.
          B
        /
    A <
        \
          C

2. Either — A causes B or A causes C; one fires, and the decider sits outside the edge.
    A --> B
      ~~> C

3. Both, ordered — A causes B and A causes C; both fire, and B is always first.
    A --> B
      \
       --> C    (B then C)

4. Chain — A causes B, and B causes C; two edges, not one.
    A --> B --> C
```

```
The cases are about the effect, and they do ask a shape question: what one shape holds all four ways an action's effects can relate. Here's the answer.

The four cases are four relations over the change steps an effect is made of:

- case 1: both steps happen, order free (parallel)
- case 2: one step or the other happens (choice)
- case 3: both steps happen, order fixed (sequence)
- case 4: the first step causes the second (chain)

One shape holds all four: the effect is a small tree. The leaves are the change steps, the facts that moved together. The internal nodes are one of three relations:

- PARALLEL: all children happen, order free
- SEQUENCE: all children happen, in this order
- CHOICE: one child happens
                       
The four cases become four trees:
                                    
1. PARALLEL(B, C)
2. CHOICE(B, C)
3. SEQUENCE(B, C)
4. SEQUENCE(edge1, edge2), where B is the shared fact that joins the two edges

Case 4 is not one edge. It's two edges composed, and the chain is the SEQUENCE relation applied one level up, to edges instead of steps.

Two notes keep it honest. CHOICE is the odd combinator. It's not an ordering at all, and it's the incomplete-precondition signal: one instance of an action produces one effect, so "either" only appears before the edge has split. In finished knowledge a CHOICE node dissolves into two edges with fuller preconditions, which is how the precondition grows. And the raw record is already a degenerate tree, a SEQUENCE of PARALLEL bundles. The environment hands back ordered steps, each step the set of facts that moved together. PARALLEL across steps,and CHOICE, are what consolidation adds by seeing order wander or effects alternate across instances.
```

```
When it comes to experiential knowledge, the structure of the effect data should obviously be a mere sequence of frames. However, causal knowledge is supposed to be more structured than that, encapsulating the belief about the nature of the relationship between a cause and its effects.
```

```
Exactly. The two tiers carry the same event at two levels of commitment, and the effect's shape differs because the commitment does.

Experience records what happened. Its effect is a sequence of frames, because that's all the environment reports and all the agent should trust before it has drawn any conclusions. Order and timing, no belief.

Causal knowledge records what the agent believes about how it happens. Its effect is the tree, because the tree adds the one thing a sequence can't say: modality. A sequence says "B then C happened." The tree says "B and C always happen, in that order" (SEQUENCE), or "B and C always happen, order never matters" (PARALLEL), or "B or C happens, never both" (CHOICE). Those are claims of always, never, one-of, and they're what reasoning can lean on. The sequence is evidence; the tree is the conclusion drawn from it.

So the tree is both less and more than the sequence. Less, because it drops the exact frames and timing. More, because it adds the belief about which parts of the order are fixed, which are free, and which are alternatives. Consolidation is the step that lifts a sequence into a tree, and that lifting is where the belief gets formed.

And it respects the project's own boundary. Experience is fact, what happened. Causal knowledge is attribution, what the agent believes about the relationship. The environment reports sequences; the agent builds trees.

The two shapes exist because of the two uses. The sequence serves consolidation, the offline pass that forms beliefs. The tree serves execution, the live reasoning over those beliefs. That's the north star applied to the effect.

The question that opens next: is PARALLEL, SEQUENCE, CHOICE the complete vocabulary of those beliefs, or does the tree need more? A "usually" relation, for effects the agent can't yet explain, for instance.
```


<p align="center">· · ·</p>

Choosing the proper technology for storing causal knowledge is critical because the store must serve the agent's every lookup, and the wrong choice would fight it at every turn. Causal knowledge is a graph because the runtime's core move is traversal, which tables are worst at. An effect is not one change but several, and how those changes relate, ordered, parallel, or alternative, is itself part of what must be stored. The graph is held in memory because it is small, single-process, and traversed live at action time. We chose NetworkX over Neo4j because the agent traverses the graph live in one process, where an in-memory library fits and a server would add a round trip for nothing. The graph is serialized to a file because that is the simplest persistence method. Experience, flat and append-only, stays in SQL.

```
PARALLEL, SEQUENCE, CHOICE are the "known" vocabulary, so far. But that's not important right now. What's important is deciding on a data structure that fits our purpose.
```

```
One recursive type with a kind tag covers both tiers: Effect = Step(frame, facts), or Parallel(effects...), or Sequence(effects...), or Choice(effects...). Experience stores only Sequence(Step...). Causal knowledge stores the full tree. Same type, two uses, and consolidation upgrades a sequence into a tree without changing the shape.
```

```
I think you need to consider all potential data storage technology. SQL is not ideal for causal knowledge, if you haven't figured that out yet.
```

```
Right. Causal knowledge is a graph: facts as nodes, edges as links, effect trees nested inside the edges. The runtime's core move is graph traversal, which is the one thing SQL is worst at. A graph database if the graph grows; an in-memory object graph if it's small, single-process, and traversed live at action time, with JSON or a document store as the persistence format. Experience stays in SQLite: it's flat, append-only rows.
```

```
oh really? and exactly how would we store a causal relationship with multiple effects? how would we represent the different types of relationships?
```

```
The effect tree is nested data, not a graph and not a table. It lives inside the edge object, and each relationship type is a tag on an internal node. A node has a kind (step, parallel, sequence, choice) and an ordered list of children; a step leaf has facts instead of children. So the graph is between facts and edges, and the effect tree is a nested document inside each edge.
```

```
so effects are nodes, right?
```

```
Two kinds of node, and the distinction matters. The facts in an effect are nodes: the shared joints other edges connect to. The relationship types (parallel, sequence, choice) are nodes too, but structural nodes owned by a single edge. So an edge is a small subgraph: an action node linked through a parallel, sequence, or choice node down to its fact nodes.
```

```
if you wanted to say something like A causes B then C, what would be the nodes, what would be the edges, and exactly where does this sequential effect relationship get described?
```

```
Nodes: A (the cause), SEQUENCE (a structural node), B and C (fact nodes). Edges: A to SEQUENCE, then SEQUENCE to B and SEQUENCE to C. The 'then' is described in two places: the node type SEQUENCE says the order of its children is meaningful, and the child order carries the direction, B first and C second.
```

```
exactly! so nodes aren't just preconditions and effects (aka facts), are they?
```

```
Right. Three kinds of node: fact nodes, the shared vocabulary and the joints; action nodes, the cause; structural nodes, parallel, sequence, choice. Facts are the shared nodes; actions and structural nodes are local to one edge.
```

```
so let's go with precondition X, action A, effects E1 and E2 in sequence. give me the graph
```

```
Nodes: X (fact), A (action), SEQUENCE (structural), E1 (fact), E2 (fact). Edges: X to A (requires), A to SEQUENCE (produces), SEQUENCE to E1 (1st), SEQUENCE to E2 (2nd).
```


<p align="center">· · ·</p>

A command sometimes changes one thing and sometimes another, and those alternatives do not fit a settled belief. They are questions, not beliefs, because heavy branching is a symptom of an incomplete belief: one cause branching many ways is really several beliefs squeezed together without determining which change happens. So a tier of open questions sits between experience and causal knowledge, where anomalies are investigated rather than discarded.

```
hmmm. i don't like it because I think the node should be (X + A).
```

```
One consequence worth naming: X is no longer a graph node. It's inside the cause node. So chaining no longer traverses across X; it matches by fact identity, indexing which edge writes X and which cause node reads X.
```

```
just spit-balling here... X -> +, A -> +, + -> SEQUENCE, SEQUENCE -> E1, SEQUENCE -> E2
```

```
That works, and it's better than fusing them. + is a conjunction node, the cause, the edge's identity. X and A stay separate nodes, so both remain shareable: X is the joint other edges write, A is the command many edges reuse.
```

```
i don't know. to me it makes the graph look more bloated and less elegant. i'd like the set of nodes and edges to be as condensed as possible.
```

```
Then drop the structural nodes and put the relationship on the edges. Nodes: (X, A), E1, E2. Edges: (X, A) to E1 labeled 1st, to E2 labeled 2nd. Two node kinds total: cause and fact. Parallel, sequence, and choice become edge labels, not nodes.
```

```
that's pretty nice. now what happens if we complicate this scenario more by saying that there's a CHOICE relationship with E3, exclusive to (E1, E2)
```

```
The flat labels break, because now the choice's alternative is itself a sequence. Nesting needs depth, and there are two ways to get it back: structural nodes return as a pure graph, or the tree nests on the cause node as a field while the graph keeps edges only to the leaf facts for indexing.
```

```
what if the edge to effect contained a grouping index and relational type?
```

```
That's the right idea, and it generalizes: the grouping index is really a path, and the tree becomes a set of leaf paths. Each edge carries its path from the root, one relation and position step per level, and the tree reconstructs by grouping the paths. Three edges, no structural nodes, no nested field.
```

```
i should think that too much alternate paths from one causal node to its effects would actually be tantamount to confusion.
```

```
Right, and that instinct has a principle behind it: heavy CHOICE fan-out is the incomplete-precondition signal showing itself. One cause node with many alternate paths is one edge covering several edges' worth of situations. The fix isn't a better encoding, it's splitting: each branch becomes its own edge with a fuller precondition.
```

```
it seems to me that this shouldn't make it into causal knowledge. we almost have an intermediary system going on here, like curiosity or questioning or investigation or something.
```

```
Exactly. The unsettled stuff, alternate paths, uncertain order, missing preconditions, is not causal knowledge. It's a third tier between experience and knowledge: the questioning tier. Its units aren't edges, they're questions. A question holds the anomaly that sparked it, the candidate preconditions being tested, and the interventions run so far.
```


<p align="center">· · ·</p>

Determining the minimal schema for a settled belief matters because causal knowledge must be deterministic. A settled belief is a cause node whose edges to its effects carry value and confidence. Value and confidence ride on the edge because they are per-cause, not properties of a shared fact.

```
that means we need a more constrained causal knowledge schema
```

```
Right. Strip CHOICE out of causal knowledge and the schema tightens to one cause node to one effect tree, with PARALLEL and SEQUENCE as the only combinators, no alternatives, deterministic. CHOICE, unstable order, and missing preconditions all belong to the questioning tier.
```

```
will we ever even need PARALLEL vs SEQUENCE for reasoning, at least in Daggorath?
```

```
For reasoning, probably not. The environment's step waits for the command to settle, so the agent always acts on the final state. Backward chaining asks only 'does this edge write the fact I want,' never 'in what order does it write its facts.' So a settled edge's effect can be a plain set of facts. The tree is a consolidation-time structure that flattens to a set once the edge settles.
```

```
consider the following extension to our causal knowledge schema: (X + A) -causes-> E1, E2; E1 -happens-after-> E2
```

```
This is the DAG form, and it collapses the tree entirely. Ordering becomes a relation between effects, so PARALLEL is just the absence of an edge and SEQUENCE is one. The schema drops to cause and fact nodes with causes and happens-after edges. One question it raises: is the ordering edge scoped to this cause, or a global claim between E1 and E2?
```

```
i don't know that we should try to normalize the graph to only ever contain one instance of an effect node.
```

```
Right, and that resolves the scoping problem. If each edge owns its effect occurrences, the happens-after edge lives between them and is scoped by construction. Facts stop being shared nodes and become identifiers, the join key. Chaining matches by fact id, this edge's effect against that edge's precondition.
```

```
what would be the problem with having one instance for each effect?
```

```
The effect's content isn't 'fact F changed.' It's 'this cause wrote F to this value, at this position, with this confidence.' One global node per effect can hold none of that. The value differs per cause, the order is scoped to one cause, and the confidence accrues to an edge, not a bare fact.
```

```
what's wrong with writing the confidence the the 'causes' edge?
```

```
Nothing. Confidence belongs on the causes edge; it's per cause and effect, which is the right granularity. And the same move dissolves the other two objections: the written value rides on the causes edge too, and the order rides there as position.
```

```
forget the happens-after edge. just write the order of causation in causes edge if needed. parallel causation gets a zero.
```

```
That settles it cleanly. The schema is a cause node (X + A) and causes edges to effect facts, each carrying value, order, and confidence. The order is an integer: 0 for parallel, 1 and up for sequence position. No happens-after edges, no structural nodes. The whole effect is a set of causes edges with an integer each.
```

```
that's way more deterministic now
```

```
Right. One cause, one set of effects, fixed values, fixed order. No alternatives, no branching, nothing conditional. Whatever isn't deterministic now lives in the questioning tier by definition.
```

```
experiences, questions, beliefs
```

```
Locking the vocabulary. Experiences are what happened, sequences of frames. Questions are what's unsettled, anomalies, candidate preconditions, experiments. Beliefs are what's settled, the deterministic edges. This supersedes the plan's two-tier split: expectations become beliefs, and questions are the new middle tier.
```

```
how does that sound to you, epistemically?
```

```
It's sound, and it tracks a real epistemic structure, Peirce's doubt-belief cycle. Experiences are the empirical given, questions are doubt made first-class, beliefs are the settled end, revisable. Its strength is making uncertainty a place where work happens and revision structural, a contradicted belief falls back into a question. The one caveat: the boundaries are thresholds, not kinds, and confidence is the continuous variable that does the blurring.
```

```
it's important to have these different buckets though. because each is intended to be utilized for reasoning and action in their own way, they need different structures.
```

```
Exactly. Each bucket serves a different moment in the cycle, and the structure follows the use. Experiences are the evidence, flat ordered append-only sequences. Questions are the inquiry, tentative and growing. Beliefs are the action, the deterministic graph indexed by fact for backward chaining. Three structures because three uses.
```

```
i think questions also serve as a way of reducing repetitious work when processing experiences.
```

```
Right. Questions are the incremental state of consolidation. They remember what's already under investigation, so each new experience only gets matched against open questions and settled beliefs, not re-scanning the whole history. Questions are the working memory that makes learning incremental.
```

```
yeah. questions are gonna need to be polymorphic structures, i think.
```

```
Right. Questions come in kinds, each with its own payload and its own resolution: missing precondition, unstable order, chain versus fork, false causation. So a question has a common core, the anomaly, its status, its evidence, plus a variant body per kind, and each kind resolves its own way.
```

```
yeah, questions have to be tied back to experiences somehow so that new experiences can wind up creating new questions or resolving old ones.
```

```
The tie is two things: a key and a set of references. The question carries the action and the facts it concerns as its key. A new experience arrives carrying the same action and facts, so routing is an index lookup. It matches an open question and feeds it evidence or resolves it, matches a settled belief and confirms or contradicts it, or matches neither and shows an anomaly, spawning a new question with that experience as its first evidence.
```

```
that's one possible way, assuming an action + facts index is always applicable to all questions.
```

```
Fair. The key is part of the polymorphic payload, not the common core. Missing precondition keys on the same action and alternating effects; unstable order keys on the same action and effects; chain versus fork keys on the same two facts regardless of action; false causation keys on the contradicted belief. Each kind defines its own 'does this experience bear on me' test. What stays common is the anomaly, the status, and the evidence.
```

```
yep
```

Afterward, the order field was questioned and dropped:

```
why would the belief carry order if it's never utilized?
```

```
Order has no consumer. Reasoning never reads it, and consolidation reads the full sequence from experience, so the belief should carry value and confidence only.
```

```
Are you sure it's a leftover? Are we saving it for later?
```

```
Not sure. The dialog wrote it "if needed," which is a hedge, not a decision. Calling it a leftover over-claims.
```

```
Maybe we should decide, or bear the hedging openly.
```

```
Decide and drop it. The project's rule is not to carry data with no consumer, and adding a field back later is trivial.
```

```
Fine with dropping it.
```

## Questions

**Experiences reach beliefs only through questions.**

Settling beliefs can sometimes require long term investigation. Such investigations need evidence gathered over many iterations, and they hold state while they run: the evidence gathered so far and the hypothesis under test. That state must persist, or the agent would re-derive the whole investigation from raw experiences every time it returns to it. Questions should be that place, and every experience should pass through a question before it supports or weakens a belief. Passing straight to the belief would split the evidence, part in the question and part in a confidence counter, leaving no single source of truth. When a question settles into all of its beliefs, it should go dormant. It should keep its evidence, because that is where a belief's confidence comes from, and because a contradiction needs to reopen the question with the conflicting experience as new evidence. Experience to question, and question to belief, are both many-to-many relationships. One experience changes several facts, so it feeds several questions, while each question gathers evidence from many experiences. One question can split into several beliefs, while several questions can converge on one.

```
Is "questions" really a tier in the same sense as the other two? Experiences and beliefs are things you store and keep. A question exists only until it resolves into a belief, then it's gone. The store plan's two tiers were both persistent stores. So "three tiers" may be miscounting: two stores, plus a transient working layer.
```

```
Do humans only remember questions while they're thinking about them for the first time?
```

```
No. A person remembers the questions they've asked even after answering them, and remembers the ones they never answered at all. Two forms, then. An open question persists because it's still unresolved. And a resolved question persists as the belief's provenance: what I once wondered, what evidence settled it, and how I could reopen it if the belief gets contradicted. So "transient" was wrong. Questions change state, open to resolved, and the resolved one stays attached to the belief it produced. The three tiers are all stores; they differ in lifecycle, not persistence.
```

```
Right. Questions might go dormant but they don't disappear.
```

```
That's the right word. A question has a state: active while under investigation, dormant once resolved. Resolution doesn't delete it; it links it to the belief it produced. And contradiction reactivates the dormant question, reopening the investigation with its old evidence still intact. So the question's shape isn't just polymorphic, it's stateful.
```

```
I think your description of the lifecycle between tiers is accurate and useful for now.
```

```
Isn't a contradiction new evidence itself?
```

```
Right. A contradiction isn't a separate event; it's an experience that lands and conflicts with what a belief predicts. That experience is itself the new evidence. Experience is the sole input. It routes to an open question and feeds it, routes to a belief and matches, confirming it, or routes to a belief and conflicts, and then the belief's dormant question reopens and the conflicting experience becomes that question's fresh evidence. The fallback isn't "reopen and wait for evidence."
```

```
We may want to consider relationship cardinality between tiers.
```

```
Mapping them: question to experience is one-to-many, belief to experience is one-to-many, and question to belief is one-to-many. The interesting case is the contradiction, one experience touching two tiers at once.
```

```
also, are we sure there should be a direct relationship between experience and belief, or should we always progress through question first?
```

```
I think always through the question is the right call, and the direct route is the mistake. The question is the home of evidence. If confirming experiences go straight to the belief, the evidence splits: everything before resolution sits in the question, everything after sits in a confidence counter on the belief. Always through the question keeps one source of truth. The belief's confidence is derived from the question's evidence, not maintained separately.
```

```
yeah. it's simpler and more stable.
```

```
now let's finish cardinality. consider the following: experience -> question: n->1 or n->n? question -> belief: 1->1 or 1->n or n->n? sorry. for question -> belief, i think i meant n->1 vs 1->n
```

```
experience to question: n to n. A question gathers many experiences, and one experience can serve several questions at once, because it changes several facts and each question keys on different ones, a kill feeding the kill, exertion, and strength questions in the same step. Forcing n to 1 would be lossy. question to belief: 1 to n. A question resolves into one or more beliefs, splitting when it finds the missing facts, like ATTACK splitting into reachable-kills and unreachable-misses.
```

```
are we sure question -> belief is not n->n?
```

```
You're right to push. Merging is real too. Two questions about the same relationship from different angles can resolve to the same belief, like the torch-light question and the dungeon-brightness question both settling on USE producing light. So question to belief is n to n.
```

```
nope. cardinality is always n->n for these tiers.
```

```
Settled then: a chain of three tiers, many-to-many at each hop. Experience never reaches belief directly.
```

```
i don't know. why don't you try thinking about something we haven't considered yet?
```

```
A few things we haven't touched: what earns an experience a question, evidence attribution when a question splits or merges, and the experience's own full shape.
```

```
Those feel like new outline items.
```



## Plans

**Planning finds a path through beliefs about what actions can be taken to get from a situation to a goal.**

Reaching a goal takes a chain of actions, not one, and the agent must find that chain before it can act. A plan is the found chain: a precondition, a series of actions, and an expected outcome. The agent builds it backward from the goal, each belief's effect applied to a state producing the next precondition, and it caches the plan as a composite belief, checking each step's expected outcome as it executes.

```
I don't think that we chain randomly. I think we do path finding.
```

```
Right, path finding, not chaining. The plan is a path of beliefs from the current situation to the goal, found by searching backward through preconditions.
```

```
chain together according to what, through to what?
```

```
By shared facts: one belief's effect is the next belief's precondition. The path runs from a belief the current situation satisfies, through to a belief whose effect is the goal.
```

```
I don't think we've really worked out "acting" yet. We just know that if we can find at least one path from situation to goal, we could act on it.
```

```
Right. The planning half is worked out. The acting half is just a presumption, take the first belief on a found path, and nothing beyond that is designed.
```

```
a plan is a series of actions and an expected outcome
```

```
a plan also has a precondition
```

```
an effect is a change to be applied. it has to be applied to a given state to produce an outcome. that outcome is the next belief's precondition.
```

```
the outcome must "match" the next precondition, which may be a fuzzy algorithm.
```



<p align="center">· · ·</p>

Applying effects and matching fuzzily makes path finding look intractable, so plans should be cached. A memorized plan is a composite belief, keyed by situation and goal, and it is reused by the same fuzzy match. When a belief changes and a plan fails, the agent attempts anyway and diagnoses the failed step.

```
because of the need to apply an effect and to match fuzzily, we're potentially treading into intractability territory, similar to the traveling salesman problem.
```

```
Yes, this is state-space search, and in the worst case it's intractable, the same family as traveling salesman. The fuzzy match widens it, because more beliefs can match a precondition, and each is a branch. But the design already carries two mitigations. Backward chaining only considers beliefs that write the fact it currently needs, an inverted index that prunes most of the graph. And execution is a symbolic search with a learned heuristic: the reasoner ranks which candidate to try first, so the search follows the promising branch rather than expanding everything. Whether a ranked backward search stays tractable at Daggorath's scale is the thing to validate, not assume.
```

```
we might want to consider memorizing plans, keyed by situation and goal.
```

```
That's plan caching, and it's the right counterweight to the search cost: find a plan once, remember it, reuse it next time the situation and goal are close. A memorized plan is a composite belief: its precondition is the situation, its action is a series of commands, and its effect is the expected outcome. Keyed by situation and goal, which is exactly the belief's key, precondition and effect. So the belief's action generalizes: one command for a primitive belief, a remembered sequence for a plan. The plans sit in the beliefs tier, and the reasoner's job shifts from finding paths to retrieving and adapting cached ones.
```

```
what happens to plans when beliefs change? do we just attempt anyway and go into diagnostic mode upon failure?
```

```
Yes, and that's exactly how the model already treats beliefs. A plan is a composite belief, so its failure is a contradiction of it. The agent attempts the plan, and if the expected outcome doesn't materialize, that failure is the new evidence that contradicts the plan as a belief. Then diagnosis kicks in: find which step failed, reopen that step's belief, and re-search from there. The wasted attempt isn't pure waste; it's the contradiction signal that feeds the diagnosis. The alternative is eager invalidation, tracking which beliefs each plan chains through, but attempt-and-diagnose is simpler and the game is forgiving enough.
```

<p align="center">· · ·</p>

A plan cannot track only its final outcome. Each step should carry its own expected outcome, scoped to the facts that matter, so failure is caught at the step and the world's own motion is ignored. The slack both matchings need points to a learned matcher rather than hard-coded rules.

```
i think not only should we track the final outcome expected from executing a plan, but we should track each expected outcome while executing each step.
```

```
Right, and that's what turns the plan from a black box into a sequence of checkpoints. Each step is an action plus its expected intermediate outcome. Execution verifies after each step, comparing the actual state to the expected one. That localizes failure, you know which step's expected outcome didn't materialize, and catches it early, stopping rather than running the remaining steps on a plan that already left the rails. It's also the path through facts made concrete: the chain of states the actions are supposed to walk.
```

```
our expectations cannot be brittle. we have to be careful to watch for only things that matter.
```

```
Right, the checkpoints can't be full-state equality, or the world's own motion makes every plan fail. The heart beats, creatures move, the torch burns, and none of that is the plan's business. So each step's expected outcome is scoped: it names only the facts the next step depends on, the ones its precondition reads. The check compares only those facts and ignores everything else.
```

```
the flexibility we need, in both precondition matching and expectation matching, seems to point toward neural nets vs hard-coded rules.
```

## Judgment

**Matching is too fuzzy for rules; the judgment is learned.**

Precondition and expectation matching both need slack, and hard-coded rules are too brittle to supply it. The judgment should be learned: a neural matcher that reads the symbolic chain, which stays readable, and judges matches fuzzily. The training signal is self-consistency, whether the judged match predicts the observed effect, and the no-action baseline is the control, the world's own motion as the negative example, so the matcher learns contingency, not similarity. It should start from the symbolic rule as its baseline, not random weights, and learn only the fuzzy remainder.
```
the flexibility we need, in both precondition matching and expectation matching, seems to point toward neural nets vs hard-coded rules.
```

```
It does, and it lands exactly where the earlier discussion already drew the line. Knowledge stays symbolic, reasoning is learned. The fuzzy, scoped matching is the reasoning layer. The belief, the plan, the scope of facts each checkpoint watches, all of that stays symbolic and readable: you can still look at a plan and see "PULL then USE." What's learned is the judgment: does this situation satisfy the precondition, did this step's outcome materialize. That's what a neural matcher does well and hard-coded rules do brittly. So it's not a choice between the chain and the network. It's the two-layer split: the network reads the symbolic chain, judges the matches fuzzily, and never writes it. The chain stays the ground truth; the network is the reasoner over it. That's the self-consistency training signal too: the matcher learns by how well its judgments predict the observations that follow.
```

```
i like that.
```

```
it's not settled. we want to think a little further on training judgement.
```

```
The training signal is self-consistency: a match judgment is good if the effect it predicted actually follows. Every attempt is a training example. The agent judges that a situation matches a precondition, acts, and the observed outcome is the label, did the effect materialize or not. The no-action baseline is the control. The world's own motion is the negative example: if the effect shows up anyway without the action, the judgment wasn't reading the cause. So the matcher isn't trained to recognize similarity; it's trained to recognize the contingency, does the effect follow the action under this match, and not otherwise. That's what keeps the fuzziness from sliding into superstition. A fuzzy match is good only insofar as it predicts. The matcher learns which slack in the match still predicts the effect, and which slack is noise, by accumulating cases where it acted and saw what followed. And its uncertainty feeds the questions tier. When the matcher can't tell whether a match is causal, that's exactly when the agent should stop and investigate rather than trust the judgment.
```

```
i think it would waste training cycles to start out with a set of weights that didn't act as a reasonable baseline for judgement.
```

```
The symbolic layer is the baseline. The matcher shouldn't start from random weights; it should start as the exact match on the declared scope, and training only learns the deviation from it, how much slack each fact can take and which facts actually predict. Two ways to arrange that. A residual matcher: exact symbolic match plus a learned correction, the correction initialized to zero, so the early cycles behave like the rule and improve from there. Or a cascade: the symbolic rule handles the clear matches, and the network only takes the cases where the rule is uncertain, which is exactly the residue that became questions. The second one has a nice property. The matcher's training data is the questions that the rule's uncertainty opened, and their resolutions are the labels. The network gets trained on exactly the cases the symbolic rule couldn't handle, never re-learning what the rule already does.
```

## Open questions

- How should knowledge from different lessons be combined into one full picture without dragging in each lesson's blind spots?
- How is the world's own motion captured, and which facts does the agent control?
- How is a causal link caught and corrected when it later turns out wrong, across sessions?
- What does execution match on, and how does a loose match weigh a cause by how it turned out before?
- How is confidence measured, and should it control how long the agent waits?
- What makes two experiences the same belief, so consolidation can group many transitions into one belief?
- How does a belief name its situation, and how does the agent test whether the current situation satisfies it?
- What earns an experience a question, the threshold below which an experience is just recorded, never investigated?
- How does evidence divide when a question splits into several beliefs, or several questions merge into one?
- What is an experience's full shape, beyond the situation, the action, and the effect's sequence of frames?
- How does the agent act on a found plan: which belief it takes, how it chooses among several paths, and what it does when a path fails?
- Does a ranked backward search stay tractable at Daggorath's scale?

## Reference

| Document | What it contains |
|---|---|
| [`knowledge-and-reasoning.md`](knowledge-and-reasoning.md) | The theory — why knowledge lives outside the weights |
| [`curriculum.md`](curriculum.md) | The lesson ordering and the per-lesson rewards the valuation layer feeds |
| [`../../sandbox/command-latency/`](../../sandbox/command-latency/README.md) | The experiment measuring the three moments |
| [`../../sandbox/causal-diff/`](../../sandbox/causal-diff/README.md) | The probe computing the effect diff |
| [`../2_plans/knowledge-store.md`](../2_plans/knowledge-store.md) | The storage spec: the data model and the storage choice |
