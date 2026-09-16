# Knowledge Store — Plan

_A pre-build spec for how experiences are stored. Expectations are named but their storage is not yet designed. The concepts and open questions live in [`../1_discussions/knowledge-representation.md`](../1_discussions/knowledge-representation.md)._

## What gets stored

The store holds two kinds of data, and this plan specifies only the first. An experience is one transition: where things stood, what the agent did, what changed, and how the outcome was judged. An expectation is one distilled claim about what causes what, drawn from many experiences; its storage shape is not yet designed and belongs to a later plan.

## The representation

The full state is a list of facts, each with a permanent id and an encoding. A vector selects some of those facts and records their values.

- The **mask** is the set of selected facts, read off the vector as the facts that appear in it. It is computed at write time and stored as an indexed column, because the application is the only writer and computes the mask from the vector in the same write.
- The **values** are the content at the selected facts.

The discriminator names what the selection is for:

- an **effect vector** selects the facts that changed;
- a **situation vector** selects the facts that identify the situation;
- a **lesson scope** selects the facts a lesson trains on.

The mask is the reliable classifier and the values are the payload. Each experience is indexed by its mask and stored with its values.

## Fact list and scope

The fact list is the global schema: one id per fact, permanent and never reused or reordered. Adding a new fact appends a new id and leaves every stored vector untouched.

A lesson's scope is an ordered subset of the fact list, stored as an array of fact ids on the lesson row. It fixes the vector shape within that lesson and doubles as the index map: position i in a lesson's vector is whatever fact sits at i in that lesson's scope. Two lessons can hold the same fact at different positions, and that shared fact is the overlap the combination step must reconcile.

Two things are immutable. Fact ids are permanent. Scopes are immutable: a lesson's scope never changes, and a changed scope is a new lesson row. The name stays the same across those rows, so the name is the stable handle for the concept and the lesson id is the version. The goal is not part of that identity. It is tuned between runs, so it is recorded per session instead of versioned into the lesson.

## Data model

The store is normalized around five relations.

| Relation | Key | Meaning |
|---|---|---|
| facts | fact id | one fact of the game state, permanent id and encoding |
| lessons | lesson id | one curriculum unit: its name and its immutable scope |
| sessions | session id | one playthrough, referencing its lesson and carrying the goal in effect |
| experiences | record id | one transition: situation vector, action, effect vector, judgment, referencing its session |
| expectations | not yet designed | the distilled expectations, one per row, specified in a later plan |

Relationships, reading "owns" as "references":

- a lesson carries its scope and owns its sessions;
- a session carries its goal and owns its experiences;
- an experience carries its situation and effect vectors as sparse maps from fact id to value;
- an experience's facts stay interpretable through experience → session → lesson → scope.

## Storage

SQLite now, `sqlite-vec` later if the representation moves to continuous embeddings. The store is embedded, append-heavy, and single-agent, so a file-backed store fits and a server does not.

## Open items

- The sentinel for a fact that is selected but has no value yet.
- The mechanics of the mask index: computed at write time and indexed, since the database cannot generate it from the stored vector.
- What consolidation reads: the batch queries that turn experiences into expectations.
