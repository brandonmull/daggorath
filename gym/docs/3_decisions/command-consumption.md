# Command Consumption

_16 Sep 2026_

## Decision

The state schema gains a `consumption` category: five true-state fields that form the parser's command-consumed fingerprint. None reaches perception; the player never sees the parser's internals. Four fields are one byte, `command_parser_position` is two. They ship as state fields, not as the separate event record the events discussion proposed.

| Field | Address | Meaning |
|-------|---------|---------|
| `command_parser_matched_exactly` | 0x027B | 0xFF on a complete, valid match; stays set |
| `command_parser_matched` | 0x0278 | 1 when at least one word matched |
| `command_parser_word_count` | 0x0279 | word-table counter; its 0 → N edge marks each match |
| `where_to_print` | 0x02B7 | 255 while output echoes the command |
| `command_parser_position` | 0x0211 | the parse cursor; its snap back to 0x02F1 marks the command finishing |

The matched signal is `command_parser_word_count`: it resets to 0 between commands and runs 0 → N → 0 as the word table is checked, so the jump from 0 marks each match. `command_parser_matched_exactly` flips to 0xFF on a match but stays set; its clear and set happen inside one word decode, so the zero lasts less than a frame for words that match early in their table. `command_parser_matched` is 1 when at least one word matched, and `where_to_print` is 255 while output echoes the command, companions that cross-check the match. The executed signal is `command_parser_position`, the game's cursor into the command line, which snaps back to its resting 0x02F1 once a command has run. Paired with the `???` echo (`command_rejected`) it separates executed from rejected.

## Why

- **Matched is not executed.** The command-latency sandbox triangulates three moments of a command's life: matched, written, executed. The executed moment is the effect, read off the state change. A lone matched flag cannot be trusted until the whole fingerprint confirms it, because the sandbox's first check is "does a command that changes nothing still match?"
- **State fields, not an event channel.** The flags are parser facts, read every frame like the other scalars, so they file into `FIELDS`/`SCHEMA` under a new category. That filing is the environment's one extension point: both sides pick the new fields up automatically, and no other code changes.

## What Changed

- `daggorath_gym/state.py` — the `consumption` category added to `FIELDS` after `mode`, all true-state; the frame grows from 20 to 26 bytes, the fields from 16 to 21.
- `emulation/plugins/daggorath/state.lua` — the five fields added to `SCHEMA` after `mode`.

## Reference Documents

| Document | What it contains |
|---|---|
| `../findings/ram-signals.md` | The command-consumed fingerprint, the five addresses and their meanings |
| `../1_discussions/extensibility.md` | The open question this resolves, state fields versus an event record |
| `../1_discussions/events.md` | The deferred event channel this declines |
| `../../../agent/sandbox/command-latency/README.md` | The sandbox whose matched and executed moments these fields serve |
| `state.md` | The state schema this extends |
