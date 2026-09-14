# Command Consumption

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The causal-timing sandbox triangulates three signals of a command's life — *matched*, *written*, *executed*. This plan adds only *matched*; *written* (`command_text`) and *executed* (the state change) already ship. The parser leaves four transient markers in RAM: `perfectMatch` (0x027B), the one that fires only on a complete, valid match, and three that change at the same instant — `foundMatch` (0x0278), `numWords` (0x0279), and `whereToPrint` (0x02B7) — which together form the "command-consumed fingerprint" catalogued in `gym/docs/findings/ram-signals.md`.

The scope is those four bytes, filed into the state schema as a new `consumption` category, non-perceived. This resolves the open question left in `../1_discussions/extensibility.md` — whether the recognition flag ships as a state field or as the separate event record `../1_discussions/events.md` proposes. The answer here is a state field: it is a fact about the parser, read every frame like the other scalars, and the sandbox reads it through the environment rather than an event channel.

## The fields

Four one-byte, true-state fields (the player does not see the parser's internals). `perfect_match` is the primary signal: it flips to 0xFF when the parser finishes a complete, valid match. The three companions change at the same instant and cross-check it — `found_match` is 1 when at least one word matched, `num_words` is 0 when the word table is exhausted, and `where_to_print` is 255 while output is redirected to echo the command. The companions matter because the sandbox's first success criterion is "does `perfect_match` fire on a command that changes nothing?" — a lone flag cannot be trusted until the fingerprint confirms it.

| Field | Address | Meaning |
|-------|---------|---------|
| `perfect_match` | 0x027B | 0xFF on a complete, valid match |
| `found_match` | 0x0278 | 1 when at least one word matched |
| `num_words` | 0x0279 | words left in the match table; 0 when resolved |
| `where_to_print` | 0x02B7 | 255 while output echoes the command |

## Where they land

Each field is filed into `FIELDS` (Python) and `SCHEMA` (Lua) under a new `consumption` category, after `mode` — the parser's state sits next to `game_mode`, which is itself a parser fact. Both sides pick the new category up automatically; no other code changes.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `gym/docs/findings/ram-signals.md` | The command-consumed fingerprint — the four addresses and their meanings |
| `../1_discussions/extensibility.md` | The open question this plan resolves |
| `../1_discussions/events.md` | The deferred event channel this plan declines |
| `../../../agent/sandbox/causal-timing/README.md` | The sandbox whose *matched* moment these fields serve |
