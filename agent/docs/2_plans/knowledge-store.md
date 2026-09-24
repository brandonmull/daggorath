# Knowledge Store — Plan

_A pre-build spec for the store: how experiences, questions, and beliefs are stored. The shapes come from [`../1_discussions/knowledge-representation.md`](../1_discussions/knowledge-representation.md)._

## What gets stored

The store holds three tiers, each with its own shape.

- An **experience** is the raw record of one step: the situation, the action, and the changes that followed, in order.
- A **question** is an investigation still in progress: the anomaly that sparked it, the hypotheses being tested, and the evidence gathered so far.
- A **belief** is a settled causal claim: a cause node, the situation and action, with edges to its effects carrying value and confidence.

## The representation

The full state is a list of facts, each a name bound to a value.

- The **mask** is the selection over the fact list: which facts a belief reads and which it writes. It is what the belief is indexed by.
- The **value** is the content a fact holds: what an effect writes and what a precondition matches. Confidence joins the value on an effect edge.

The selection has three uses:

- an **effect** selects the facts a belief writes;
- a **precondition** selects the facts a belief reads;
- a **lesson scope** selects the facts a lesson trains on.

The mask is the index and the value is the payload.

The data is stored sparse, fact ids as keys, with names never entering the records. The judgment network should stay small, cheap to train and fast at decision time. A network that interprets ids and values directly would have to learn an embedding for every fact, which enlarges it and duplicates what the fact list already knows. So the interpretation should live in code rather than the network. As the fact list grows, the network's input grows with it, and the open question is how to expand it without disturbing the judgment it already has. One candidate is to grow the weight set with each new fact, the new weights defaulting to keep the output stable until they are learned.

## Fact list and scope

The fact list is the global schema: one id per fact, permanent and never reused or reordered. Every record references facts by id, a belief's mask, a question's key, an experience's situation and effect, a lesson's scope, so renaming a fact or reordering the list leaves every reference intact. Adding a new fact appends a new id and leaves existing records untouched.

The id is assigned from a counter that only increases, so no id is ever reused. The list is append-only, new facts go to the end, nothing is reordered or deleted, and the name is a field on the entry, so a rename updates the name while the id stays put. The data stores ids, not names, and interpretability comes from resolving each id against the fact list. The fact list ships alongside the data, so any record stays readable by looking its ids up.

A lesson's scope is an ordered subset of the fact list, stored as an array of fact ids on the lesson row. It says which facts the lesson cares about, and every other fact is dropped when the lesson compares situations. Two lessons can share a fact, and that shared fact is the overlap the combination step must reconcile.

Two things are immutable. Fact ids are permanent. Scopes are immutable: a lesson's scope never changes, and a changed scope is a new lesson row. The name stays the same across those rows, so the name is the stable handle for the concept and the lesson id is the version. The goal is not part of that identity. It is tuned between runs, so it is recorded per session instead of versioned into the lesson.

## Data model

The store is split by where each tier lives.

**Experiences** are rows in SQL: the situation, the action, and the effect, each referencing its session.

**Beliefs** are the JSON graph: a cause node per belief, each effect edge carrying a value and a confidence.

**Questions** persist alongside, carrying the anomaly, the hypotheses, and the evidence, and the beliefs each settled into.

**Facts** are the global schema, one id per fact. **Lessons** carry the scope over the fact list, and **sessions** carry the goal and own their experiences.

## Storage

The store is split by shape. The fact list is a flat JSON list, one entry per fact: its id, its name, and its value type. The beliefs are a NetworkX graph, serialized as JSON. The questions are their own JSON records, each carrying the anomaly, the hypotheses, and the evidence. Experiences stay in SQL, flat append-only rows, alongside two small tables, a lesson carrying its name and scope, and a session carrying its goal and referencing its lesson. The store is embedded and single-agent, so files fit and a server does not.

## Open items

- What counts as one fact: the granularity, and where the first facts come from.
- How the judgment network's input grows with the fact list, and how to keep its judgment stable as it does.
- What earns an experience a question: the threshold below which an experience is just recorded.
- How evidence divides when a question splits into several beliefs, or several questions merge into one.
- How confidence is computed from a question's evidence.
- How the agent acts on a found plan.
- Whether a ranked backward search stays tractable at Daggorath's scale.
