# Command Consumption

_See [overview.md](../../../docs/overview.md) for project context and architecture._

## Purpose and scope

The command-latency sandbox triangulates three signals of a command's life — *matched*, *written*, *executed*. This plan puts *matched* and *executed* on the wire as state fields; *written* (`command_area_text`) already ships. The parser leaves five markers in RAM that form the "command-consumed fingerprint" catalogued in `gym/docs/findings/ram-signals.md`: `command_parser_matched_exactly` (0x027B), `command_parser_matched` (0x0278), `command_parser_word_count` (0x0279), `where_to_print` (0x02B7), and `command_parser_position` (0x0211).

The scope is those five fields, filed into the state schema as a new `consumption` category, non-perceived. This resolves the open question left in `../1_discussions/extensibility.md` — whether these flags ship as state fields or as the separate event record `../1_discussions/events.md` proposes. The answer here is a state field: they are facts about the parser, read every frame like the other scalars, and the sandbox reads them through the environment rather than an event channel.

## The fields

Five true-state fields (the player does not see the parser's internals); four are one-byte, `command_parser_position` is two. The matched signal is `command_parser_word_count`: it resets to 0 between commands and goes 0 → N → 0 as the word table is checked, so the moment it jumps from 0 marks each match. `command_parser_matched_exactly` flips to 0xFF on a match but stays set; its clear and set happen inside one word decode, so the zero lasts less than a frame for words that match early in their table. `command_parser_matched` is 1 when at least one word matched, and `where_to_print` is 255 while output is redirected to echo the command — companions that cross-check the match. The executed signal is `command_parser_position`, the game's cursor into the command line, which snaps back to its resting 0x02F1 once a command has run; paired with the `???` echo (`command_rejected`) it separates executed from rejected. The companions matter because the sandbox's first success criterion is "does a command that changes nothing still match?" — a lone flag cannot be trusted until the fingerprint confirms it.

| Field | Address | Meaning |
|-------|---------|---------|
| `command_parser_matched_exactly` | 0x027B | 0xFF on a complete, valid match; stays set |
| `command_parser_matched` | 0x0278 | 1 when at least one word matched |
| `command_parser_word_count` | 0x0279 | word-table counter; its 0 → N edge marks each match |
| `where_to_print` | 0x02B7 | 255 while output echoes the command |
| `command_parser_position` | 0x0211 | a cursor into the command line; its snap back to 0x02F1 marks the command finishing |

## Where they land

Each field is filed into `FIELDS` (Python) and `SCHEMA` (Lua) under a new `consumption` category, after `mode` — the parser's state sits next to `game_mode`, which is itself a parser fact. Both sides pick the new category up automatically; no other code changes.

## Reference Documents

| Document | What It Contains |
|----------|-----------------|
| `gym/docs/findings/ram-signals.md` | The command-consumed fingerprint — the five addresses and their meanings |
| `../1_discussions/extensibility.md` | The open question this plan resolves |
| `../1_discussions/events.md` | The deferred event channel this plan declines |
| `../../../agent/sandbox/command-latency/README.md` | The sandbox whose *matched* and *executed* moments these fields serve |
