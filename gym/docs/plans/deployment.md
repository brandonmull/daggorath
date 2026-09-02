# Deployment

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose

Deployment is the umbrella for how a trainer obtains and runs the environment. The implemented half — the package split, the import boundary, and the reference trainer — is recorded in the deployment decision (`../decisions/deployment.md`). This plan covers the remaining half: **registration** — making `gymnasium.make("Daggorath-v0")` resolve within the repo.

Registration is code-side — the `gymnasium.register` call that names the environment. It is distinct from distribution, publishing the package to the public repository, which is out of scope here.

## Scope

- Register `Daggorath-v0` in `daggorath_gym/__init__.py`, as a side effect of import, pointing at `DaggorathEnv`. The environment already constructs with no arguments, so nothing else needs wiring.
- Register the raw environment only — the reward wrapper stays an explicit opt-in, never a second id.
- Resolve Known Issue #1 and drop it from `gym/README.md`.

## What registration does

importing `daggorath_gym`
    → registers `Daggorath-v0`
    → a trainer obtains the environment through gymnasium.make
    → the reward wrapper is applied on top, never registered

## Decisions

- **One id, the raw environment.** `Daggorath-v0` is the objective world (`reward == 0.0`); the reward wrapper is an opt-in, so the world and its worth stay separate.
- **Registration is code-side, not distribution.** This plan covers the `gymnasium.register` call only; publishing to the public repository is separate and out of scope.
- **Registration is a side effect of import.** No separate setup step — importing `daggorath_gym` registers the id.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `../decisions/deployment.md` | The implemented half — package split, import boundary, reference trainer |
| `../../../README.md` | Known Issue #1 — the gap this plan closes |
