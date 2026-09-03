# Commands Module

_1 Sep 2026_

## Decision

The 154 valid command phrases are enumerated from eight command words, a direction table, and six object classes (25 proper names), then factored into a `MultiDiscrete([26, 31])` action space — a (verb form, object specifier) pair — whose object axis reuses the observation's 31 specifier indices.

## Why

- **Factor the choice, not the list.** Splitting one flat 154-way choice into two axes collapses 124 GET/PULL buttons into four templates plus one shared object index. The agent acts on an object by echoing the index it observed — zero translation.
- **The INCANT restriction is joint, not per-axis.** "Object 25 is valid for PULL LEFT but invalid for INCANT" cannot be expressed by SB3's independent per-axis masks; it needs an autoregressive or custom policy. The environment's `derive_command_index` returns `None` for the invalid pair and `step()` no-ops now; the joint mask is a later consumer.
- **Prevent what you can, punish what you can't.** A syntactically-invalid pair is an artifact of the factorization — there is nothing to learn, so it is prevented (no-op), never penalized. A semantically-invalid command is state-dependent, learnable structure only the game can judge, so the game's own `???` verdict is surfaced and priced (~−0.1), charged once per rejection.

## What Changed

- `daggorath_gym/commands.py` — grammar constants, phrase builders, the 31 specifiers, `derive_command_index`, `DaggorathCommand`.
- `emulation/plugins/daggorath/commands.lua` — the mirrored grammar and `COMMAND_PHRASES`, dispatch via natkeyboard.
