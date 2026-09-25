# Knowledge Store — Plan

_A spec for building the store. The vocabulary and the reasoning behind it live in [`../1_discussions/knowledge-representation.md`](../1_discussions/knowledge-representation.md); this doc only says what to build._

## Scope

Build one embedded DuckDB store with discrete matching in code. No network, no questions tables yet. The first build records experiences, holds facts and beliefs, and searches beliefs backward to find a plan. The point is something playable that the game can correct, not a theory.

## The store

One DuckDB file, opened inside the agent's process, no server. All the tables below live in that file. DuckDB's list types carry a scope and the sparse fact lists directly.

## Tables

A sparse fact set is one column of (fact id, value) pairs. The id is the key and the value is the payload, so no name ever enters a record; resolving the id against the fact table gives the name, and the fact's value type says how to read the value.

**fact** is the global schema, append-only.
- `id` INTEGER: permanent, from a counter that only increases
- `name` TEXT: renaming changes this, the id stays
- `value_type` TEXT: how to read the value

**lesson** is a named scope over the fact list.
- `id` INTEGER
- `name` TEXT: the stable handle; a new scope under the same name is a new row
- `scope` INTEGER[]: ordered fact ids, immutable

**session** is one run with a goal.
- `id` INTEGER
- `goal`: what the session pursues
- `lesson_id` INTEGER: the lesson the session trains

**experience** is the raw record of one step, append-only.
- `id` INTEGER
- `session_id` INTEGER
- `situation`: the facts that held before the action, as sparse pairs
- `action`: the command
- `effect`: the facts that changed, as sparse pairs, in order

**belief** is a settled cause.
- `id` INTEGER
- `situation`: the facts the belief reads, as sparse pairs
- `action`: the command

**belief_effect** holds the facts a belief writes.
- `belief_id` INTEGER
- `fact_id` INTEGER
- `value`: the value written
- `confidence`: how reliable the effect is

## Operations

```
record_experience()
    → appends one row to experiences
    → stores the situation and the effect as sparse pairs
    → writes nothing else: recording makes no judgment

settle_belief()
    → inserts one belief row with its situation and action
    → inserts one effect row for each fact it writes, with its value and confidence

find_beliefs_writing()
    → finds the effect rows that name the wanted fact
    → returns each with its cause and confidence

find_satisfied_beliefs()
    → finds the beliefs whose situation facts are all present in the state
    → tests each situation value against the state by the discrete rule
    → returns the beliefs that hold

search_backward()
    → starts from the wanted fact
    → finds the beliefs that write it
    → tests each one's situation against the state
    → recurses on any situation fact the state lacks
    → returns a chain of beliefs from the state to the goal
```

## Deferred

- The questions tier, its tables and lifecycle.
- Fuzzy matching and a learned judgment. Matching stays discrete until the rules meet the game and show where they break.
- Archiving old experiences.

## Open items

- What counts as one fact, and where the first facts come from.
- The exact DuckDB encoding of a sparse (fact id, value) pair: a list of structs or two aligned lists.
- How confidence is set on a hand-settled belief before any evidence.
- Whether the iterative backward search stays tractable at Daggorath's scale.
